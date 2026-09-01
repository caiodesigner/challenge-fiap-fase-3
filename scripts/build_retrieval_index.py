"""Constrói o índice vetorial dos protocolos ativos e versionados."""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from assistente_medico.retrieval import VectorIndex, chunks_from_protocols  # noqa: E402
from assistente_medico.retrieval.e5 import E5Embedder  # noqa: E402


def main() -> None:
    config = json.loads(
        (PROJECT_ROOT / "configs/retrieval.json").read_text(encoding="utf-8")
    )
    protocols = json.loads(
        (PROJECT_ROOT / config["protocols_file"]).read_text(encoding="utf-8")
    )
    chunks = chunks_from_protocols(protocols)
    embedder = E5Embedder(
        config["embedding_model"],
        batch_size=config["batch_size"],
        max_length=config["max_length"],
    )
    index = VectorIndex.build(chunks, embedder)
    output = PROJECT_ROOT / config["index_file"]
    index.save(output)
    print(f"Índice criado: {output} ({len(chunks)} chunks)")


if __name__ == "__main__":
    main()
