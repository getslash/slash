default: test

detox-test:
	detox

test: env
	.env/bin/py.test --cov=slash --cov-report=html tests

pylint: env
	.env/bin/pylint -j 4 --rcfile=.pylintrc slash tests setup.py doc

env: .env/.up-to-date

.env/.up-to-date: setup.py Makefile
	python -m virtualenv .env
	.env/bin/pip install -e .[testing,doc]
	touch .env/.up-to-date

doc: env
	.env/bin/sphinx-build -a -E doc build/sphinx/html

.PHONY: doc

release: test
	python scripts/make_release.py
