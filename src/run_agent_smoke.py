"""Run one dev question through the real Gemini agent."""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from starter.agentic import run_agent
from src.gemini_controller import GeminiController
from src.hybrid_retriever import HybridRetriever


ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--allow-api",
        action="store_true",
        help="Authorize sending this dev question and context to Gemini.",
    )
    parser.add_argument(
        "--query-id",
        default="q01",
        help="Dev question ID to run.",
    )
    args = parser.parse_args()

    if not args.allow_api:
        parser.exit(
            message="No API request sent. Review the plan before using --allow-api.\n"
        )

    questions = json.loads(
        (ROOT / "starter/data/day6/dev_questions.json").read_text(
            encoding="utf-8-sig"
        )
    )
    question = next(
        (
            q for q in questions
            if q["id"] == args.query_id and q.get("split") == "dev"
        ),
        None,
    )
    if question is None:
        parser.error(f"{args.query_id!r} is not a dev question")

    # Initialize local retrieval before opening the Gemini client.
    retriever = HybridRetriever(candidate_k=20, rrf_k=60)
    controller = GeminiController()

    output = {
        "query_id": question["id"],
        "split": "dev",
        "model": controller.model,
        "retriever": "hybrid_rrf",
        "max_searches": 2,
        "top_k": 3,
        "budget_chars": 2500,
        "status": "started",
    }

    try:
        result = run_agent(
            question["question"],
            controller,
            retriever,
            filters=question.get("filter"),
            max_searches=2,
            top_k=3,
            budget=2500,
        )
        output["status"] = "completed"
        output["result"] = result

        print("Agent status:", result["status"])
        print("Answer:", result["answer"])
        print("Citations:", result["citations"])
        print(
            "Search calls:",
            sum(e["event"] == "search" for e in result["events"]),
        )

    except Exception as error:
        output["status"] = "error"
        output["error_type"] = type(error).__name__
        raise

    finally:
        output["model_calls"] = controller.calls
        controller.close()

        folder = ROOT / "starter/results/day7/agent_smoke"
        folder.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        path = folder / f"{question['id']}_{stamp}.json"

        path.write_text(
            json.dumps(
                output,
                ensure_ascii=False,
                indent=2,
                allow_nan=False,
            ),
            encoding="utf-8",
        )
        print("Model requests attempted:", len(controller.calls))
        print("Saved:", path)


if __name__ == "__main__":
    main()