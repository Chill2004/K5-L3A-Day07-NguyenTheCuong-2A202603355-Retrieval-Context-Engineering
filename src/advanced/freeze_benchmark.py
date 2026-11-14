"""Validate and freeze the Advanced benchmark before experiments."""

import hashlib
import json
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "starter/data/advanced"
BENCHMARK = BASE / "benchmark"

EXPECTED = {
    "dev": {
        "table": 3,
        "image": 3,
        "chart": 3,
        "multi_hop": 3,
        "text": 3,
        "unanswerable": 3,
    },
    "test": {
        "table": 6,
        "image": 5,
        "chart": 5,
        "multi_hop": 4,
        "text": 4,
        "unanswerable": 6,
    },
}


def normalize(text):
    return " ".join(
        unicodedata.normalize("NFC", text).casefold().split()
    )


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    output = BENCHMARK / "benchmark_freeze.json"
    if output.exists():
        raise FileExistsError(
            "Freeze already exists. Keep the original record."
        )

    files = {
        BASE / "raw/world-development-report-2018.pdf",
        BASE / "manifest.json",
        BASE / "chunks.json",
    }
    ids = set()
    question_texts = set()
    counts = {}

    for split, expected_groups in EXPECTED.items():
        path = BENCHMARK / f"{split}_questions.json"
        questions = json.loads(
            path.read_text(encoding="utf-8-sig")
        )
        assert len(questions) == sum(expected_groups.values())
        assert dict(Counter(
            q["group"] for q in questions
        )) == expected_groups
        files.add(path)

        for question in questions:
            assert question["split"] == split
            assert question["id"] not in ids
            ids.add(question["id"])

            normalized = normalize(question["question"])
            assert normalized not in question_texts
            question_texts.add(normalized)

            assert type(question["answerable"]) is bool

            if not question["answerable"]:
                assert question["group"] == "unanswerable"
                assert question["absence_reason"]
                assert question["absence_checks"]
                assert not question.get("gold")
                continue

            assert question["expected_answer"]
            assert question["gold"]
            assert question["evidence_mode"] == "all"

            for gold in question["gold"]:
                assert gold["source_id"] == "wdr_2018_education"
                assert 1 <= gold["page"] <= 240
                assert gold["locator"]
                x0, y0, x1, y1 = gold["bbox_normalized"]
                assert 0 <= x0 < x1 <= 1
                assert 0 <= y0 < y1 <= 1

                image = ROOT / gold["image"]
                assert image.is_file(), image
                assert image.read_bytes().startswith(
                    b"\x89PNG\r\n\x1a\n"
                )
                files.add(image)

            if question["group"] == "multi_hop":
                assert len({
                    gold["page"] for gold in question["gold"]
                }) >= 2

        counts[split] = dict(Counter(
            q["group"] for q in questions
        ))

    record = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "Source, benchmark questions and evidence images",
        "counts": counts,
        "test_total": 30,
        "required_pass_count": 27,
        "grading": {
            "answerable": (
                "Pass only if the final answer is correct and complete, "
                "including required units, conditions and calculations, "
                "with supporting page and region citations."
            ),
            "unanswerable": (
                "Pass only if the agent explicitly abstains without "
                "unsupported factual claims."
            ),
            "errors": (
                "System errors, timeouts and missing results count "
                "as failures in the full 30-question denominator."
            ),
        },
        "controls": [
            "Use dev only for configuration selection.",
            "Freeze the selected pipeline separately before test.",
            "Do not pass gold, expected answers or evidence crops to the agent.",
            "Do not tune using test results.",
            "Keep original runs and report errors.",
        ],
        "sha256": {
            path.relative_to(ROOT).as_posix(): sha256(path)
            for path in sorted(files)
        },
    }

    with output.open("x", encoding="utf-8") as handle:
        json.dump(
            record, handle, ensure_ascii=False, indent=2
        )

    public = ROOT / "artifacts/advanced/benchmark_freeze.json"
    public.parent.mkdir(parents=True, exist_ok=True)
    public.write_text(
        json.dumps(record, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("Dev: 18 questions")
    print("Test: 30 questions")
    print("Exact duplicate questions: 0")
    print("Hashed files:", len(files))
    print("Required result: at least 27/30")
    print("Saved:", output)
    print("Advanced benchmark freeze: OK")
    print("Gemini requests: 0")


if __name__ == "__main__":
    main()