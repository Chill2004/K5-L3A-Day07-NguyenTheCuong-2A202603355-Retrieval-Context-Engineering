"""Hybrid retrieval using Reciprocal Rank Fusion."""

from src.dense_retriever import DenseRetriever
from src.lexical_retriever import LexicalRetriever


class HybridRetriever:
    def __init__(
        self,
        dense=None,
        lexical=None,
        candidate_k=20,
        rrf_k=60,
    ):
        if type(candidate_k) is not int or candidate_k < 1:
            raise ValueError("candidate_k must be a positive integer.")

        if type(rrf_k) is not int or rrf_k < 1:
            raise ValueError("rrf_k must be a positive integer.")

        self.dense = dense if dense is not None else DenseRetriever()
        self.lexical = (
            lexical if lexical is not None else LexicalRetriever()
        )
        self.candidate_k = candidate_k
        self.rrf_k = rrf_k

    def search(self, query, *, filters=None, top_k=3):
        if not isinstance(query, str) or not query.strip():
            raise ValueError("Query must be a non-empty string.")

        if type(top_k) is not int or top_k < 1:
            raise ValueError("top_k must be a positive integer.")

        depth = max(self.candidate_k, top_k)

        dense_results = self.dense.search(
            query,
            filters=filters,
            top_k=depth,
        )
        lexical_results = self.lexical.search(
            query,
            filters=filters,
            top_k=depth,
        )

        fused = {}

        for method, results in [
            ("dense", dense_results),
            ("lexical", lexical_results),
        ]:
            seen = set()

            for rank, chunk in enumerate(results, start=1):
                chunk_id = chunk["id"]
                if chunk_id in seen:
                    raise ValueError("Duplicate IDs in component ranking.")
                seen.add(chunk_id)

                if chunk_id not in fused:
                    fused[chunk_id] = {
                        **chunk,
                        "score": 0.0,
                        "strategy": "hybrid_rrf",
                        "component_ranks": {},
                        "component_scores": {},
                    }
                else:
                    for key in (
                        "source_id", "source", "page", "text", "metadata"
                    ):
                        if fused[chunk_id][key] != chunk[key]:
                            raise ValueError(
                                f"Component corpus mismatch: {chunk_id}"
                            )

                item = fused[chunk_id]
                item["score"] += 1.0 / (self.rrf_k + rank)
                item["component_ranks"][method] = rank
                item["component_scores"][method] = chunk["score"]

        return sorted(
            fused.values(),
            key=lambda item: (-item["score"], item["id"]),
        )[:top_k]