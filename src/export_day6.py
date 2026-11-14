"""Export the selected Day 6 index into the Day 7 chunk contract."""

import hashlib
import json
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

strategy = os.getenv("DAY6_STRATEGY", "A")
output_dir = ROOT / "starter/data/day6"

with psycopg.connect(
    os.environ["DATABASE_URL"],
    connect_timeout=5,
) as connection:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT chunk_id, document_id, source, page,
                   text, metadata, vector_dims(embedding)
            FROM ingestion_chunks
            WHERE strategy = %s
            ORDER BY document_id, page, chunk_id
            """,
            (strategy,),
        )
        rows = cursor.fetchall()

if not rows:
    raise ValueError("Selected index is empty.")

if any(row[6] != 384 for row in rows):
    raise ValueError("Expected 384-dimensional vectors.")

chunks = [
    {
        "id": row[0],
        "source_id": row[1],
        "source": row[2],
        "page": row[3],
        "text": row[4],
        "metadata": row[5],
    }
    for row in rows
]

if len({chunk["id"] for chunk in chunks}) != len(chunks):
    raise ValueError("Duplicate chunk IDs.")

output_dir.mkdir(parents=True, exist_ok=True)
path = output_dir / "chunks.json"

path.write_text(
    json.dumps(chunks, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)

snapshot = {
    "origin": "Day06 PostgreSQL ingestion_chunks",
    "strategy": strategy,
    "chunk_count": len(chunks),
    "source_page_count": len({
        (chunk["source_id"], chunk["page"])
        for chunk in chunks
    }),
    "dimensions": 384,
    "chunks_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
}

(output_dir / "snapshot.json").write_text(
    json.dumps(snapshot, indent=2) + "\n",
    encoding="utf-8",
)

print("Strategy:", strategy)
print("Exported chunks:", len(chunks))
print("Source pages:", snapshot["source_page_count"])
print("Saved:", path)
print("Export: OK")