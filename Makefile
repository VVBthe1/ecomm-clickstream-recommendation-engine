.PHONY: help venv install download clean explore features train all test dry-run

PYTHON ?= python3
VENV := .venv
BIN := $(VENV)/bin

help:
	@echo "make install   venv + deps"
	@echo "make download  Kaggle -> bronze"
	@echo "make clean     bronze -> silver"
	@echo "make explore   EDA -> metadata/"
	@echo "make features  silver -> gold"
	@echo "make train     gold -> models + metrics"
	@echo "make all       full pipeline"
	@echo "make dry-run   clean (2 chunks)"
	@echo "make test      pytest"

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

all: download clean explore features train

test:
	$(BIN)/pytest -q

dry-run:
	$(BIN)/python -c "import yaml; from pathlib import Path; p=Path('config.yaml'); c=yaml.safe_load(p.read_text()); c['dataset']['max_chunks']=2; p.write_text(yaml.dump(c, default_flow_style=False, sort_keys=False))"
	$(BIN)/python scripts/clean.py
