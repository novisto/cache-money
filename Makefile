default:
	@echo "See usage in Makefile"

.PHONY: sys-deps install run format lint tests build
sys-deps:
	pip install -U pre-commit poetry==1.0.10 tox
	pre-commit install

install:
	poetry install

run:
	poetry run python run.py

LINT_TARGETS = cache_money/ tests/
format:
	poetry run black $(LINT_TARGETS)
	poetry run autoflake --in-place --remove-all-unused-imports -r $(LINT_TARGETS)
	poetry run isort $(LINT_TARGETS)

lint:
	poetry run flake8 $(LINT_TARGETS)

tests:
	poetry run pytest --cov-report term-missing --cov cache_money/ tests/

redis-start:
	docker run -d -p 63798:6379 --name cache_money redis:6.2.5

redis-stop:
	docker stop cache_money
