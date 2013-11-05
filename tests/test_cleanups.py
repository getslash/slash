from .utils import TestCase
import slash
import slash.runner
from slash import exception_handling
from slash import Session
from slash.loader import Loader

class CleanupsTest(TestCase):
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
            slash.runner.run_tests(Loader().iter_test_factory(Test))

    def test_error_cleanups(self):

        exc_infos = []
        new_exc_handlers = list(exception_handling._EXCEPTION_HANDLERS)
        new_exc_handlers.append(exc_infos.append)
        self.forge.replace_with(exception_handling, "_EXCEPTION_HANDLERS", new_exc_handlers)

        class Test(slash.Test):
            def test(self_):
                slash.add_cleanup(self.events.cleanup, 1)
                slash.add_cleanup(self.events.cleanup, 2)
                raise Exception("!!!")
        self.events.cleanup(2).and_raise(SecondException())
        self.events.cleanup(1).and_raise(FirstException())
        self.forge.replay()
        with Session() as session:
            slash.runner.run_tests(Loader().iter_test_factory(Test))
        [result] = session.results.iter_test_results()
        [err1, err2, err3] = errors = result.get_errors()

        self.assertEquals(len(errors), len(exc_infos))
        self.assertEquals(
            [e[0] for e in exc_infos],
            [Exception, SecondException, FirstException],
            )

class FirstException(Exception):
    pass
class SecondException(Exception):
    pass
class ThirdException(Exception):
    pass
