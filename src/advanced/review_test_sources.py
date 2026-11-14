"""Collect original pages for developing the Advanced benchmark."""

import json
from pathlib import Path

import pymupdf

from src.advanced.entities import caption_entities


ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "starter/data/advanced"
OUTPUT = BASE / "test_source_review"

CANDIDATES = [
    ("table", "O.1"),
    ("table", "O.2"),
    ("table", "1.1"),
    ("table", "1.2"),
    ("table", "3.1"),
    ("table", "11.1"),
    ("figure", "O.11"),
    ("figure", "O.15"),
    ("figure", "S2.1"),
    ("figure", "5.3"),
    ("figure", "10.2"),
    ("figure", "O.9"),
    ("figure", "O.10"),
    ("figure", "2.1"),
    ("figure", "7.1"),
    ("figure", "S6.1"),
    ("table", "11.2"),
    ("table", "S6.1"),
    ("figure", "11.4"),
]

def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)

    pages = json.loads(
        (BASE / "pages.json").read_text(encoding="utf-8-sig")
    )

    catalog = {}
    for page in pages:
        for entity in caption_entities(page["text"]):
            catalog.setdefault(entity, []).append(page)

    records = []
    reading = []

    with pymupdf.open(
        BASE / "raw/world-development-report-2018.pdf"
    ) as document:
        for kind, identifier in CANDIDATES:
            matches = catalog.get((kind, identifier), [])
            if not matches:
                raise ValueError(
                    f"Cannot locate caption: {kind} {identifier}"
                )

            reading.append(
                f"\n========== {kind.upper()} {identifier} =========="
            )

            for page in matches:
                number = page["page"]
                image_path = OUTPUT / f"page_{number:03d}.png"

                if not image_path.exists():
                    document[number - 1].get_pixmap(
                        dpi=140
                    ).save(image_path)

                records.append({
                    "intended_split": "test",
                    "kind": kind,
                    "identifier": identifier,
                    "pdf_page": number,
                    "image": str(image_path.relative_to(ROOT)),
                })

                reading.extend([
                    f"PDF PAGE: {number}",
                    f"IMAGE: {image_path.name}",
                    page["text"],
                    "",
                ])

            print(
                kind,
                identifier,
                "| PDF pages:",
                [page["page"] for page in matches],
            )

    (OUTPUT / "sources.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (OUTPUT / "reading.txt").write_text(
        "\n".join(reading),
        encoding="utf-8",
    )

    print("Saved:", OUTPUT)
    print("Source review preparation: OK")
    print("Gemini requests: 0")


if __name__ == "__main__":
    main()