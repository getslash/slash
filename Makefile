all: travis-test

travis-test:
	epylint setup.py
	epylint shakedown
	nosetests -w tests
