from ...exception_handling import handling_exceptions

class ActiveFixture(object):

    def __init__(self, fixture):
        super(ActiveFixture, self).__init__()
        self.fixture = fixture
        self.id = fixture.info.id
        self.name = fixture.info.name
        self._test_start_callbacks = []
        self._test_end_callbacks = []
        self._cleanups = []

    def test_start(self, callback):
        self._test_start_callbacks.append(callback)

    def test_end(self, callback):
        self._test_end_callbacks.append(callback)

    def call_test_start(self):
        with handling_exceptions():
            for callback in self._test_start_callbacks:
                callback()

    def call_test_end(self):
        with handling_exceptions():
            for callback in self._test_end_callbacks:
                callback()

    def add_cleanup(self, cleanup):
        self._cleanups.append(cleanup)

    def do_cleanups(self):
        while self._cleanups:
            cleanup = self._cleanups.pop()
            cleanup()
