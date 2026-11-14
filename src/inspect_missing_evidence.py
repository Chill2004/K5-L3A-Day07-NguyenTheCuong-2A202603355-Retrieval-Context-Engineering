"""Export relevant source passages for unanswerable-question review."""

import json
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DAY6 = (
    ROOT.parent
    / "K5-L3A-Nguyen-The-Cuong-2A202603355-Day06-DataIngestionEngineering"
)


def searchable(text):
    text = unicodedata.normalize("NFD", text.casefold())
    text = "".join(
        character for character in text
        if unicodedata.category(character) != "Mn"
    )
    return " ".join(text.replace("đ", "d").split())


pages = [
    json.loads(line)
    for line in (DAY6 / "results/pages.jsonl")
    .read_text(encoding="utf-8-sig").splitlines()
    if line.strip()
]

keywords = [
    "lich thi",
    "hoc bong",
    "tai nang",
    "tri tue nhan tao",
    "2026",
    "2027",
]

blocks = []

for page in pages:
    text = searchable(page["text"])
    matched = [keyword for keyword in keywords if keyword in text]

    if matched:
        blocks.append(
            f"\n{'=' * 60}\n"
            f"PDF PAGE: {page['page']}\n"
            f"MATCHED: {', '.join(matched)}\n\n"
            f"{page['text']}"
        )

output = ROOT / "starter/data/day6/missing_evidence_review.txt"
output.write_text("\n".join(blocks), encoding="utf-8")

print("Source pages checked:", len(pages))
print("Relevant pages exported:", len(blocks))
print("Saved:", output)