"""Summarize original test runs without changing their outputs."""

import json
import statistics
from pathlib import Path

from src.evaluate_retrieval import evidence_in_context


ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "starter/results/day7"

FILES = {
    "baseline": (
        FOLDER / "agent_test/baseline"
        / "test_20261114T131936803449Z.json"
    ),
    "top5": (
        FOLDER / "agent_test/top5"
        / "test_20261114T132252908347Z.json"
    ),
}


def main():
    cases = json.loads(
        (ROOT / "starter/data/day6/test_questions.json").read_text(
            encoding="utf-8-sig"
        )
    )
    cases_by_id = {case["id"]: case for case in cases}
    summaries = {}

    for name, path in FILES.items():
        run = json.loads(path.read_text(encoding="utf-8-sig"))
        traces = run["traces"]

        assert run["status"] == "completed"
        assert len(traces) == 7
        assert len({t["query_id"] for t in traces}) == 7
        assert {t["query_id"] for t in traces} == set(cases_by_id)

        first_hit1 = 0
        first_hit3 = 0
        context_hits = 0
        answered = 0
        false_abstentions = 0
        missing_abstentions = 0
        explicit_missing_abstentions = 0
        search_counts = []
        request_count = 0
        token_totals = {
            "prompt_token_count": 0,
            "candidates_token_count": 0,
            "thoughts_token_count": 0,
            "total_token_count": 0,
        }

        for trace in traces:
            assert trace["status"] in ("answered", "abstain")
            case = cases_by_id[trace["query_id"]]
            result = trace["result"]
            searches = [
                event for event in result["events"]
                if event["event"] == "search"
            ]
            search_counts.append(len(searches))

            calls = trace.get("model_calls", [])
            request_count += len(calls)

            for call in calls:
                usage = call.get("usage") or {}
                for key in token_totals:
                    token_totals[key] += usage.get(key) or 0

            if case["answerable"]:
                answered += trace["status"] == "answered"
                false_abstentions += trace["status"] == "abstain"

                first_results = searches[0]["results"] if searches else []
                first_hit1 += evidence_in_context(
                    first_results[:1], case["gold"]
                )
                first_hit3 += evidence_in_context(
                    first_results[:3], case["gold"]
                )

                if searches:
                    final_ids = set(searches[-1]["context_ids"])
                    retrieved = {
                        chunk["id"]: chunk
                        for search in searches
                        for chunk in search["results"]
                    }
                    included = [
                        retrieved[chunk_id] for chunk_id in final_ids
                    ]
                    context_hits += evidence_in_context(
                        included, case["gold"]
                    )
            else:
                missing_abstentions += trace["status"] == "abstain"
                explicit_missing_abstentions += any(
                    event["event"] == "model_abstain"
                    for event in result["events"]
                )

        summaries[name] = {
            "source_run": str(path.relative_to(ROOT)),
            "split": "test",
            "question_count": 7,
            "answerable_count": 5,
            "unanswerable_count": 2,
            "answered_on_answerable": answered,
            "false_abstentions": false_abstentions,
            "final_abstentions_on_unanswerable": missing_abstentions,
            "explicit_abstentions_on_unanswerable": (
                explicit_missing_abstentions
            ),
            "first_tool_evidence_hit_at_1_count": first_hit1,
            "first_tool_evidence_hit_at_3_count": first_hit3,
            "final_context_evidence_complete_count": context_hits,
            "retrieval_metric_scope": (
                "First model-generated search query; cutoff 1 and 3 "
                "for both configurations. Not the original-query benchmark."
            ),
            "model_request_attempts": request_count,
            "search_calls_total": sum(search_counts),
            "median_question_seconds_including_pacing": statistics.median(
                trace["elapsed_seconds"] for trace in traces
            ),
            "reported_token_usage": token_totals,
            "grading_note": (
                "Answer correctness and semantic citation support "
                "require separate reviewed labels."
            ),
        }

        print(name)
        print(json.dumps(summaries[name], indent=2))

    output = FOLDER / "test_automatic_summary.json"
    output.write_text(
        json.dumps(summaries, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print("Saved:", output)


if __name__ == "__main__":
    main()