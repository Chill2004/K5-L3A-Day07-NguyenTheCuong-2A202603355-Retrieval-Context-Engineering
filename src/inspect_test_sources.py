"""Export source pages for preparing new Day 7 test questions."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DAY6 = (
    ROOT.parent
    / "K5-L3A-Nguyen-The-Cuong-2A202603355-Day06-DataIngestionEngineering"
)

pages = [
    json.loads(line)
    for line in (DAY6 / "results/pages.jsonl")
    .read_text(encoding="utf-8-sig").splitlines()
    if line.strip()
]

selected_pages = {40, 41, 49, 60, 71}
selected = [
    page for page in pages
    if page["page"] in selected_pages
]

if len(selected) != len(selected_pages):
    raise ValueError("Some requested source pages are missing.")

blocks = [
    f"\n{'=' * 60}\nPDF PAGE: {page['page']}\n\n{page['text']}"
    for page in selected
]

output = ROOT / "starter/data/day6/test_source_review.txt"
output.write_text("\n".join(blocks), encoding="utf-8")

print("Exported pages:", sorted(selected_pages))
print("Saved:", output)