"""Continue only unattempted questions from the original test."""

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from src.run_advanced_test import ROOT, BASE, sha256


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allow-api", action="store_true")
    args = parser.parse_args()

    # Reuse the original runner's frozen-file and model checks.
    subprocess.run(
        [sys.executable, "-m", "src.run_advanced_test"],
        cwd=ROOT,
        check=True,
    )

    folder = ROOT / "starter/results/day7/advanced/test"
    original_path = folder / "test_run.json"
    original = json.loads(
        original_path.read_text(encoding="utf-8")
    )
    selection_path = ROOT / "artifacts/advanced/selection_dev.json"

    if original["selection_sha256"] != sha256(selection_path):
        raise ValueError("Selection differs from the original test.")

    questions = json.loads(
        (BASE / "benchmark/test_questions.json").read_text(
            encoding="utf-8-sig"
        )
    )

    # Include previous continuation files when finding attempted IDs.
    attempted = set()
    parents = {}
    for path in [original_path, *sorted(folder.glob("continuation_*.json"))]:
        run = json.loads(path.read_text(encoding="utf-8"))
        if run["selection_sha256"] != original["selection_sha256"]:
            raise ValueError(f"Selection mismatch: {path}")
        parents[path.relative_to(ROOT).as_posix()] = sha256(path)
        for result in run["results"]:
            question_id = result["question_id"]
            if question_id in attempted:
                raise ValueError(f"Duplicate attempt: {question_id}")
            attempted.add(question_id)

    remaining = [q for q in questions if q["id"] not in attempted]
    print("Remaining IDs:", [q["id"] for q in remaining])
    print("Maximum additional requests:", len(remaining) * 3)

    if not args.allow_api or not remaining:
        print("Additional Gemini requests: 0")
        return

    from src.advanced.agent import run_question
    from src.advanced.retrieval import AdvancedRetriever

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    output = folder / f"continuation_{stamp}.json"
    record = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "split": "test",
        "config": original["config"],
        "model": original["model"],
        "selection_sha256": original["selection_sha256"],
        "runner_sha256": sha256(Path(__file__)),
        "parent_run_sha256": parents,
        "question_ids": [q["id"] for q in remaining],
        "denominator": 30,
        "results": [],
        "status": "running",
    }

    def save():
        output.write_text(
            json.dumps(record, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    with output.open("x", encoding="utf-8") as handle:
        json.dump(record, handle, ensure_ascii=False, indent=2)

    retriever = None
    try:
        retriever = AdvancedRetriever()
        for index, question in enumerate(remaining):
            if index:
                time.sleep(6)

            started = time.perf_counter()
            result = run_question(
                question["question"],
                retriever,
                **original["config"],
            )
            result["question_id"] = question["id"]
            result["elapsed_seconds"] = time.perf_counter() - started
            record["results"].append(result)
            save()

            print(
                question["id"],
                result["status"],
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