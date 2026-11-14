"""Evaluate dense, lexical, and hybrid retrieval on the dev split."""

import json
import statistics
import time
from pathlib import Path
import unicodedata

from src.dense_retriever import DenseRetriever
from src.hybrid_retriever import HybridRetriever
from src.lexical_retriever import LexicalRetriever
from src.rerank_retriever import RerankRetriever

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "starter" / "data" / "day6"
OUTPUT_DIR = ROOT / "starter" / "results" / "day7"
TOP_K = 3


def normalize_evidence(text):
    text = unicodedata.normalize("NFC", text).casefold()
    return " ".join(text.split())


def is_hit(chunk, gold):
    chunk_text = normalize_evidence(chunk["text"])
    return any(
        chunk["source_id"] == item["source_id"]
        and chunk["page"] == item["page"]
        and normalize_evidence(item["evidence"]) in chunk_text
        for item in gold
    )
def evidence_in_context(results, gold):
    groups = {}

    for chunk in results:
        metadata = chunk["metadata"]
        start = metadata["start_char"]
        end = metadata["end_char"]

        if not (
            type(start) is int
            and type(end) is int
            and 0 <= start < end
            and end - start == len(chunk["text"])
        ):
            raise ValueError(f"Invalid chunk offsets: {chunk['id']}")

        key = (
            chunk["source_id"],
            chunk["page"],
            metadata["unit_id"],
        )
        groups.setdefault(key, []).append(
            (start, end, chunk["text"])
        )

    for (source_id, page, unit_id), spans in groups.items():
        spans.sort(key=lambda span: (span[0], span[1]))
        merged = []

        for start, end, text in spans:
            if not merged or start > merged[-1][1]:
                merged.append([start, end, text])
                continue

            previous = merged[-1]
            overlap_end = min(previous[1], end)
            overlap_length = overlap_end - start
            previous_offset = start - previous[0]

            if (
                previous[2][
                    previous_offset:previous_offset + overlap_length
                ]
                != text[:overlap_length]
            ):
                raise ValueError(
                    f"Conflicting overlap: {source_id}, {page}, {unit_id}"
                )

            if end > previous[1]:
                previous[2] += text[previous[1] - start:]
                previous[1] = end

        for item in gold:
            if (
                item["source_id"] != source_id
                or item["page"] != page
            ):
                continue

            evidence = normalize_evidence(item["evidence"])
            if evidence and any(
                evidence in normalize_evidence(text)
                for _, _, text in merged
            ):
                return True

    return False


