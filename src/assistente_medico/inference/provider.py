"""Provider do adaptador QLoRA, isolado da chain e carregado sob demanda."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol


class TextGenerationProvider(Protocol):
    def generate(self, prompt: str) -> str: ...


class FineTunedLocalProvider:  # pragma: no cover - integração GPU
    def __init__(
        self,
        base_model: str,
        adapter_dir: Path,
        *,
        max_new_tokens: int = 300,
    ) -> None:
        import torch
        from peft import PeftModel
        from transformers import (
            AutoModelForCausalLM,
            AutoTokenizer,
            BitsAndBytesConfig,
        )

        self._torch = torch
        self._tokenizer = AutoTokenizer.from_pretrained(  # type: ignore[no-untyped-call]
            base_model
        )
        base = AutoModelForCausalLM.from_pretrained(
            base_model,
            quantization_config=BitsAndBytesConfig(  # type: ignore[no-untyped-call]
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,
            ),
            device_map={"": 0},
            dtype=torch.float16,
        )
        self._model = PeftModel.from_pretrained(base, adapter_dir)
        self._model.eval()
        self._max_new_tokens = max_new_tokens

    def generate(self, prompt: str) -> str:
        encoded: Any = self._tokenizer.apply_chat_template(
            [{"role": "user", "content": prompt}],
            add_generation_prompt=True,
            tokenize=True,
            return_dict=True,
            return_tensors="pt",
        ).to(self._model.device)
        with self._torch.inference_mode():
            output = self._model.generate(  # type: ignore[no-untyped-call]
                **encoded,
                max_new_tokens=self._max_new_tokens,
                do_sample=False,
                pad_token_id=self._tokenizer.eos_token_id,
            )
        generated = output[0][encoded["input_ids"].shape[-1] :]
        return str(self._tokenizer.decode(generated, skip_special_tokens=True))
