SHELL := /bin/bash
.DEFAULT_GOAL := help
PYTHON ?= python3
VENV ?= .venv
DB_CONTAINER ?= school-orders-postgres
DB_VOLUME ?= school-orders-data
# 5433 не конфликтует с обычным локальным PostgreSQL на 5432.
DB_PORT ?= 5433
DB_BIND_HOST ?= 127.0.0.1
export DB_CONTAINER DB_VOLUME DB_PORT DB_BIND_HOST

.PHONY: help install db-up db-init db-stop db-shell run serve test test-env
help:
	@echo 'make run       — зависимости, PostgreSQL, общая база/таблицы и пять сервисов'
	@echo 'make serve     — только пять сервисов (БД уже готова)'
	@echo 'make db-init   — запуск PostgreSQL и повторяемая инициализация'
	@echo 'make db-shell  — интерактивный SQL со всеми пятью таблицами'
	@echo 'make db-stop   — остановка PostgreSQL с сохранением данных'
	@echo 'make test      — тесты команд и проверки всей цепочки без Docker'

$(VENV)/bin/python:
	$(PYTHON) -m venv $(VENV)

$(VENV)/.dependencies: requirements.txt | $(VENV)/bin/python
	$(VENV)/bin/python -m pip install -r requirements.txt
	@touch $@

install: $(VENV)/.dependencies

db-up:
	bash database/postgres.sh

db-init:
	bash database/setup.sh

# Подключение под ролью приложения: доступны все пять таблиц общей базы.
db-shell: db-init
	docker exec -e PGPASSWORD=1234 -it $(DB_CONTAINER) psql -h 127.0.0.1 -U orders -d orders_db

db-stop:
	docker stop $(DB_CONTAINER)

# Рекурсивный make обеспечивает последовательность даже с make -j.
run:
	$(MAKE) install
	$(MAKE) db-init
	$(MAKE) serve

serve: install
	$(VENV)/bin/python scripts/run_services.py

TEST_PYTHON := $(abspath $(VENV)/bin/python)

test: install
	@for service in demo-orders demo-stock demo-payment demo-delivery demo-notification; do \
		(cd $$service && $(TEST_PYTHON) -m unittest discover -s tests -v) || exit $$?; \
	done
	$(VENV)/bin/python -m unittest discover -s tests -v

# Сохраняем исходную команду для маленького тестового приложения из проекта.
test-env: install
	$(VENV)/bin/python -m uvicorn main:app --app-dir test-environment --reload
