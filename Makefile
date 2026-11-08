default: test

test: env
	.venv/bin/pytest --cov=slash --cov-report=html tests

ruff: env
	.venv/bin/ruff check .

env: .venv/.up-to-date

.venv/.up-to-date: Makefile pyproject.toml
	uv venv --allow-existing .venv
	uv pip install --python .venv -e ".[testing,doc]"
	touch .venv/.up-to-date

doc: env
	.venv/bin/sphinx-build -a -W -E doc build/sphinx/html

.PHONY: doc
