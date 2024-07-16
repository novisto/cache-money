default:
	@echo "See usage in Makefile"

.PHONY: sys-deps install format lint tests
sys-deps:
	pip install -U \
		"pre-commit<4" \
		"poetry<2" \
		"tox<5" \
		"tox-docker<6"
	pre-commit install

install:
	poetry install

format:
	poetry run ruff check --fix .
	poetry run ruff format .

lint:
	poetry run ruff check .
	poetry run ruff format --check .

tests:
	poetry run pytest --cov cache_money/

redis-start:
	docker run -d --rm -p 6379:6379 --name cache_money_redis --pull always redis:7

redis-stop:
	docker stop cache_money_redis
