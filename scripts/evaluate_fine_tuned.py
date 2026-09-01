"""Compara o modelo-base pareado e seu adaptador no conjunto fechado."""

from __future__ import annotations

import gc
import json
import sys
import time
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from assistente_medico.evaluation import run_baseline  # noqa: E402
from assistente_medico.evaluation.baseline import load_cases  # noqa: E402


def _load_model(base_model: str, adapter: Path | None) -> tuple[Any, Any]:
    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

    tokenizer = AutoTokenizer.from_pretrained(base_model)
    model = AutoModelForCausalLM.from_pretrained(
        base_model,
        quantization_config=BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
        ),
        device_map={"": 0},
        dtype=torch.float16,
    )
    if adapter is not None:
        model = PeftModel.from_pretrained(model, adapter)
    model.eval()
    return model, tokenizer


def _provider(model: Any, tokenizer: Any) -> Any:
    import torch

    def generate(prompt: str, **options: Any) -> tuple[str, dict[str, Any]]:
        encoded = tokenizer.apply_chat_template(
            [{"role": "user", "content": prompt}],
            add_generation_prompt=True,
            tokenize=True,
            return_dict=True,
            return_tensors="pt",
        ).to(model.device)
        started = time.perf_counter()
        with torch.inference_mode():
            output = model.generate(
                **encoded,
                max_new_tokens=options["num_predict"],
                do_sample=False,
                pad_token_id=tokenizer.eos_token_id,
            )
        latency = time.perf_counter() - started
        generated = output[0][encoded["input_ids"].shape[-1] :]
        return tokenizer.decode(generated, skip_special_tokens=True), {
            "latency_seconds": latency,
            "eval_count": int(generated.shape[0]),
            "prompt_eval_count": int(encoded["input_ids"].shape[-1]),
        }

    return generate


def _write_result(name: str, payload: dict[str, Any]) -> None:
    output = PROJECT_ROOT / "reports" / "training" / f"{name}.json"
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def main() -> None:  # pragma: no cover - integration with GPU
    import torch

    training = json.loads(
        (PROJECT_ROOT / "configs" / "training.json").read_text(encoding="utf-8")
    )
    baseline_config = json.loads(
        (PROJECT_ROOT / "configs" / "baseline.json").read_text(encoding="utf-8")
    )
    cases = load_cases(PROJECT_ROOT / baseline_config["evaluation_dataset"])
    common = {
        **baseline_config,
        "provider": "transformers-local",
        "model": training["base_model"],
        "num_predict": 300,
    }

    base, tokenizer = _load_model(training["base_model"], None)
    paired = run_baseline(common, cases, generate=_provider(base, tokenizer))
    _write_result("paired_base_evaluation", paired)
    del base, tokenizer
    gc.collect()
    torch.cuda.empty_cache()

    adapter_path = PROJECT_ROOT / training["output_dir"]
    tuned, tokenizer = _load_model(training["base_model"], adapter_path)
    tuned_config = {**common, "fine_tuned": True}
    fine_tuned = run_baseline(tuned_config, cases, generate=_provider(tuned, tokenizer))
    _write_result("fine_tuned_evaluation", fine_tuned)
    comparison = {
        "base_model": training["base_model"],
        "adapter": training["output_dir"],
        "paired_base": paired["aggregate"],
        "fine_tuned": fine_tuned["aggregate"],
        "delta": {
            key: fine_tuned["aggregate"][key] - paired["aggregate"][key]
            for key in paired["aggregate"]
            if key != "cases"
        },
    }
    _write_result("fine_tuning_comparison", comparison)
    print(json.dumps(comparison, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
