"""Run the frozen Advanced test once."""

import argparse
import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "starter/data/advanced"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allow-api", action="store_true")
    args = parser.parse_args()

    selection_path = ROOT / "artifacts/advanced/selection_dev.json"
    selection = json.loads(
        selection_path.read_text(encoding="utf-8")
    )
    freeze_path = BASE / "benchmark/benchmark_freeze.json"

    if sha256(freeze_path) != selection["benchmark_freeze_sha256"]:
        raise ValueError("Benchmark freeze changed.")

    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))

    checks = {
        **freeze["sha256"],
        **selection["pipeline_sha256"],
        selection["source_run"]: selection["source_run_sha256"],
    }
    for relative, expected in checks.items():
        if sha256(ROOT / relative) != expected:
            raise ValueError(f"Frozen file changed: {relative}")

    questions = json.loads(
        (BASE / "benchmark/test_questions.json").read_text(
            encoding="utf-8-sig"
        )
    )
    if len(questions) != 30:
        raise ValueError("Expected 30 test questions.")
    if len({q["id"] for q in questions}) != 30:
        raise ValueError("Duplicate question IDs.")
    if any(q["split"] != "test" for q in questions):
        raise ValueError("Unexpected question split.")

    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
    if os.environ.get("GEMINI_MODEL") != selection["model"]:
        raise ValueError("Model differs from selected dev configuration.")

    config = selection["config"]
    print("Split: test")
    print("Model:", selection["model"])
    print("Config:", config)
    print("Questions:", len(questions))
    print(
        "Maximum Gemini requests:",
        len(questions) * (config["max_searches"] + 1),
    )
    print("Required result: at least 27/30")
    print("Frozen files: OK")

    if not args.allow_api:
        print("Gemini requests: 0")
        return

    output = ROOT / (
        "starter/results/day7/advanced/test/test_run.json"
    )
    output.parent.mkdir(parents=True, exist_ok=True)

    # Exclusive creation protects the original test run.
    record = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "split": "test",
        "model": selection["model"],
        "config": config,
        "selection_sha256": sha256(selection_path),
        "runner_sha256": sha256(Path(__file__)),
        "question_ids": [q["id"] for q in questions],
        "denominator": 30,
        "results": [],
        "status": "running",
    }
    with output.open("x", encoding="utf-8") as handle:
        json.dump(record, handle, ensure_ascii=False, indent=2)

    def save():
        output.write_text(
            json.dumps(record, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    retriever = None
    try:
        from src.advanced.agent import run_question
        from src.advanced.retrieval import AdvancedRetriever

        retriever = AdvancedRetriever()

        for index, question in enumerate(questions):
            if index:
                time.sleep(6)

            started = time.perf_counter()

            # Gold, expected answers and evidence crops are not sent.
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
            if result["status"] == "error":
                record["status"] = "stopped_on_error"
                break
        else:
            record["status"] = "completed"

    except BaseException as error:
        record["status"] = "interrupted_or_error"
        record["error_type"] = type(error).__name__
        raise
    finally:
        save()
        if retriever is not None:
            retriever.close()
        print("Saved:", output)


if __name__ == "__main__":
    main()