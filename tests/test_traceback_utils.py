import sys

import emport

from slash.core.error import Error


def test_traceback_line_numbers(tmpdir):
    filename = tmpdir.join('filename.py')

    with filename.open('w') as f:
        f.write('''from contextlib import contextmanager
def f():
    with context():
        a = 1
        b = 2
        g()
        c = 3
        d = 4

def g():
    1/0

@contextmanager
def context():
    yield
''')

    mod = emport.import_file(str(filename))
    try:
        mod.f()
    except ZeroDivisionError:
        err = Error(exc_info=sys.exc_info())
    else:
        assert False, 'did not fail'

    assert err.traceback.frames[-2].lineno == 6


def test_is_test_code(suite, suite_test):
    suite_test.when_run.error()
    summary = suite.run()
    [result] = summary.get_all_results_for_test(suite_test)
    [err] = result.get_errors()
    assert err.traceback.frames[-1].is_in_test_code()

    error_json = err.traceback.to_list()
    assert error_json[-1]['is_in_test_code']


def test_self_attribute_throws():

    class CustomException(Exception):
        pass

    def func():
        x = DangerousObject()
        x.method()

    class DangerousObject(object):

        def __getattribute__(self, attr):
            if attr == '__dict__':
                1/0
            return super(DangerousObject, self).__getattribute__(attr)

        def method(self):
            raise CustomException()

    try:
        func()
    except CustomException:
        error = Error(exc_info=sys.exc_info())
    else:
        assert False, 'Did not raise'

    locals = error.traceback.frames[-1].locals
    assert 'self' in locals
    for key in locals:
        assert 'self.' not in key
