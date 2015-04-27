Slash
=====


|                       |                                                                                    |
|-----------------------|------------------------------------------------------------------------------------|
| Build Status          | ![Build Status] (https://secure.travis-ci.org/slash-testing/slash.png?branch=master,dev) |
| Supported Versions    | ![Supported Versions] (https://pypip.in/py_versions/slash/badge.png?style=flat)    |
| Downloads             | ![Downloads] (https://pypip.in/d/slash/badge.png?style=flat)                       |
| Latest Version        | ![Latest Version] (https://pypip.in/v/slash/badge.png?style=flat)                  |
| Test Coverage         | ![Coverage] (https://coveralls.io/repos/slash-testing/slash/badge.png?branch=dev)        |


Slash is a testing framework written in Python for testing complex projects. 

* [Homepage](http://vmalloc.github.io/slash)

* [Documentation](https://slash.readthedocs.org/en/latest/)

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
