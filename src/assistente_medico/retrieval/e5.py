"""Adaptador de embeddings E5 com mean pooling e normalização L2."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any


class E5Embedder:  # pragma: no cover - exercised by index build/evaluation
    """Carrega o modelo apenas quando o índice é construído ou consultado."""

    def __init__(
        self, model_id: str, *, batch_size: int = 8, max_length: int = 512
    ) -> None:
        import torch
        from transformers import AutoModel, AutoTokenizer

        self.model_id = model_id
        self.batch_size = batch_size
        self.max_length = max_length
        self._torch = torch
        self._tokenizer = AutoTokenizer.from_pretrained(model_id)  # type: ignore[no-untyped-call]
        self._model = AutoModel.from_pretrained(model_id)
        self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._model.to(self._device)
        self._model.eval()

    def _embed(self, texts: Sequence[str], prefix: str) -> list[list[float]]:
        torch = self._torch
        vectors: list[list[float]] = []
        for start in range(0, len(texts), self.batch_size):
            batch = [
                f"{prefix}: {text}" for text in texts[start : start + self.batch_size]
            ]
            encoded: dict[str, Any] = self._tokenizer(
                batch,
                max_length=self.max_length,
                padding=True,
                truncation=True,
                return_tensors="pt",
            )
            encoded = {key: value.to(self._device) for key, value in encoded.items()}
            with torch.inference_mode():
                hidden = self._model(**encoded).last_hidden_state
            mask = encoded["attention_mask"].unsqueeze(-1).bool()
            hidden = hidden.masked_fill(~mask, 0.0)
            pooled = hidden.sum(dim=1) / mask.sum(dim=1).clamp(min=1)
            normalized = torch.nn.functional.normalize(pooled, p=2, dim=1)
            vectors.extend(normalized.cpu().float().tolist())
        return vectors

    def embed_passages(self, texts: Sequence[str]) -> list[list[float]]:
        return self._embed(texts, "passage")

    def embed_queries(self, texts: Sequence[str]) -> list[list[float]]:
        return self._embed(texts, "query")
