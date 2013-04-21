from .utils import TestCase
import shakedown
import shakedown.runner
from shakedown.session import Session

class CleanupsTest(TestCase):
    def test_cleanups(self):
        class Test(shakedown.Test):
            def test1(self_):
                self.events.test1()
                shakedown.add_cleanup(self.events.cleanup, "test1 cleanup")
            def test2(self_):
                self.events.test2()
                shakedown.add_cleanup(self.events.cleanup, "test2 cleanup")

        with self.forge.any_order():
            with self.forge.ordered():
                self.events.test1()
                self.events.cleanup("test1 cleanup")
            with self.forge.ordered():
                self.events.test2()
                self.events.cleanup("test2 cleanup")

        self.forge.replay()
        with Session():
            shakedown.runner.run_tests(Test.generate_tests())
    def test_error_cleanups(self):
        class Test(shakedown.Test):
            def test(self_):
                shakedown.add_cleanup(self.events.cleanup, 1)
                shakedown.add_cleanup(self.events.cleanup, 2)
                raise Exception("!!!")
        self.events.cleanup(1).and_raise(FirstException())
        self.events.cleanup(2).and_raise(SecondException())
        self.forge.replay()
        with Session() as session:
            shakedown.runner.run_tests(Test.generate_tests())
        [result] = session.iter_results()
        [err1, err2, err3] = result.get_errors()


class FirstException(Exception):
    pass
class SecondException(Exception):
    pass
class ThirdException(Exception):
    pass
