SHELL := /bin/bash
.DEFAULT_GOAL := help
PYTHON ?= python3
VENV ?= .venv

.PHONY: help install run serve test
help:
	@echo 'make run      — установить зависимости и запустить только свой сервис'
	@echo 'make test     — тесты без сети и PostgreSQL'

$(VENV)/bin/python:
	$(PYTHON) -m venv $(VENV)

$(VENV)/.dependencies: requirements.txt | $(VENV)/bin/python
	$(VENV)/bin/python -m pip install -r requirements.txt
	@touch $@

install: $(VENV)/.dependencies

run: serve

serve: install
	$(VENV)/bin/python run.py

test: install
	$(VENV)/bin/python -m unittest discover -s tests -v
