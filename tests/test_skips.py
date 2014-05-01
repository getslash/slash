import pytest
import slash

from .utils import TestCase


@pytest.mark.parametrize("args", [(), ("message",)])
def test_skip_test(args):
    "Make sure the skip_test function raises a SkipTest exception"
    with pytest.raises(slash.exceptions.SkipTest) as caught:
        slash.skip_test(*args)
    if args:
        assert caught.value.reason == args[0]


def test_skip_with_before_after_test(checkpoint):
    "Make sure that after() is called for Test even if we skip"
    class MyTest(slash.Test):

        def test(self):
            slash.skip_test("!")

        def after(self):
            checkpoint()

    _assert_skips(MyTest, reason="!")
    assert checkpoint.called


def test_method_without_reason():
    class Test(slash.Test):

        @slash.skipped
        def test(self):
            pass

    _assert_skips(Test)


def test_method_with_reason():

    class Test(slash.Test):

        @slash.skipped("reason")
        def test(self):
            pass
    _assert_skips(Test, "reason")


def test_class_decorator():
    @slash.skipped("reason")
    class Test(slash.Test):

        def test_1(self):
            pass

        def test_2(self):
            pass

    [test_1, test_2] = Test.generate_tests()

    _assert_skips(test_1.run, "reason")
    _assert_skips(test_2.run, "reason")


def _assert_skips(thing, reason=None):
    if isinstance(thing, type) and issubclass(thing, slash.Test):
        [thing] = thing.generate_tests()
        thing = thing.run

    with pytest.raises(slash.exceptions.SkipTest) as caught:
        thing()
    assert caught.value.reason == reason
