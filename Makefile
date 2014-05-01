default: test

detox-test:
	detox

test: env
	.env/bin/python scripts/test_and_pylint.py

coverage-test: env
	.env/bin/coverage run .env/bin/py.test tests

env: .env/.up-to-date

.env/.up-to-date: setup.py Makefile
	virtualenv .env
	.env/bin/python scripts/install_test_deps.py
	.env/bin/pip install -e .
	.env/bin/pip install -r ./doc/pip_requirements.txt
	.env/bin/pip install pylint
	touch .env/.up-to-date

doc: env
	.env/bin/python setup.py build_sphinx -a -E

.PHONY: doc

release: test
	python scripts/make_release.py

fixture-dir:
	rm -rf $(dir)
	python scripts/build_test_dir.py $(dir)
