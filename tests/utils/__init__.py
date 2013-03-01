from logbook.compat import LoggingHandler
import platform

if platform.python_version() < "2.7":
    import unittest2 as unittest
else:
    import unittest

class TestCase(unittest.TestCase):
    def setUp(self):
        super(TestCase, self).setUp()
        self._handler = LoggingHandler()
        self._handler.push_application()
    def tearDown(self):
        self._handler.pop_application()
        super(TestCase, self).tearDown()
