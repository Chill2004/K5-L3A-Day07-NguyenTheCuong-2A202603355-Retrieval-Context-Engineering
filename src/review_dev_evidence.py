"""Review q06 evidence and validate dev gold against source pages."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DAY6 = (
    ROOT.parent
    / "K5-L3A-Nguyen-The-Cuong-2A202603355-Day06-DataIngestionEngineering"
)

path = ROOT / "starter/data/day6/dev_questions.json"
questions = json.loads(path.read_text(encoding="utf-8-sig"))


def normalize(text):
    return " ".join(text.split())


q06 = next(q for q in questions if q["id"] == "q06")
original = normalize(q06["gold"][0]["evidence"])
first_sentence, separator, _ = original.partition(".")

if not separator:
    raise ValueError("Cannot identify the first sentence of q06.")

evidence = first_sentence + "."

if not evidence.endswith("một điểm đánh giá."):
    raise ValueError("Unexpected q06 sentence; inspect before saving.")

q06["gold"][0]["evidence"] = evidence
q06["evidence_review"] = (
    "Day07 preparation: retain the complete general rule and "
    "under-2-credit exception; remove unrelated assessment details. "
    "Day06 benchmark is unchanged."
)

pages = [
    json.loads(line)
    for line in (DAY6 / "results/pages.jsonl")
    .read_text(encoding="utf-8-sig").splitlines()
    if line.strip()
]

for question in questions:
    for gold in question["gold"]:
        found = any(
            page["document_id"] == gold["source_id"]
            and page["page"] == gold["page"]
            and normalize(gold["evidence"]) in normalize(page["text"])
            for page in pages
        )

        if not found:
            raise ValueError(
                f"Evidence missing from source: {question['id']}"
            )

path.write_text(
    json.dumps(questions, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)

print("q06 reviewed evidence:", evidence)
print("Dev source evidence checks:", len(questions))
print("Evidence review: OK")