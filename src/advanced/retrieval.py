"""Persistent dense/lexical retrieval with access to original PDF page images."""

import io
import json
import re
import sqlite3
from collections import Counter
from pathlib import Path

import numpy as np
import pymupdf
from sentence_transformers import SentenceTransformer

from src.advanced.prepare import BASE, MODEL, REVISION, SOURCE_ID, SOURCE_URL
from src.advanced.entities import caption_entities, requested_entities


def tokens(text):
    return re.findall(r"\w+", text.casefold())


class AdvancedRetriever:
    def __init__(self):
        database = BASE / "index.sqlite3"
        if not database.exists():
            raise FileNotFoundError("Run python -m src.advanced.prepare --embed first.")
        with sqlite3.connect(database.as_uri() + "?mode=ro", uri=True) as connection:
            rows = connection.execute("SELECT id,source_id,page,text,metadata,embedding FROM chunks WHERE source_id=? ORDER BY id", (SOURCE_ID,)).fetchall()
        if not rows:
            raise ValueError("Advanced index is empty.")
        self.chunks = [
            {"id":r[0],"source_id":r[1],"page":r[2],"text":r[3],"metadata":json.loads(r[4]),"source":SOURCE_URL}
            for r in rows
        ]
        self.vectors = np.stack([np.frombuffer(r[5], dtype=np.float32) for r in rows])
        assert self.vectors.shape[1] == 384
        self.counts = [Counter(tokens(c["text"])) for c in self.chunks]
        df = Counter(term for count in self.counts for term in count)
        self.idf = {term: np.log(1+(len(rows)-freq+0.5)/(freq+0.5)) for term,freq in df.items()}
        self.lengths = np.array([sum(c.values()) for c in self.counts])
        self.average_length = float(self.lengths.mean())
        self.model = SentenceTransformer(MODEL, revision=REVISION, device="cpu")
        self.document = pymupdf.open(BASE / "raw/world-development-report-2018.pdf")
        self.entity_pages = {}
        for page in json.loads((BASE / "pages.json").read_text(encoding="utf-8")):
            for entity in caption_entities(page["text"]):
                self.entity_pages.setdefault(entity,set()).add(page["page"])

    def search(self, query, *, top_k=3, pages=None):
        if not isinstance(query,str) or not query.strip():
            raise ValueError("Query must be a nonempty string.")
        if type(top_k) is not int or not 1<=top_k<=20:
            raise ValueError("top_k must be between 1 and 20.")
        eligible = [i for i,c in enumerate(self.chunks) if pages is None or c["page"] in pages]
        if not eligible:
            return []
        text = "query: " + query.strip()
        if len(self.model.tokenizer(text,truncation=False)["input_ids"])>self.model.max_seq_length:
            raise ValueError("Query exceeds embedding token limit.")
        vector = self.model.encode(text,normalize_embeddings=True,show_progress_bar=False)
        dense = self.vectors @ vector
        lexical = np.zeros(len(self.chunks))
        for term in set(tokens(query)):
            idf = self.idf.get(term,0)
            for i in eligible:
                tf = self.counts[i].get(term,0)
                if tf:
                    lexical[i] += idf * tf * 2.2 / (tf+1.2*(0.25+0.75*self.lengths[i]/self.average_length))
        rankings = [sorted(eligible,key=lambda i:(-float(dense[i]),self.chunks[i]["id"]))[:40],
                    sorted((i for i in eligible if lexical[i]>0),key=lambda i:(-float(lexical[i]),self.chunks[i]["id"]))[:40]]
        fused = {}
        for ranking in rankings:
            for rank,index in enumerate(ranking,1):
                fused[index] = fused.get(index,0) + 1/(60+rank)
        exact_pages = set()
        for entity in requested_entities(query):
            exact_pages.update(self.entity_pages.get(entity,set()))
        # Caption lookup applies to any explicit figure/table/map reference.
        # The catalog is built from the entire source, never from gold labels.
        for index in eligible:
            if self.chunks[index]["page"] in exact_pages and index not in fused:
                fused[index] = 0.0
        # A tool result is a page, not multiple competing slices of one page.
        selected = []
        seen_pages = set()
        for index in sorted(fused,key=lambda i:(self.chunks[i]["page"] not in exact_pages,-fused[i],self.chunks[i]["id"])):
            page = self.chunks[index]["page"]
            if page in seen_pages:
                continue
            seen_pages.add(page)
            selected.append({**self.chunks[index],"score":fused[index],"page_id":f"wdr2018-p{page:03d}","lookup_method":"caption_id" if page in exact_pages else "hybrid_rrf"})
            if len(selected)==top_k:
                break
        return selected

    def read_page(self, number, dpi=120):
        if type(number) is not int or not 1<=number<=len(self.document):
            raise ValueError("Invalid PDF page number.")
        page = self.document[number-1]
        image = page.get_pixmap(dpi=dpi).tobytes("png")
        return {"page":number,"page_id":f"wdr2018-p{number:03d}",
                "text":page.get_text(sort=True),"bbox":list(page.rect),
                "image_bytes":image,"mime_type":"image/png"}

    def close(self):
        self.document.close()
