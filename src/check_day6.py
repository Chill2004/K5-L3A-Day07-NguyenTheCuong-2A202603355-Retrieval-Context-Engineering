"""Read-only check of the Day 6 vector store."""

import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

database_url = os.environ["DATABASE_URL"]
strategy = os.getenv("DAY6_STRATEGY", "A")

with psycopg.connect(database_url, connect_timeout=5) as connection:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT COUNT(*),
                   MIN(vector_dims(embedding)),
                   MAX(vector_dims(embedding))
            FROM ingestion_chunks
            WHERE strategy = %s
            """,
            (strategy,),
        )
        count, min_dimensions, max_dimensions = cursor.fetchone()

if count == 0:
    raise ValueError("Selected Day 6 index is empty.")

if (min_dimensions, max_dimensions) != (384, 384):
    raise ValueError("Expected 384-dimensional embeddings.")

print("Strategy:", strategy)
print("Chunks:", count)
print("Dimensions:", min_dimensions)
print("Day07 -> Day06 connection: OK")