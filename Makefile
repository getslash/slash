default: test

test: env
	.venv/bin/pytest --cov=slash --cov-report=html tests

pylint: env
	.venv/bin/pylint -j 4 --rcfile=.pylintrc slash tests doc

env:
	uv venv --seed
	uv pip install -e ".[testing,doc]"

doc: env
	.venv/bin/sphinx-build -a -W -E doc build/sphinx/html

.PHONY: doc
