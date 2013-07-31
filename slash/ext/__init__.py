# -*- coding: utf-8 -*-
"""
slash.ext
~~~~~~~~~

Redirect imports from slash.ext.X to slash_X.

This code is an adaptation of flask.ext, copyright 2011 Armin Ronacher, licensed under BSD
"""


def setup():
    from ..exthook import ExtensionImporter
    importer = ExtensionImporter(['slash_%s'], __name__)
    importer.install()

setup()
del setup