def main():
    questions = json.loads(
        (DATA_DIR / "dev_questions.json").read_text(encoding="utf-8-sig")
    )

    if len(questions) != 17:
        raise ValueError(f"Expected 17 dev questions, got {len(questions)}.")
    if any(question.get("split") != "dev" for question in questions):
        raise ValueError("The dev file contains a non-dev question.")
    if len({question["id"] for question in questions}) != len(questions):
        raise ValueError("Duplicate question IDs in dev set.")
    if sum(question.get("answerable") is True for question in questions) != 15:
        raise ValueError("Expected 15 answerable dev questions.")
    if sum(question.get("answerable") is False for question in questions) != 2:
        raise ValueError("Expected 2 unanswerable dev questions.")

    setup_seconds = {}

    started = time.perf_counter()
    dense = DenseRetriever()
    setup_seconds["dense"] = time.perf_counter() - started

    started = time.perf_counter()
    lexical = LexicalRetriever()
    setup_seconds["lexical"] = time.perf_counter() - started

    started = time.perf_counter()
    hybrid = HybridRetriever(dense=dense, lexical=lexical)
    setup_seconds["hybrid"] = time.perf_counter() - started

    started = time.perf_counter()
    reranked = RerankRetriever(hybrid=hybrid)
    setup_seconds["hybrid_rerank"] = time.perf_counter() - started

    retrievers = {
        "dense": dense,
        "lexical": lexical,
        "hybrid": hybrid,
        "hybrid_rerank": reranked,
    }

    warmup_question = next(
        question for question in questions if question["id"] == "q01"
    )
    for retriever in retrievers.values():
        retriever.search(
            warmup_question["question"],
            filters=warmup_question.get("filter"),
            top_k=TOP_K,
        )

    traces = {name: [] for name in retrievers}

    for question in questions:
        answerable = question["answerable"]
        gold = question.get("gold", []) if answerable else []

        for name, retriever in retrievers.items():
            started = time.perf_counter()
            results = retriever.search(
                question["question"],
                filters=question.get("filter"),
                top_k=TOP_K,
            )
            elapsed_ms = (time.perf_counter() - started) * 1000

            result_ids = [result["id"] for result in results]
            if len(result_ids) != len(set(result_ids)):
                raise ValueError(
                    f"{name} returned duplicate IDs for {question['id']}."
                )

            result_hits = [
                is_hit(result, gold) for result in results
            ] if answerable else []

            prefix_hits = [
                evidence_in_context(results[:k], gold)
                for k in range(1, TOP_K + 1)
            ] if answerable else []

            first_hit_rank = next(
                (
                    rank
                    for rank, matched in enumerate(prefix_hits, start=1)
                    if matched
                ),
                None,
            )

            traced_results = []
            for rank, result in enumerate(results, start=1):
                traced = {
                    "rank": rank,
                    "id": result["id"],
                    "source_id": result["source_id"],
                    "source": result["source"],
                    "page": result["page"],
                    "text": result["text"],
                    "metadata": result["metadata"],
                    "score": float(result["score"]),
                    "strategy": result.get("strategy", name),
                    "gold_hit": (
                        result_hits[rank - 1] if answerable else None
                    ),
                }
                for key in (
                    "component_ranks",
                    "component_scores",
                    "candidate_rank",
                    "retrieval_score",
                ):
                    if key in result:
                        traced[key] = result[key]
                traced_results.append(traced)

            traces[name].append({
                "query_id": question["id"],
                "split": "dev",
                "question": question["question"],
                "answerable": answerable,
                "filter": question.get("filter"),
                "gold": gold,
                "elapsed_ms": elapsed_ms,
                "hit_at_1": (
                    prefix_hits[0] if answerable else None
                ),
                "hit_at_3": (
                    prefix_hits[TOP_K - 1] if answerable else None
                ),
                "reciprocal_rank_at_3": (
                    1.0 / first_hit_rank if first_hit_rank else 0.0
                ) if answerable else None,
                "results": traced_results,
            })

    answerable_count = sum(
        question["answerable"] is True for question in questions
    )
    summaries = {}

    for name, method_traces in traces.items():
        scored = [
            trace for trace in method_traces
            if trace["answerable"]
        ]
        all_latencies = [
            trace["elapsed_ms"] for trace in method_traces
        ]

        summaries[name] = {
            "strategy": name,
            "evaluation_definition": "evidence_complete_contiguous_spans_v1",
            "reciprocal_rank_definition": "first_evidence_complete_prefix",
            "split": "dev",
            "query_count": len(method_traces),
            "answerable_count": answerable_count,
            "unanswerable_count": len(method_traces) - answerable_count,
            "top_k": TOP_K,
            "hit_at_1_count": sum(
                trace["hit_at_1"] for trace in scored
            ),
            "hit_at_1_rate": sum(
                trace["hit_at_1"] for trace in scored
            ) / answerable_count,
            "hit_at_3_count": sum(
                trace["hit_at_3"] for trace in scored
            ),
            "hit_at_3_rate": sum(
                trace["hit_at_3"] for trace in scored
            ) / answerable_count,
            "mrr_at_3": statistics.mean(
                trace["reciprocal_rank_at_3"] for trace in scored
            ),
            "median_search_ms_all_queries": statistics.median(
                all_latencies
            ),
            "index_setup_seconds": setup_seconds[name],
        }

    if hasattr(hybrid, "candidate_k"):
        summaries["hybrid"]["candidate_k"] = hybrid.candidate_k
        summaries["hybrid"]["rrf_k"] = hybrid.rrf_k
        summaries["hybrid_rerank"]["reranker_config"] = reranked.config
        summaries["hybrid_rerank"]["base_retriever"] = "hybrid"
        summaries["hybrid_rerank"]["setup_timing_scope"] = (
        "reranker initialization only; reuses hybrid dependencies"
        )
        summaries["hybrid"]["setup_timing_scope"] = (
        "wrapper initialization only; reuses dense and lexical"
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "dev_retrieval_traces.json").write_text(
        json.dumps(traces, ensure_ascii=False, indent=2, allow_nan=False)
        + "\n",
        encoding="utf-8",
    )
    (OUTPUT_DIR / "dev_retrieval_summary.json").write_text(
        json.dumps(summaries, ensure_ascii=False, indent=2, allow_nan=False)
        + "\n",
        encoding="utf-8",
    )

    print(json.dumps(summaries, ensure_ascii=False, indent=2))
    print("Saved:", OUTPUT_DIR / "dev_retrieval_traces.json")
    print("Saved:", OUTPUT_DIR / "dev_retrieval_summary.json")


if __name__ == "__main__":
    main()