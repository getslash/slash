Slash
=====


|                       |                                                                                    |
|-----------------------|------------------------------------------------------------------------------------|
| Build Status          | ![Build Status] (https://secure.travis-ci.org/slash-testing/slash.png?branch=master,dev) |
| Supported Versions    | ![Supported Versions] (https://img.shields.io/pypi/pyversions/slash.svg)    |
| Downloads             | ![Downloads] (https://img.shields.io/pypi/dm/slash.svg)                       |
| Latest Version        | ![Latest Version] (https://img.shields.io/pypi/v/slash.svg)                  |
| Test Coverage         | ![Coverage Status] (https://img.shields.io/coveralls/slash-testing/slash/develop.svg)   |




Slash is a testing framework written in Python for testing complex projects. 

* [Homepage](http://slash-testing.github.io/slash/)

* [Documentation](https://slash.readthedocs.org/)

Development
===========

Releasing a Version
-------------------

Run the following from the project's root (requires `git-flow`):

```
$ make release
```

After the script finishes, push the relevant branches

```
$ git push origin master:master develop:develop --tags
```

Upload a release:
```
$ git checkout master
$ python setup.py sdist upload
```
