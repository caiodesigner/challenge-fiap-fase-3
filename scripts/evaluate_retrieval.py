"""Mede Recall@K e MRR do índice de protocolos."""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from assistente_medico.retrieval import VectorIndex  # noqa: E402
from assistente_medico.retrieval.e5 import E5Embedder  # noqa: E402


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line
    ]


def main() -> None:
    config = json.loads(
        (PROJECT_ROOT / "configs/retrieval.json").read_text(encoding="utf-8")
    )
    index = VectorIndex.load(PROJECT_ROOT / config["index_file"])
    embedder = E5Embedder(
        config["embedding_model"],
        batch_size=config["batch_size"],
        max_length=config["max_length"],
    )
    rows = []
    reciprocal_ranks = []
    positive_count = 0
    negative_count = 0
    rejected_negatives = 0
    for case in _read_jsonl(PROJECT_ROOT / config["evaluation_file"]):
        results = index.search(
            case["query"],
            embedder,
            top_k=config["top_k"],
            minimum_score=config["minimum_score"],
            specialty=case["specialty"],
            as_of=date.fromisoformat(config["as_of"]),
        )
        source_ids = [result.chunk.source_id for result in results]
        expected = case["expected_source_id"]
        if expected is None:
            negative_count += 1
            rejected_negatives += not source_ids
            rank = None
        else:
            positive_count += 1
            rank = source_ids.index(expected) + 1 if expected in source_ids else None
            reciprocal_ranks.append(1 / rank if rank else 0.0)
        rows.append(
            {
                **case,
                "retrieved": [
                    {
                        "source_id": result.chunk.source_id,
                        "score": result.score,
                        "citation": result.citation,
                    }
                    for result in results
                ],
                "rank": rank,
            }
        )
    count = len(rows)
    payload = {
        "model_id": index.model_id,
        "top_k": config["top_k"],
        "cases": count,
        "positive_cases": positive_count,
        "negative_cases": negative_count,
        "recall_at_k": sum(
            row["rank"] is not None
            for row in rows
            if row["expected_source_id"] is not None
        )
        / positive_count,
        "mrr": sum(reciprocal_ranks) / positive_count,
        "out_of_scope_rejection_rate": rejected_negatives / negative_count,
        "results": rows,
    }
    output = PROJECT_ROOT / config["report_file"]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {key: value for key, value in payload.items() if key != "results"}, indent=2
        )
    )


if __name__ == "__main__":
    main()
