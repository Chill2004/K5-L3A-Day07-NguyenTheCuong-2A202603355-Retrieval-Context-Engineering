"""TF-IDF retrieval using the frozen Day06 chunks."""

import json
from pathlib import Path

from starter.baseline import TfidfIndex


ROOT = Path(__file__).resolve().parents[1]


class LexicalRetriever:
    def __init__(self):
        path = ROOT / "starter/data/day6/chunks.json"
        self.chunks = json.loads(
            path.read_text(encoding="utf-8-sig")
        )

        if not self.chunks:
            raise ValueError("Corpus must not be empty.")

        ids = [chunk["id"] for chunk in self.chunks]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate chunk IDs.")

        # Fit IDF once on the full corpus, independent of query filters.
        self.index = TfidfIndex(self.chunks)

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

        # Retrieve the full ranking before filtering, so excluded chunks
        # cannot consume the requested top_k positions.
        ranked = self.index.search(
            query.strip(),
            top_k=len(self.chunks),
        )

        eligible = [
            chunk
            for chunk in ranked
            if all(
                chunk["metadata"].get(key) == value
                for key, value in filters.items()
            )
        ]

        return eligible[:top_k]