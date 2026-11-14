"""Import only Day 6 dev questions into the Day 7 contract."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

day6_path = (
    ROOT.parent
    / "K5-L3A-Nguyen-The-Cuong-2A202603355-Day06-DataIngestionEngineering"
    / "benchmark/questions.jsonl"
)

raw_questions = [
    json.loads(line)
    for line in day6_path.read_text(
        encoding="utf-8-sig"
    ).splitlines()
    if line.strip()
]

questions = []

for question in raw_questions:
    if question["split"] != "dev":
        continue

    questions.append({
        "id": question["id"],
        "split": "dev",
        "answerable": True,
        "question": question["question"],
        "expected_answer": question["expected_answer"],
        "gold": [{
            "source_id": question["gold_source_id"],
            "page": question["gold_page"],
            "evidence": question["evidence_quote"],
        }],
        "filter": question.get("filter"),
    })

if len(questions) != 15:
    raise ValueError("Expected exactly 15 answerable dev questions.")

if len({question["id"] for question in questions}) != 15:
    raise ValueError("Duplicate question IDs.")

output = ROOT / "starter/data/day6/dev_questions.json"
output.parent.mkdir(parents=True, exist_ok=True)

output.write_text(
    json.dumps(questions, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)

print("Answerable dev questions:", len(questions))
print("Questions with filter:", sum(
    bool(question["filter"]) for question in questions
))
print("Saved:", output)
print("Dev import: OK")