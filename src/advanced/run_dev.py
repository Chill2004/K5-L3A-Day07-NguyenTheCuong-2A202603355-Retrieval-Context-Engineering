"""Run Advanced dev questions; API calls require --allow-api."""

import argparse
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "starter/data/advanced"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allow-api", action="store_true")
    parser.add_argument("--skip-ids", nargs="*", default=[])
    args = parser.parse_args()

    freeze_path = BASE / "benchmark/benchmark_freeze.json"
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))

    # Verify that frozen source, questions and evidence remain unchanged.
    for relative_path, expected in freeze["sha256"].items():
        path = ROOT / relative_path
        if sha256(path) != expected:
            raise ValueError(f"Frozen file changed: {relative_path}")

    questions = json.loads(
        (BASE / "benchmark/dev_questions.json").read_text(
            encoding="utf-8-sig"
        )
    )
    known_ids = {q["id"] for q in questions}
    unknown = set(args.skip_ids) - known_ids
    if unknown:
        raise ValueError(f"Unknown skipped IDs: {sorted(unknown)}")

    selected = [
        q for q in questions if q["id"] not in args.skip_ids
    ]
    if not selected:
        raise ValueError("No questions selected.")

    config = {"max_searches": 2, "top_k": 3}
    print("Split: dev")
    print("Config:", config)
    print("Selected questions:", [q["id"] for q in selected])
    print("Maximum Gemini requests:", len(selected) * 3)
    print("Maximum original page images per request: 6")

    if not args.allow_api:
        print("Gemini requests: 0")
        print("Review this plan before adding --allow-api.")
        return

    from src.advanced.agent import run_question
    from src.advanced.retrieval import AdvancedRetriever

    folder = ROOT / "starter/results/day7/advanced/dev"
    folder.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    output = folder / f"dev_{stamp}.json"

    record = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "split": "dev",
        "config": config,
        "benchmark_freeze_sha256": sha256(freeze_path),
        "selected_ids": [q["id"] for q in selected],
        "skipped_ids": args.skip_ids,
        "code_sha256": {
            path.relative_to(ROOT).as_posix(): sha256(path)
            for path in sorted(
                (ROOT / "src/advanced").glob("*.py")
            )
        },
        "results": [],
        "status": "running",
    }

    def save():
        output.write_text(
            json.dumps(record, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    save()
    retriever = None

    try:
        retriever = AdvancedRetriever()

        for index, question in enumerate(selected):
            if index:
                time.sleep(6)

            started = time.perf_counter()

            # Only the question text reaches the agent.
            # Gold, expected answers and evidence crops are excluded.
            result = run_question(
                question["question"], retriever, **config
            )
            result["question_id"] = question["id"]
            result["elapsed_seconds"] = (
                time.perf_counter() - started
            )

            record["results"].append(result)
            save()

            print(
                question["id"],
                "| status:", result["status"],
                "| requests:", len(result["model_calls"]),
            )

            # Preserve the failure and stop to avoid repeated API errors.
            if result["status"] == "error":
                record["status"] = "stopped_on_error"
                break
        else:
            record["status"] = "completed"

    except Exception as error:
        record["status"] = "error"
        record["error_type"] = type(error).__name__
        raise
    finally:
        if retriever is not None:
            retriever.close()
        save()
        print("Saved:", output)

    print(
        "Model requests attempted:",
        sum(len(r["model_calls"]) for r in record["results"]),
    )


if __name__ == "__main__":
    main()