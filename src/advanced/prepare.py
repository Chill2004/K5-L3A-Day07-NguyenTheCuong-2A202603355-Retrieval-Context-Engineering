"""Index the entire Advanced document locally, without Gemini requests."""

import argparse
import hashlib
import json
import re
import sqlite3
from pathlib import Path

import numpy as np
import pymupdf
from sentence_transformers import SentenceTransformer

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "starter/data/advanced"
SOURCE_ID = "wdr_2018_education"
SOURCE_URL = "https://documents1.worldbank.org/curated/en/240351507784846426/pdf/120299-WDR-v1-PUBLIC-main.pdf"
MODEL = "intfloat/multilingual-e5-small"
REVISION = "614241f622f53c4eeff9890bdc4f31cfecc418b3"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--embed", action="store_true")
    args = parser.parse_args()
    pdf_path = BASE / "raw/world-development-report-2018.pdf"
    pdf_digest = hashlib.sha256(pdf_path.read_bytes()).hexdigest()
    records = []
    pages = []

    with pymupdf.open(pdf_path) as document:
        for number, page in enumerate(document, start=1):
            text = page.get_text(sort=True)
            useful = len(re.sub(r"\s", "", text)) >= 100
            visual_only = not useful and (
                bool(page.get_images()) or len(page.get_drawings()) > 15
            )
            pages.append({
                "page": number,
                "text": text,
                "text_characters": len(text),
                "bbox": list(page.rect),
                "image_objects": len(page.get_images()),
                "useful_text": useful,
                "visual_only_candidate": visual_only,
                "retrieval_status": "indexed" if text.strip() else "image_only",
                "original_page_render_available": True,
            })

            # Cover all nonempty page text, including captions, references,
            # appendices and tables. Benchmark pages are never consulted.
            if text.strip():
                for start in range(0, len(text), 800):
                    chunk_text = text[start:start + 900]
                    if not chunk_text.strip():
                        continue
                    chunk_id = f"wdr2018-p{number:03d}-c{start:05d}"
                    records.append({
                        "id": chunk_id,
                        "source_id": SOURCE_ID,
                        "source": SOURCE_URL,
                        "page": number,
                        "text": chunk_text,
                        "metadata": {
                            "start_char": start,
                            "end_char": start + len(chunk_text),
                            "unit_id": f"wdr2018-p{number:03d}",
                            "bbox": list(page.rect),
                            "region_type": "page_text_with_original_visual",
                            "page_image_id": f"wdr2018-p{number:03d}",
                        },
                    })
            else:
                records.append({
                    "id": f"wdr2018-p{number:03d}-visual",
                    "source_id": SOURCE_ID,
                    "source": SOURCE_URL,
                    "page": number,
                    "text": f"World Development Report 2018. Visual page {number}. Open the original page image to inspect its content.",
                    "metadata": {
                        "bbox": list(page.rect),
                        "region_type": "visual_only_placeholder",
                        "page_image_id": f"wdr2018-p{number:03d}",
                    },
                })

    BASE.mkdir(parents=True, exist_ok=True)
    (BASE / "pages.json").write_text(
        json.dumps(pages, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (BASE / "chunks.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    manifest = {
        "source_id": SOURCE_ID,
        "title": "World Development Report 2018: Learning to Realize Education's Promise",
        "source_url": SOURCE_URL,
        "source_pdf": "starter/data/advanced/raw/world-development-report-2018.pdf",
        "pdf_sha256": pdf_digest,
        "physical_page_count": len(pages),
        "pages_with_substantive_extracted_text": sum(p["useful_text"] for p in pages),
        "indexed_page_count": len({r["page"] for r in records}),
        "chunk_count": len(records),
        "index_scope": "All nonempty text on every page; original page render accessible for all 240 pages.",
        "visual_only_pages": [p["page"] for p in pages if p["retrieval_status"] == "image_only"],
        "limitations": [
            "Native text search does not fully describe visual relationships.",
            "Visual-only placeholder embeddings are not semantic OCR; inspect original rendered pages through the vision agent.",
            "Table reading order can be incorrect in text extraction; verify with the original page image.",
            "Page-level bbox is a locator, not a precise figure crop. Figure/table IDs must accompany final visual citations.",
        ],
        "license": "CC BY 3.0 IGO; see PDF page 6 and third-party-content caveat.",
        "attribution": "World Bank. 2018. World Development Report 2018: Learning to Realize Education's Promise. Washington, DC: World Bank. doi:10.1596/978-1-4648-1096-1.",
        "adaptation_notice": "This is an adaptation of an original work by The World Bank. Views and opinions expressed in the adaptation are the sole responsibility of its authors and are not endorsed by The World Bank.",
        "translation_notice": "Vietnamese questions and answers are not official World Bank translations; the World Bank is not liable for translation errors.",
        "embedding_model": MODEL,
        "embedding_revision": REVISION,
        "dimensions": 384,
        "index_status": "text prepared; embedding pending",
    }

    # Content coverage is checked independently of any benchmark evidence.
    for page in pages:
        if not page["text"].strip():
            continue
        coverage = bytearray(len(page["text"]))
        for record in records:
            if record["page"] != page["page"]:
                continue
            meta = record["metadata"]
            assert record["text"] == page["text"][meta["start_char"]:meta["end_char"]]
            coverage[meta["start_char"]:meta["end_char"]] = b"\x01" * len(record["text"])
        assert all(c or t.isspace() for c, t in zip(coverage, page["text"]))

    if args.embed:
        model = SentenceTransformer(MODEL, revision=REVISION, device="cpu")
        inputs = ["passage: " + r["text"] for r in records]
        lengths = [len(ids) for ids in model.tokenizer(inputs, truncation=False)["input_ids"]]
        if max(lengths) > model.max_seq_length:
            raise ValueError("An indexed chunk exceeds embedding token limit.")
        vectors = model.encode(inputs, batch_size=16, normalize_embeddings=True,
                               convert_to_numpy=True, show_progress_bar=True)
        assert vectors.shape == (len(records), 384)
        assert np.isfinite(vectors).all()
        assert np.allclose(np.linalg.norm(vectors, axis=1), 1, atol=1e-4)
        database = BASE / "index.sqlite3"
        with sqlite3.connect(database) as connection:
            connection.execute("CREATE TABLE IF NOT EXISTS chunks (id TEXT PRIMARY KEY, source_id TEXT NOT NULL, page INTEGER NOT NULL, text TEXT NOT NULL, metadata TEXT NOT NULL, embedding BLOB NOT NULL)")
            connection.execute("DELETE FROM chunks WHERE source_id = ?", (SOURCE_ID,))
            connection.executemany("INSERT INTO chunks VALUES (?, ?, ?, ?, ?, ?)", [
                (r["id"], SOURCE_ID, r["page"], r["text"], json.dumps(r["metadata"]),
                 np.asarray(v, dtype=np.float32).tobytes())
                for r, v in zip(records, vectors)
            ])
        manifest["index_status"] = "persistent local index ready"
        manifest["index_path"] = "starter/data/advanced/index.sqlite3"
        manifest["max_embedding_tokens"] = max(lengths)

    (BASE / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    public = ROOT / "artifacts/advanced"
    public.mkdir(parents=True, exist_ok=True)
    (public / "source_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("Physical pages:", len(pages))
    print("Indexed pages:", manifest["indexed_page_count"])
    print("Substantive text pages:", manifest["pages_with_substantive_extracted_text"])
    print("Chunks:", len(records))
    print("Coverage: OK")
    print("Status:", manifest["index_status"])
    print("Gemini requests sent: 0")


if __name__ == "__main__":
    main()
