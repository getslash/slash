import functools
from ...exception_handling import handling_exceptions
from ...ctx import context as slash_context


class ActiveFixture(object):

    def __init__(self, fixture):
        super(ActiveFixture, self).__init__()
        self.fixture = fixture
        self.id = fixture.info.id
        self.name = fixture.info.name
        self._test_start_callbacks = []
        self._test_end_callbacks = []
        self._cleanups = []
        self._test_start_called = False

    def test_start(self, callback):
        self._test_start_callbacks.append(callback)

    def test_end(self, callback):
        self._test_end_callbacks.append(callback)

    def call_test_start(self):
        if self._test_start_called:
            return

        self._test_start_called = True
        with handling_exceptions():
            for callback in self._test_start_callbacks:
                callback()

    def call_test_end(self):
        self._test_start_called = False
        with handling_exceptions():
            for callback in self._test_end_callbacks:
                callback()

    def add_cleanup(self, cleanup=None, success_only_cleanup=False):
        if cleanup is None:
            return functools.partial(self.add_cleanup, success_only_cleanup=success_only_cleanup)

        self._cleanups.append((cleanup, success_only_cleanup))

    def do_cleanups(self):
        if not slash_context.result:
            # for when we're unit-testing, and there's not 'result'
            success = True
        else:
            success = slash_context.result.is_success()
        while self._cleanups:
            cleanup, success_only_cleanup = self._cleanups.pop()
            if not success_only_cleanup or success:
                cleanup()
