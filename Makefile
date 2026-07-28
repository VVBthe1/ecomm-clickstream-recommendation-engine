.PHONY: help venv install download clean explore features train tune retrain analyze api all test dry-run

PYTHON ?= python3
VENV := .venv
BIN := $(VENV)/bin

help:
	@echo "make install    venv + deps"
	@echo "make download   Kaggle -> bronze (Oct + Nov)"
	@echo "make clean      bronze -> silver"
	@echo "make explore    EDA -> metadata/"
	@echo "make features   silver -> gold"
	@echo "make train      E1 + E2 + E_final (defaults) + best_model"
	@echo "make tune       hyperparameter search on E_final train"
	@echo "make retrain    E_final with tuned params -> best_model"
	@echo "make analyze    error analysis plots"
	@echo "make api        FastAPI on :8000"
	@echo "make all        full final pipeline (download..analyze)"
	@echo "make test       pytest"

venv:
	$(PYTHON) -m venv $(VENV)

install: venv
	$(BIN)/pip install -q -U pip
	$(BIN)/pip install -q -r requirements.txt

download:
	$(BIN)/python scripts/download.py

clean:
	$(BIN)/python scripts/clean.py

explore:
	$(BIN)/python scripts/explore.py

features:
	$(BIN)/python scripts/build_features.py

train:
	$(BIN)/python scripts/train_models.py

tune:
	$(BIN)/python scripts/tune_models.py

retrain:
	$(BIN)/python scripts/train_models.py --use-tuned --experiment final

analyze:
	$(BIN)/python scripts/analyze_results.py

api:
	PYTHONPATH="$(CURDIR)/.pip_pkgs:$$PYTHONPATH" $(BIN)/uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Full final pipeline: data -> experiments -> tune -> best model -> analysis
all: download clean explore features train tune retrain analyze

test:
	PYTHONPATH="$(CURDIR)/.pip_pkgs:$$PYTHONPATH" $(BIN)/pytest -q

dry-run:
	$(BIN)/python -c "import yaml; from pathlib import Path; p=Path('config.yaml'); c=yaml.safe_load(p.read_text()); c['dataset']['max_chunks']=2; p.write_text(yaml.dump(c, default_flow_style=False, sort_keys=False))"
	$(BIN)/python scripts/clean.py
