"""Executa a integração real da Etapa 6 e preserva a resposta validada."""

from __future__ import annotations

import json
import sys
import time
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from assistente_medico.chains import ClinicalAssistantChain  # noqa: E402
from assistente_medico.inference import FineTunedLocalProvider  # noqa: E402
from assistente_medico.repositories import ClinicalRepository  # noqa: E402
from assistente_medico.retrieval import VectorIndex  # noqa: E402
from assistente_medico.retrieval.e5 import E5Embedder  # noqa: E402
from assistente_medico.tools import ClinicalToolRegistry  # noqa: E402


def main() -> None:
    assistant_config = json.loads(
        (PROJECT_ROOT / "configs/assistant.json").read_text(encoding="utf-8")
    )
    retrieval_config = json.loads(
        (PROJECT_ROOT / assistant_config["retrieval_config"]).read_text(
            encoding="utf-8"
        )
    )
    tools = ClinicalToolRegistry(
        ClinicalRepository(PROJECT_ROOT / assistant_config["database"])
    )
    index = VectorIndex.load(PROJECT_ROOT / retrieval_config["index_file"])
    embedder = E5Embedder(
        retrieval_config["embedding_model"],
        batch_size=retrieval_config["batch_size"],
        max_length=retrieval_config["max_length"],
    )
    model = FineTunedLocalProvider(
        assistant_config["base_model"],
        PROJECT_ROOT / assistant_config["adapter_dir"],
        max_new_tokens=assistant_config["max_new_tokens"],
    )
    chain = ClinicalAssistantChain(
        tools=tools,
        index=index,
        embedder=embedder,
        model=model,
        prompt_version=assistant_config["prompt_version"],
        top_k=retrieval_config["top_k"],
        minimum_score=retrieval_config["minimum_score"],
        as_of=date.fromisoformat(retrieval_config["as_of"]),
    )
    started = time.perf_counter()
    response = chain.invoke(
        {
            "patient_id": "PAT-SYN-003",
            "question": (
                "Quais exames estão pendentes e qual protocolo limita a conduta?"
            ),
            "specialty": "clinica_medica",
        }
    )
    payload = {
        "prompt_version": assistant_config["prompt_version"],
        "model": assistant_config["base_model"],
        "adapter": assistant_config["adapter_dir"],
        "elapsed_seconds": time.perf_counter() - started,
        "response": response.model_dump(mode="json"),
    }
    output = PROJECT_ROOT / "reports/chains/langchain_demo.json"
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
