default: test

test: env
	.venv/bin/pytest --cov=slash --cov-report=html tests

pylint: env
	.venv/bin/ruff check .

env: .venv/.up-to-date

.venv/.up-to-date: Makefile pyproject.toml
	python -m venv .venv
	.venv/bin/pip install -e .[testing,doc]
	touch .venv/.up-to-date

doc: env
	.venv/bin/sphinx-build -a -W -E doc build/sphinx/html

.PHONY: doc
