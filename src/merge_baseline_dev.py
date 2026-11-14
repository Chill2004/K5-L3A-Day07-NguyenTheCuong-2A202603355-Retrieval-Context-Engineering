"""Merge baseline dev runs while retaining failed attempts."""

import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "starter/results/day7/agent_dev/baseline"

FILES = [
    "dev_20261114T102351627014Z.json",
    "dev_20261114T105743862256Z.json",
    "dev_20261114T110009099441Z.json",
]


def main():
    questions = json.loads(
        (ROOT / "starter/data/day6/dev_questions.json").read_text(
            encoding="utf-8-sig"
        )
    )
    expected_ids = {q["id"] for q in questions}

    successful = {}
    errors = []
    requests = 0
    reference = None

    for filename in FILES:
        run = json.loads(
            (FOLDER / filename).read_text(encoding="utf-8-sig")
        )

        settings = {
            key: run[key]
            for key in (
                "config_name", "config", "retriever",
                "candidate_k", "rrf_k", "model", "split",
            )
        }
        if reference is None:
            reference = settings
        elif settings != reference:
            raise ValueError("Run configuration mismatch.")

        for trace in run["traces"]:
            requests += len(trace.get("model_calls", []))
            item = {**trace, "source_run": filename}
            query_id = trace["query_id"]

            if query_id not in expected_ids:
                raise ValueError(f"Unexpected question: {query_id}")

            if trace["status"] == "error":
                errors.append(item)
                continue

            if trace["status"] not in ("answered", "abstain"):
                raise ValueError(f"Unexpected status: {trace['status']}")

            if query_id in successful:
                raise ValueError(f"Duplicate completed question: {query_id}")

            successful[query_id] = item

    if set(successful) != expected_ids:
        raise ValueError(
            f"Missing questions: {sorted(expected_ids - set(successful))}"
        )

    traces = [successful[q["id"]] for q in questions]
    merged = {
        **reference,
        "source_runs": FILES,
        "question_count": len(traces),
        "model_request_attempts": requests,
        "failed_question_attempts": errors,
        "status": "completed",
        "traces": traces,
        "timing_note": (
            "Runs span a rate-limit pacing change. "
            "End-to-end latency is not directly comparable across runs."
        ),
    }

    output = FOLDER / "dev_merged.json"
    output.write_text(
        json.dumps(merged, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    reading = []
    for trace in traces:
        result = trace["result"]
        events = result["events"]
        searches = [e for e in events if e["event"] == "search"]

        reading.extend([
            f"========== {trace['query_id']} ==========",
            f"ANSWERABLE: {trace['answerable']}",
            f"QUESTION: {trace['question']}",
            f"STATUS: {trace['status']}",
            f"ANSWER: {result['answer']}",
            f"CITATIONS: {result['citations']}",
            f"EVENTS: {[e['event'] for e in events]}",
            "FINAL CONTEXT:",
            searches[-1]["context"] if searches else "(no retrieval)",
            "",
        ])

    reading_path = FOLDER / "dev_audit_reading.txt"
    reading_path.write_text("\n".join(reading), encoding="utf-8")

    print("Completed questions:", len(traces))
    print("Statuses:", dict(Counter(t["status"] for t in traces)))
    print("Failed question attempts:", len(errors))
    print("Model request attempts:", requests)
    print("Saved:", output)
    print("Saved:", reading_path)
    print("Baseline merge: OK")


if __name__ == "__main__":
    main()