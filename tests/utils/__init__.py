from logbook.compat import LoggingHandler
import platform
import forge
from confetti.utils import (
    assign_path,
    get_path,
    )
from shakedown.conf import config
if platform.python_version() < "2.7":
    import unittest2 as unittest
else:
    import unittest

class TestCase(unittest.TestCase):
    def setUp(self):
        super(TestCase, self).setUp()
        self._handler = LoggingHandler()
        self._handler.push_application()
    def override_config(self, path, value):
        self.addCleanup(assign_path, config, path, get_path(config, path))
        assign_path(config, path, value)
    _forge = None
    @property
    def forge(self):
        if self._forge is None:
            self._forge = forge.Forge()
        return self._forge
    _events = None
    @property
    def events(self):
        if self._events is None:
            self._events = self.forge.create_wildcard_mock()
        return self._events
    def tearDown(self):
        if self._forge is not None:
            self._forge.verify()
        self._handler.pop_application()
        super(TestCase, self).tearDown()
