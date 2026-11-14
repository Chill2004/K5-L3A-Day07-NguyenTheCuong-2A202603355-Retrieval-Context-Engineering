"""Run one agent configuration over a selected number of dev questions."""

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from starter.agentic import run_agent
from src.gemini_controller import GeminiController
from src.hybrid_retriever import HybridRetriever


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "starter" / "data" / "day6" / "dev_questions.json"
OUTPUT_ROOT = ROOT / "starter" / "results" / "day7" / "agent_dev"

CONFIGS = {
    "baseline": {
        "max_searches": 2,
        "top_k": 3,
        "budget": 2500,
    },
    "top5": {
        "max_searches": 2,
        "top_k": 5,
        "budget": 2500,
    },
    "single_search": {
        "max_searches": 1,
        "top_k": 3,
        "budget": 2500,
    },
}

CANDIDATE_K = 20
RRF_K = 60


def save(path, output):
    path.write_text(
        json.dumps(output, ensure_ascii=False, indent=2, allow_nan=False)
        + "\n",
        encoding="utf-8",
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, choices=CONFIGS)
    parser.add_argument(
        "--max-questions",
        required=True,
        type=int,
        help="Number of dev questions; use 17 for the full dev set.",
    )
    parser.add_argument(
        "--allow-api",
        action="store_true",
        help="Authorize sending selected dev questions/context to Gemini.",
    )
    parser.add_argument(
        "--skip-ids",
        nargs="*",
        default=[],
        help="Skip dev question IDs already evaluated.",
    )

    args = parser.parse_args()

    questions = json.loads(DATA_PATH.read_text(encoding="utf-8-sig"))

    if len(questions) != 17 or any(
        q.get("split") != "dev" for q in questions
    ):
        raise ValueError("Expected exactly 17 dev questions.")

    if not 1 <= args.max_questions <= len(questions):
        parser.error("--max-questions must be between 1 and 17.")

    known_ids = {q["id"] for q in questions}
    skipped = set(args.skip_ids)

    if skipped - known_ids:
        parser.error(f"Unknown question IDs: {sorted(skipped - known_ids)}")

    selected = [
        q for q in questions[:args.max_questions]
        if q["id"] not in skipped
    ]

    if not selected:
        parser.error("No questions remain after skipping.")

    config = CONFIGS[args.config]
    max_calls = len(selected) * (config["max_searches"] + 1)

    print("Config:", args.config, config)
    print("Selected questions:", [q["id"] for q in selected])
    print("Maximum model requests:", max_calls)

    if not args.allow_api:
        print("No API request sent. Review the plan before using --allow-api.")
        return

    retriever = HybridRetriever(
        candidate_k=CANDIDATE_K,
        rrf_k=RRF_K,
    )
    
    import os
    import psycopg
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")

    with psycopg.connect(
        os.environ["DATABASE_URL"],
        connect_timeout=5,
        options="-c default_transaction_read_only=on",
    ) as connection:
        count = connection.execute(
            """
            SELECT COUNT(*)
            FROM ingestion_chunks
            WHERE strategy = %s
            """,
            ("A",),
        ).fetchone()[0]

    if count != 192:
        raise ValueError(f"Expected 192 strategy A chunks, got {count}.")

    print("Database preflight: OK")
    controller = GeminiController()

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    folder = OUTPUT_ROOT / args.config
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"dev_{stamp}.json"

    output = {
        "config_name": args.config,
        "config": config,
        "retriever": "hybrid_rrf",
        "candidate_k": CANDIDATE_K,
        "rrf_k": RRF_K,
        "model": controller.model,
        "split": "dev",
        "question_count": len(selected),
        "status": "running",
        "traces": [],
        "selected_question_ids": [q["id"] for q in selected],
        "skipped_question_ids": sorted(skipped),
    }

    try:
        for question in selected:
            calls_start = len(controller.calls)
            started = time.perf_counter()

            try:
                result = run_agent(
                    question["question"],
                    controller,
                    retriever,
                    filters=question.get("filter"),
                    max_searches=config["max_searches"],
                    top_k=config["top_k"],
                    budget=config["budget"],
                )
            except Exception as error:
                output["traces"].append({
                    "query_id": question["id"],
                    "answerable": question["answerable"],
                    "question": question["question"],
                    "filter": question.get("filter"),
                    "status": "error",
                    "error_type": type(error).__name__,
                    "elapsed_seconds": time.perf_counter() - started,
                    "model_calls": controller.calls[calls_start:],
                })
                output["status"] = "error"
                save(path, output)
                raise

            output["traces"].append({
                "query_id": question["id"],
                "answerable": question["answerable"],
                "question": question["question"],
                "filter": question.get("filter"),
                "status": result["status"],
                "result": result,
                "elapsed_seconds": time.perf_counter() - started,
                "model_calls": controller.calls[calls_start:],
            })
            save(path, output)
            print(
                question["id"],
                result["status"],
                "requests:",
                len(controller.calls) - calls_start,
            )

        output["status"] = "completed"

    except Exception:
        output["status"] = "error"
        raise

    finally:
        try:
            controller.close()
        finally:
            save(path, output)
            print("Model requests attempted:", len(controller.calls))
            print("Saved:", path)


if __name__ == "__main__":
    main()