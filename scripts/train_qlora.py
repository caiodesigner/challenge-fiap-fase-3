"""Executa QLoRA e salva somente o adaptador PEFT e os logs."""

from __future__ import annotations

import json
import platform
import sys
import time
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line
    ]


def main() -> None:  # pragma: no cover - integration with GPU and model download
    import torch
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
    from torch.utils.data import Dataset
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        BitsAndBytesConfig,
        Trainer,
        TrainingArguments,
        set_seed,
    )

    config = json.loads(
        (PROJECT_ROOT / "configs" / "training.json").read_text(encoding="utf-8")
    )
    if not torch.cuda.is_available():
        raise RuntimeError(
            "QLoRA requer CUDA neste pipeline; nenhuma GPU foi detectada."
        )
    set_seed(config["seed"])
    tokenizer = AutoTokenizer.from_pretrained(config["base_model"])
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    class ChatDataset(Dataset[dict[str, torch.Tensor]]):
        def __init__(self, path: Path) -> None:
            self.rows = _read_jsonl(path)

        def __len__(self) -> int:
            return len(self.rows)

        def __getitem__(self, index: int) -> dict[str, torch.Tensor]:
            messages = self.rows[index]["messages"]
            text = tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=False,
            )
            prompt_text = tokenizer.apply_chat_template(
                messages[:-1], tokenize=False, add_generation_prompt=True
            )
            encoded = tokenizer(
                text,
                truncation=True,
                max_length=config["max_length"],
                padding="max_length",
                return_tensors="pt",
            )
            input_ids = encoded["input_ids"].squeeze(0)
            attention_mask = encoded["attention_mask"].squeeze(0)
            prompt_length = len(
                tokenizer(
                    prompt_text,
                    truncation=True,
                    max_length=config["max_length"],
                    add_special_tokens=False,
                )["input_ids"]
            )
            labels = input_ids.clone()
            labels[:prompt_length] = -100
            labels[attention_mask == 0] = -100
            return {
                "input_ids": input_ids,
                "attention_mask": attention_mask,
                "labels": labels,
            }

    quantization_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type=config["quantization"],
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )
    model = AutoModelForCausalLM.from_pretrained(
        config["base_model"],
        quantization_config=quantization_config,
        device_map={"": 0},
        torch_dtype=torch.float16,
    )
    model.config.use_cache = False
    model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=True)
    model = get_peft_model(
        model,
        LoraConfig(
            r=config["lora_r"],
            lora_alpha=config["lora_alpha"],
            lora_dropout=config["lora_dropout"],
            bias="none",
            task_type="CAUSAL_LM",
            target_modules="all-linear",
        ),
    )
    trainable, total = model.get_nb_trainable_parameters()
    output_dir = PROJECT_ROOT / config["output_dir"]
    arguments = TrainingArguments(
        output_dir=str(output_dir),
        num_train_epochs=config["epochs"],
        per_device_train_batch_size=config["batch_size"],
        per_device_eval_batch_size=1,
        gradient_accumulation_steps=config["gradient_accumulation_steps"],
        learning_rate=config["learning_rate"],
        warmup_ratio=config["warmup_ratio"],
        weight_decay=config["weight_decay"],
        logging_steps=config["logging_steps"],
        eval_strategy="epoch",
        save_strategy="epoch",
        save_total_limit=2,
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
        fp16=True,
        gradient_checkpointing=True,
        optim="paged_adamw_8bit",
        report_to="none",
        seed=config["seed"],
        data_seed=config["seed"],
    )
    trainer = Trainer(
        model=model,
        args=arguments,
        train_dataset=ChatDataset(PROJECT_ROOT / config["train_file"]),
        eval_dataset=ChatDataset(PROJECT_ROOT / config["validation_file"]),
    )
    started = time.time()
    train_result = trainer.train()
    evaluation = trainer.evaluate()
    model.save_pretrained(output_dir, safe_serialization=True)
    tokenizer.save_pretrained(output_dir)
    metadata = {
        "base_model": config["base_model"],
        "adapter_dir": config["output_dir"],
        "method": "QLoRA",
        "quantization": "4-bit NF4 with double quantization",
        "trainable_parameters": trainable,
        "total_parameters": total,
        "trainable_percentage": 100 * trainable / total,
        "train_metrics": train_result.metrics,
        "evaluation_metrics": evaluation,
        "elapsed_seconds": time.time() - started,
        "seed": config["seed"],
        "gpu": torch.cuda.get_device_name(0),
        "gpu_memory_bytes": torch.cuda.get_device_properties(0).total_memory,
        "python": platform.python_version(),
        "torch": torch.__version__,
    }
    report_dir = PROJECT_ROOT / "reports" / "training"
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "training_metrics.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    trainer.save_state()
    print(json.dumps(metadata, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"Falha no treinamento: {error}", file=sys.stderr)
        raise
