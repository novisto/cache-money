default:
	@echo "See usage in Makefile"

.PHONY: sys-deps install format lint tests build
sys-deps:
	pip install -U pre-commit "poetry>=1.1.8,<2" tox tox-docker coveragepy
	pre-commit install

install:
	poetry install

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
	docker run -d -p 63798:6379 --name cache_money_redis redis:6.2.5

redis-stop:
	docker stop cache_money_redis
