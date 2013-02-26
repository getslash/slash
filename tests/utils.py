from shakedown import RunnableTest
from shakedown.exceptions import TestFailed
import six
import platform
import itertools
import uuid

if platform.python_version() < "2.7":
    from unittest2 import TestCase
else:
    from unittest import TestCase

class TestBucket(object):
    """
    Utility class for allocating runnable tests, remembering them, and asserting all of them
    have run
    """
    __test__ = False # for nose

    def __init__(self):
        super(TestBucket, self).__init__()
        self._expected = set()
        self._uuid_base = str(uuid.uuid1())
        self._uuid_generator = ("{0}/{1}".format(self._uuid_base, i) for i in itertools.count(1))
        self._run_callbacks = {}
    def generate_tests(self, num_tests=3):
        return [self.generate_test() for _ in six.moves.xrange(num_tests)]
    def generate_test(self):
        test_id = next(self._uuid_generator)
        self._expected.add(test_id)
        return BucketTest(self, test_id)
    def notify_run(self, test):
        self._expected.remove(test.__bucket_testid__)
        callback_list = self._run_callbacks.get(test.__bucket_testid__, [])
        while callback_list:
            callback_list.pop(0)(test)
    def assert_all_run(self):
        assert not self._expected, "These tests have not run: {0}".format(", ".join(self._expected))
    ### Functions to manage test execution
    def make_test_raise_exception(self, test):
        self.add_test_run_callback(test, self.do_raise_exception)
    def make_test_fail(self, test):
        self.add_test_run_callback(test, self.do_fail)
    def add_test_run_callback(self, test, handler):
        self._run_callbacks.setdefault(test.__bucket_testid__, []).append(handler)
    ### handlers
    def do_raise_exception(self, _):
        raise OSError("Sample exception")
    def do_fail(self, _):
        raise TestFailed("Test failed")

class BucketTest(RunnableTest):
    def __init__(self, bucket, bucket_test_id):
        super(BucketTest, self).__init__()
        self._bucket = bucket
        self.__bucket_testid__ = bucket_test_id
    def run(self):
        self._bucket.notify_run(self)
