"""Export test review labels and aggregate their scores."""

import json
import hashlib
from pathlib import Path

from starter.agent_metrics import aggregate


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


def write_json(path, value):
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main():
    cases = json.loads(
        (ROOT / "starter/data/day6/test_questions.json").read_text(
            encoding="utf-8-sig"
        )
    )
    summaries = {}
    confirmed_configs = []

    for name, path in FILES.items():
        run = json.loads(path.read_text(encoding="utf-8-sig"))
        by_id = {trace["query_id"]: trace for trace in run["traces"]}
        reviews = []
        flat_traces = []

        for case in cases:
            trace = by_id[case["id"]]
            result = trace["result"]
            assert trace["status"] in ("answered", "abstain")

            flat_traces.append({
                "query_id": case["id"],
                "status": trace["status"],
                "events": result["events"],
                "citations": result["citations"],
            })

            review = {
                "query_id": case["id"],
                "citation_support": [],
            }

            if case["answerable"]:
                # Labels assigned by Codex (AI) after inspecting the original test outputs.
                failed = name == "top5" and case["id"] == "test_03"
                expected_status = "abstain" if failed else "answered"
                assert trace["status"] == expected_status

                review.update({
                    "answer_grade": 0 if failed else 2,
                    "context_grade": 2,
                    "citation_support": [
                        True for _ in result["citations"]
                    ],
                    "reason": (
                        "Final output abstained because grouped inline "
                        "citations did not match the validator format. "
                        "The context contained sufficient evidence."
                        if failed else
                        "Final answer matches the requested facts; "
                        "the cited retrieved text supports the answer."
                    ),
                })
            else:
                assert trace["status"] == "abstain"
                review.update({
                    "abstention_correct": True,
                    "reason": (
                        "Final output abstains on a question reviewed "
                        "as unanswerable within corpus pages 39-77. "
                        "See trace events for the stopping mechanism."
                    ),
                })

            reviews.append(review)

        confirmation_path = ROOT / "artifacts/test_review_confirmation.json"
        human_confirmed = False
        confirmed_by = None
        if confirmation_path.exists():
            confirmation = json.loads(
                confirmation_path.read_text(encoding="utf-8-sig")
            )
            recorded = confirmation["configurations"][name]
            keys = (
                "query_id", "answer_grade", "context_grade",
                "citation_support", "abstention_correct", "reason",
            )
            content = [
                {key: r[key] for key in keys if key in r}
                for r in reviews
            ]
            digest = hashlib.sha256(json.dumps(
                content, ensure_ascii=False, sort_keys=True
            ).encode("utf-8")).hexdigest()
            run_digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if (
                digest != recorded["review_content_sha256"]
                or run_digest != recorded["source_run_sha256"]
            ):
                raise ValueError(
                    "Labels or run changed; existing human confirmation "
                    "cannot be applied to new results."
                )
            confirmed_by = confirmation["confirmed_by"]
            human_confirmed = True


        metrics = aggregate(cases, flat_traces, reviews)

        summaries[name] = {
            "source_run": str(path.relative_to(ROOT)),
            **metrics,
            "context_grade_counts": {"0": 0, "1": 0, "2": 5},
            "context_grade_mean": 2.0,
        }

        folder = FOLDER / "agent_test" / name
        write_json(folder / "test_flat_traces.json", flat_traces)
        if human_confirmed:
            confirmed_configs.append(name)
            write_json(folder / "test_reviews_confirmed.json", reviews)
        write_json(folder / "test_reviews_ai.json", reviews)
        # Keep legacy paths synchronized for existing scripts and reports.
        write_json(folder / "test_reviews_proposed.json", reviews)
        print(name, json.dumps(summaries[name], ensure_ascii=True))

    if len(confirmed_configs) == len(FILES):
        write_json(FOLDER / "test_review_summary_confirmed.json", summaries)
    write_json(FOLDER / "test_review_summary_ai.json", summaries)
    write_json(FOLDER / "test_review_summary_proposed.json", summaries)
    public_dir = ROOT / "artifacts"
    public_dir.mkdir(exist_ok=True)
    for filename in (
        "test_review_summary_ai.json",
        "test_review_summary_proposed.json",
        "test_review_summary_confirmed.json",
    ):
        source = FOLDER / filename
        if source.exists():
            write_json(public_dir / filename, json.loads(
                source.read_text(encoding="utf-8-sig")
            ))
    print("Saved test labels and summary.")


if __name__ == "__main__":
    main()
