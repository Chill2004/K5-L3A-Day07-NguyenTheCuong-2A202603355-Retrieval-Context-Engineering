"""Rerank hybrid candidates locally using a pinned cross-encoder."""

import json
import math
from pathlib import Path

from sentence_transformers import CrossEncoder

from src.hybrid_retriever import HybridRetriever


ROOT = Path(__file__).resolve().parents[1]


class RerankRetriever:
    def __init__(self, hybrid=None):
        path = ROOT / "artifacts/reranker_config.json"
        self.config = json.loads(path.read_text(encoding="utf-8"))

        self.hybrid = (
            hybrid if hybrid is not None else HybridRetriever()
        )
        self.candidate_k = self.config["candidate_k"]
        self.batch_size = self.config["batch_size"]
        self.max_length = self.config["max_length"]

        self.model = CrossEncoder(
            self.config["model"],
            revision=self.config["revision"],
            device=self.config["device"],
            max_length=self.max_length,
        )

    def search(self, query, *, filters=None, top_k=3):
        if not isinstance(query, str) or not query.strip():
            raise ValueError("Query must be a non-empty string.")

        if type(top_k) is not int or top_k < 1:
            raise ValueError("top_k must be a positive integer.")

        candidates = self.hybrid.search(
            query,
            filters=filters,
            top_k=max(self.candidate_k, top_k),
        )

        if not candidates:
            return []

        pairs = [
            (query.strip(), chunk["text"])
            for chunk in candidates
        ]

        for query_text, passage in pairs:
            tokens = self.model.tokenizer(
                query_text,
                passage,
                truncation=False,
            )["input_ids"]

            if len(tokens) > self.max_length:
                raise ValueError(
                    "Query-passage pair exceeds the reranker token limit."
                )

        scores = self.model.predict(
            pairs,
            batch_size=self.batch_size,
            show_progress_bar=False,
        )
        scores = [float(score) for score in scores]

        if len(scores) != len(candidates):
            raise ValueError("Reranker score count mismatch.")
        if not all(math.isfinite(score) for score in scores):
            raise ValueError("Non-finite reranker score.")

        results = [
            {
                **chunk,
                "retrieval_score": chunk["score"],
                "candidate_rank": rank,
                "score": score,
                "strategy": "hybrid_rerank",
            }
            for rank, (chunk, score) in enumerate(
                zip(candidates, scores),
                start=1,
            )
        ]

        return sorted(
            results,
            key=lambda chunk: (-chunk["score"], chunk["id"]),
        )[:top_k]