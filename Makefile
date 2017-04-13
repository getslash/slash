default: test

detox-test:
	detox

test: env
	.env/bin/py.test --cov=slash --cov-report=html tests

pylint: env
	.env/bin/pylint --rcfile=.pylintrc slash tests setup.py

env: .env/.up-to-date

.env/.up-to-date: setup.py Makefile
	python -m virtualenv .env
	.env/bin/pip install -e .
	.env/bin/pip install -r ./doc/pip_requirements.txt -r test_requirements.txt
	touch .env/.up-to-date

doc: env
	.env/bin/python setup.py build_sphinx -a -E

.PHONY: doc

release: test
	python scripts/make_release.py
