default: test

test: env
	.env/bin/pytest --cov=slash --cov-report=html tests

pylint: env
	.env/bin/pylint -j 4 --rcfile=.pylintrc slash tests doc

env: .env/.up-to-date

.env/.up-to-date: Makefile pyproject.toml
	python -m venv .env
	.env/bin/pip install -e .[testing,doc]
	touch .env/.up-to-date

doc: env
	.env/bin/sphinx-build -a -W -E doc build/sphinx/html

.PHONY: doc
