"""Compare context packing on saved dev retrieval results."""

import json
from pathlib import Path

from starter.baseline import pack_context
from src.evaluate_retrieval import evidence_in_context
from src.neighbor_context import pack_neighbor_context


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "starter/data/day6"
OUTPUT = ROOT / "starter/results/day7"
BUDGET = 2500


def main():
    corpus = json.loads(
        (DATA / "chunks.json").read_text(encoding="utf-8-sig")
    )
    retrieval = json.loads(
        (OUTPUT / "dev_retrieval_traces.json").read_text(
            encoding="utf-8-sig"
        )
    )

    traces = []
    summaries = []

    for method in ("hybrid", "hybrid_rerank"):
        for packing in ("ranked", "neighbors"):
            rows = []

            for trace in retrieval[method]:
                assert trace["split"] == "dev"
                results = trace["results"]

                if packing == "ranked":
                    context, ids = pack_context(results, budget=BUDGET)
                    included = [
                        chunk for chunk in results if chunk["id"] in ids
                    ]
                else:
                    context, ids, included = pack_neighbor_context(
                        results, corpus, budget=BUDGET
                    )

                assert len(context) <= BUDGET

                row = {
                    "query_id": trace["query_id"],
                    "method": method,
                    "packing": packing,
                    "answerable": trace["answerable"],
                    "budget_chars": BUDGET,
                    "context_chars": len(context),
                    "context": context,
                    "context_ids": ids,
                    "included_chunks": included,
                    "context_evidence_complete": (
                        evidence_in_context(included, trace["gold"])
                        if trace["answerable"] else None
                    ),
                }
                rows.append(row)

            scored = [row for row in rows if row["answerable"]]
            hits = sum(
                row["context_evidence_complete"] for row in scored
            )
            misses = [
                row["query_id"] for row in scored
                if not row["context_evidence_complete"]
            ]

            summary = {
                "method": method,
                "packing": packing,
                "budget_chars": BUDGET,
                "answerable_count": len(scored),
                "context_evidence_complete_count": hits,
                "context_evidence_complete_rate": hits / len(scored),
                "misses": misses,
            }
            summaries.append(summary)
            traces.extend(rows)

            print(
                f"{method} | {packing} | "
                f"context evidence: {hits}/{len(scored)} | "
                f"misses: {misses}"
            )

    for filename, value in [
        ("dev_context_traces.json", traces),
        ("dev_context_summary.json", summaries),
    ]:
        (OUTPUT / filename).write_text(
            json.dumps(value, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    print("Dev context evaluation: OK")


if __name__ == "__main__":
    main()