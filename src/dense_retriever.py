"""Read-only dense retrieval over the Day06 pgvector index."""

import math
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from sentence_transformers import SentenceTransformer


ROOT = Path(__file__).resolve().parents[1]
MODEL_NAME = "intfloat/multilingual-e5-small"
MODEL_REVISION = "614241f622f53c4eeff9890bdc4f31cfecc418b3"


class DenseRetriever:
    def __init__(self):
        load_dotenv(ROOT / ".env")
        self.database_url = os.environ["DATABASE_URL"]
        self.strategy = os.getenv("DAY6_STRATEGY", "A")

        if self.strategy != "A":
            raise ValueError("Day07 benchmark requires Day06 strategy A.")

        self.model = SentenceTransformer(
            MODEL_NAME,
            revision=MODEL_REVISION,
            device="cpu",
        )

        dimensions = self.model.get_embedding_dimension()
        if dimensions != 384:
            raise ValueError(f"Expected 384 dimensions, got {dimensions}.")

    def search(self, query, *, filters=None, top_k=3):
        if not isinstance(query, str) or not query.strip():
            raise ValueError("Query must be a non-empty string.")

        if type(top_k) is not int or top_k < 1:
            raise ValueError("top_k must be a positive integer.")

        if filters is None:
            filters = {}

        if not isinstance(filters, dict):
            raise ValueError("filters must be a dictionary.")

        if set(filters) - {"section"}:
            raise ValueError("Only the section metadata filter is supported.")

        if filters and (
            not isinstance(filters["section"], str)
            or not filters["section"].strip()
        ):
            raise ValueError("section must be a non-empty string.")

        text = "query: " + query.strip()
        token_ids = self.model.tokenizer(
            text,
            truncation=False,
            add_special_tokens=True,
        )["input_ids"]

        if len(token_ids) > self.model.max_seq_length:
            raise ValueError("Query exceeds the embedding token limit.")

        vector = self.model.encode(
            text,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        ).tolist()

        if len(vector) != 384 or not all(map(math.isfinite, vector)):
            raise ValueError("Invalid query embedding.")

        # pgvector accepts a textual vector cast through a SQL parameter.
        vector_text = "[" + ",".join(str(value) for value in vector) + "]"

        with psycopg.connect(
            self.database_url,
            connect_timeout=10,
            options="-c default_transaction_read_only=on",
            row_factory=dict_row,
        ) as connection:
            rows = connection.execute(
                """
                SELECT
                    chunk_id AS id,
                    document_id AS source_id,
                    source,
                    page,
                    text,
                    metadata,
                    1 - (embedding <=> %(vector)s::vector) AS score
                FROM ingestion_chunks
                WHERE strategy = %(strategy)s
                  AND metadata @> %(filters)s
                ORDER BY
                    embedding <=> %(vector)s::vector,
                    chunk_id
                LIMIT %(top_k)s
                """,
                {
                    "vector": vector_text,
                    "strategy": self.strategy,
                    "filters": Jsonb(filters),
                    "top_k": top_k,
                },
            ).fetchall()

        return [
            {**row, "strategy": "dense"}
            for row in rows
        ]