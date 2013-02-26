from shakedown import RunnableTest
import itertools
import uuid

class TestBucket(object):
    """
    Utility class for allocating runnable tests, remembering them, and asserting all of them
    have run
    """
    def __init__(self):
        super(TestBucket, self).__init__()
        self._expected = set()
        self._uuid_base = str(uuid.uuid1())
        self._uuid_generator = ("{0}/{1}".format(self._uuid_base, i) for i in itertools.count(1))
    def generate_tests(self, num_tests=3):
        return [self.generate_test() for _ in xrange(num_tests)]
    def generate_test(self):
        test_id = next(self._uuid_generator)
        self._expected.add(test_id)
        return BucketTest(self, test_id)
    def notify_run(self, test_id):
        self._expected.pop()
    def assert_all_run(self):
        assert not self._expected, "These tests have not run: {0}".format(", ".join(self._expected))

class BucketTest(RunnableTest):
    def __init__(self, bucket, bucket_test_id):
        super(BucketTest, self).__init__()
        self._bucket = bucket
        self._id = bucket_test_id
    def run(self):
        self._bucket.notify_run(self._id)
