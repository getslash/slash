import sys

import emport
import vintage

from slash.core.error import Error
from slash.utils import traceback_utils
from slash.utils.traceback_utils import _MAX_VARIABLE_VALUE_LENGTH



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


def test_variable_capping():

    def f():
        g()

    def g():
        long_var = 'a' * 1000
        assert len(long_var) > _MAX_VARIABLE_VALUE_LENGTH
        1/0                     # pylint: disable=pointless-statement

    try:
        f()
    except ZeroDivisionError:
        err = Error(exc_info=sys.exc_info())

    distilled = err.traceback.to_list()
    assert len(distilled[-1]['locals']['long_var']['value']) == _MAX_VARIABLE_VALUE_LENGTH




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
                1/0  # pylint: disable=pointless-statement
            return super(DangerousObject, self).__getattribute__(attr)

        def method(self):
            raise CustomException()

    try:
        func()
    except CustomException:
        error = Error(exc_info=sys.exc_info())
    else:
        assert False, 'Did not raise'

    with vintage.get_no_deprecations_context():
        locals_ = error.traceback.frames[-1].locals
    assert 'self' in locals_
    for key in locals_:
        assert 'self.' not in key


class NonReprable(object):
    def __repr__(self):
        raise Exception('Repr error')


def test_safe_repr_for_non_repable_object():
    # pylint: disable=protected-access
    obj = NonReprable()
    returned = traceback_utils._safe_repr(obj, blacklisted_types=())
    assert 'unprintable' in returned.lower()

    returned = traceback_utils._safe_repr(obj, blacklisted_types=(NonReprable,))
    assert 'unprintable' not in returned.lower()


class NonDictable(object):

    def __getattribute__(self, attr):
        if attr == '__dict__':
            raise Exception('dict error')
        return super(NonDictable, self).__getattribute__(attr)

    def method(self):
        1/0 # pylint: disable=pointless-statement


def test_dict_getting_raises_exception():

    def func():
        x = NonDictable()
        x.method()

    try:
        func()
    except ZeroDivisionError:
        error_string = Error(exc_info=sys.exc_info()).traceback.to_string(include_vars=True)
    assert 'self:' in error_string
