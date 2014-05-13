import gossip
import slash
import slash.runner
from slash import exception_handling, Session
from slash.loader import Loader

from .utils import TestCase


class CleanupsTest(TestCase):

    def setUp(self):
        super(CleanupsTest, self).setUp()
        self._successful_tests = []
        self.addCleanup(gossip.unregister_token, "monitor_test_success")
        slash.hooks.test_success.register(self._register_test_success, token="monitor_test_success")

    def _register_test_success(self):
        self._successful_tests.append(slash.context.test)

    def test_cleanups(self):
        class Test(slash.Test):
            def test1(self_):
                self.events.test1()
                slash.add_cleanup(self.events.cleanup, "test1 cleanup 2")
                slash.add_cleanup(self.events.cleanup, "test1 cleanup 1")
            def test2(self_):
                self.events.test2()
                slash.add_cleanup(self.events.cleanup, "test2 cleanup")

        with self.forge.any_order():
            with self.forge.ordered():
                self.events.test1()
                self.events.cleanup("test1 cleanup 1")
                self.events.cleanup("test1 cleanup 2")
            with self.forge.ordered():
                self.events.test2()
                self.events.cleanup("test2 cleanup")

        self.forge.replay()
        with Session():
            slash.runner.run_tests(Loader().get_runnables(Test))

        assert len(self._successful_tests) == 2

    def test_error_cleanups_and_fail_test(self):
        self._test_error_cleanups(fail_test=True)

    def test_error_cleanups_and_not_fail_test(self):
        self._test_error_cleanups(fail_test=False)

    def _test_error_cleanups(self, fail_test):

        exc_infos = []
        new_exc_handlers = list(exception_handling._EXCEPTION_HANDLERS)
        new_exc_handlers.append(exc_infos.append)
        self.forge.replace_with(exception_handling, "_EXCEPTION_HANDLERS", new_exc_handlers)

        class Test(slash.Test):
            def test(self_):
                slash.add_cleanup(self.events.cleanup, 1)
                slash.add_cleanup(self.events.cleanup, 2)
                if fail_test:
                    raise Exception("!!!")
        self.events.cleanup(2).and_raise(SecondException())
        self.events.cleanup(1).and_raise(FirstException())
        self.forge.replay()
        with Session() as session:
            slash.runner.run_tests(Loader().get_runnables(Test))
        self.forge.verify()
        [result] = session.results.iter_test_results()
        errors = result.get_errors()

        assert len(errors) == (3 if fail_test else 2)

        self.assertEquals(len(errors), len(exc_infos))
        self.assertEquals(
            [e[0] for e in exc_infos],
            [Exception, SecondException, FirstException] if fail_test else [SecondException, FirstException],
            )
        self.assertEquals(self._successful_tests, [])

class FirstException(Exception):
    pass
class SecondException(Exception):
    pass
class ThirdException(Exception):
    pass
