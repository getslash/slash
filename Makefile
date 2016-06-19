default: test

detox-test:
	detox

test: env
	.env/bin/python scripts/test_and_pylint.py

pylint: env
	.env/bin/pylint --rcfile=.pylintrc slash

env: .env/.up-to-date

.env/.up-to-date: setup.py Makefile
	python -m virtualenv .env
	.env/bin/python scripts/install_test_deps.py
	.env/bin/pip install -e .
	.env/bin/pip install -r ./doc/pip_requirements.txt
	touch .env/.up-to-date

doc: env
	.env/bin/python setup.py build_sphinx -a -E

.PHONY: doc

release: test
	python scripts/make_release.py
