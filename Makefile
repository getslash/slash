default: quicktest

detox-test:
	detox

travis-test: env
	.env/bin/python scripts/travis_test.py

quicktest: env
	.env/bin/nosetests -w tests

coverage-test: env
	.env/bin/coverage run .env/bin/nosetests -w tests

env: .env/.up-to-date

.env/.up-to-date: setup.py Makefile
	virtualenv .env
	.env/bin/python scripts/install_test_deps.py
	.env/bin/pip install -e .
	touch .env/.up-to-date

release:
	python scripts/make_release.py
