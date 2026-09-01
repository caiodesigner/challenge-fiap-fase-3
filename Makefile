.PHONY: install data validate baseline prepare-training train evaluate-tuned index evaluate-retrieval evaluate-complete database demo-tools demo-chain demo-graph demo-safety demo-audit report ui test test-e2e lint type check

PYTHON := .venv/bin/python

install:
	python3.12 -m venv .venv
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -e ".[dev]"

data:
	$(PYTHON) scripts/generate_synthetic_data.py

validate:
	$(PYTHON) scripts/validate_data.py

baseline:
	$(PYTHON) scripts/run_baseline.py

prepare-training:
	$(PYTHON) scripts/prepare_fine_tuning_data.py

train:
	$(PYTHON) scripts/train_qlora.py

evaluate-tuned:
	$(PYTHON) scripts/evaluate_fine_tuned.py

index:
	$(PYTHON) scripts/build_retrieval_index.py

evaluate-retrieval:
	$(PYTHON) scripts/evaluate_retrieval.py

evaluate-complete:
	$(PYTHON) scripts/evaluate_complete_solution.py

database:
	$(PYTHON) scripts/build_clinical_database.py

demo-tools:
	$(PYTHON) scripts/demo_clinical_tools.py

demo-chain:
	$(PYTHON) scripts/demo_langchain.py

demo-graph:
	$(PYTHON) scripts/demo_langgraph.py

demo-safety:
	$(PYTHON) scripts/demo_safety.py

demo-audit:
	$(PYTHON) scripts/demo_audit.py

ui:
	.venv/bin/streamlit run app.py

report:
	$(PYTHON) scripts/build_final_report.py

test:
	$(PYTHON) -m pytest

test-e2e:
	$(PYTHON) -m pytest -m e2e --cov-fail-under=0

lint:
	$(PYTHON) -m ruff check .
	$(PYTHON) -m ruff format --check .

type:
	$(PYTHON) -m mypy

check: lint type test validate
