"""Download, pin and locally check the reranker on a dev query."""

import json
import math
from pathlib import Path

from huggingface_hub import model_info
from sentence_transformers import CrossEncoder

from src.hybrid_retriever import HybridRetriever


ROOT = Path(__file__).resolve().parents[1]
MODEL_NAME = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"


def main():
    config_path = ROOT / "artifacts/reranker_config.json"

    if config_path.exists():
        config = json.loads(
            config_path.read_text(encoding="utf-8")
        )
        assert config["model"] == MODEL_NAME
        revision = config["revision"]
    else:
        revision = model_info(MODEL_NAME).sha

    model = CrossEncoder(
        MODEL_NAME,
        revision=revision,
        device="cpu",
        max_length=512,
    )

    questions = json.loads(
        (ROOT / "starter/data/day6/dev_questions.json").read_text(
            encoding="utf-8-sig"
        )
    )
    question = next(q for q in questions if q["id"] == "q01")

    retriever = HybridRetriever(candidate_k=20, rrf_k=60)
    candidates = retriever.search(
        question["question"],
        filters=question.get("filter"),
        top_k=20,
    )
    assert candidates

    pairs = [
        (question["question"], chunk["text"])
        for chunk in candidates
    ]

    lengths = [
        len(model.tokenizer(
            query,
            text,
            truncation=False,
        )["input_ids"])
        for query, text in pairs
    ]
    if max(lengths) > 512:
        raise ValueError("A query-passage pair exceeds 512 tokens.")

    scores = model.predict(
        pairs,
        batch_size=8,
        show_progress_bar=False,
    )
    scores = [float(score) for score in scores]

    assert len(scores) == len(candidates)
    assert all(math.isfinite(score) for score in scores)

    config = {
        "model": MODEL_NAME,
        "revision": revision,
        "device": "cpu",
        "max_length": 512,
        "batch_size": 8,
        "candidate_k": 20,
        "inference": "local",
        "api_cost_usd": 0,
    }

    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        json.dumps(config, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    ranked = sorted(
        zip(candidates, scores),
        key=lambda item: (-item[1], item[0]["id"]),
    )

    print("Model:", MODEL_NAME)
    print("Revision:", revision)
    print("Candidate count:", len(candidates))
    print("Max pair tokens:", max(lengths))

    for rank, (chunk, score) in enumerate(ranked[:3], start=1):
        print(
            f"Rank: {rank} | page: {chunk['page']} | "
            f"reranker score: {score:.6f}"
        )

    print("Saved:", config_path)
    print("Local reranker check: OK")


if __name__ == "__main__":
    main()