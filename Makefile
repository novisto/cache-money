default:
	@echo "See usage in Makefile"

.PHONY: sys-deps install format lint tests build
sys-deps:
	pip install -U \
		"pre-commit>=2.15,<3" \
		"poetry>=1.2,<2" \
		"tox>=3.24,<4" \
		"tox-docker>=3.1,<4" \
		"coverage>=5.5,<6"
	pre-commit install

install:
	poetry install

LINT_TARGETS = cache_money/ tests/
format:
	poetry run autoflake --in-place --remove-all-unused-imports -r $(LINT_TARGETS)
	poetry run isort $(LINT_TARGETS)
	poetry run black $(LINT_TARGETS)

lint:
	poetry run flake8 $(LINT_TARGETS)

tests:
	poetry run pytest --cov cache_money/

redis-start:
	docker run -d --rm -p 63798:6379 --name cache_money_redis --pull always redis:7

redis-stop:
	docker stop cache_money_redis
