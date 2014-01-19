default: test

detox-test:
	detox

test: env
	.env/bin/python scripts/test_and_pylint.py

coverage-test: env
	.env/bin/coverage run .env/bin/nosetests -w tests

env: .env/.up-to-date

.env/.up-to-date: setup.py Makefile
	virtualenv .env
	.env/bin/python scripts/install_test_deps.py
	.env/bin/pip install -e .
	.env/bin/pip install Sphinx==1.1.3 releases
	.env/bin/pip install pylint
	touch .env/.up-to-date

doc: env
	.env/bin/python setup.py build_sphinx

.PHONY: doc

release: test
	python scripts/make_release.py
