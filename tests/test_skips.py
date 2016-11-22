import pytest
import slash

from .utils import TestCase, run_tests_in_session


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


def test_class_decorator(suite):

    cls = suite.classes[1]

    cls.add_decorator('slash.skipped("reason")')

    for test in cls.tests:
        test.expect_skip()

    results = suite.run()

    for test in cls.tests:
        result = results[test]
        assert 'reason' in result.get_skips()


def test_custom_skip_exception():
    reason = 'blabla'

    class MyCustomSkipException(Exception):

        def __repr__(self):
            return reason
        __str__ = __repr__


    def test_skip():
        slash.register_skip_exception(MyCustomSkipException)
        raise MyCustomSkipException()

    _assert_skips(test_skip, reason=reason)


def _assert_skips(thing, reason=None):
    session = run_tests_in_session(thing)
    for res in session.results:
        assert res.is_skip()
        assert res.get_skips() == [reason]
