import os

from .element import Element
from .function import Function

_SUCCESS, _FAIL, _ERROR, _INTERRUPT, _SKIP, _NOT_RUN = ['SUCCESS', 'FAIL', 'ERROR', 'INTERRUPT', 'SKIP', 'NOT_RUN']

class Test(Function, Element):

    cls = None

    def __init__(self, suite, file):
        super(Test, self).__init__(suite)
        self.file = file
        self._expected_result = _SUCCESS
        self._selected = True
        self.when_run = WhenRunHelper(self)
        self._repetitions = 1
        self.excluded_param_values = frozenset()

    def exclude_param_value(self, param_name, param_value):
        self.excluded_param_values |= {(param_name, param_value)}

    def get_full_address(self, root_path):
        filepath = os.path.join(root_path, self.file.name)
        name = self.name
        if self.cls is not None:
            name = '{.name}.{}'.format(self.cls, name) # pylint: disable=missing-format-attribute
        return '{}:{}'.format(filepath, name)

    def repeat(self, num_repetitions):
        self.add_decorator('slash.repeat({0})'.format(num_repetitions))
        self.expect_repetition(num_repetitions)

    def expect_repetition(self, num_repetitions):
        self._repetitions *= num_repetitions

    def get_num_expected_repetitions(self):
        return self._repetitions

    def add_cleanup(self, **kw):
        return self.add_deferred_event('slash.add_cleanup', name='test_cleanup', **kw)

    def expect_failure(self):
        self._expect(_FAIL)

    def expect_error(self):
        self._expect(_ERROR)

    def expect_interruption(self):
        self._expect(_INTERRUPT)

    def expect_skip(self):
        self._expect(_SKIP)

    def expect_not_run(self):
        self._expect(_NOT_RUN)

    def expect_deselect(self):
        self._selected = False

    def is_selected(self):
        return self._selected

    def _expect(self, expected_result):
        if self._expected_result != _SUCCESS:
            raise NotImplementedError() # pragma: no cover
        self._expected_result = expected_result

    def get_expected_result(self):
        return self._expected_result

    def is_method_test(self):
        raise NotImplementedError() # pragma: no cover

    def is_function_test(self):
        raise NotImplementedError() # pragma: no cover

    def _write_prologue(self, code_formatter):
        self._write_event(code_formatter, 'test_start')
        super(Test, self)._write_prologue(code_formatter)

    def _write_epilogue(self, code_formatter):
        self._write_event(code_formatter, 'test_end')
        super(Test, self)._write_epilogue(code_formatter)

    def _get_function_name(self):
        return 'test_{0}'.format(self.id)


class WhenRunHelper(object):

    def __init__(self, test):
        super(WhenRunHelper, self).__init__()
        self.test = test

    def raise_exception(self):
        self.test.append_line('raise Exception("Test exception")')
        self.test.expect_error()

    error = raise_exception

    def fail(self):
        self.test.append_line('assert False')
        self.test.expect_failure()

    def interrupt(self):
        self.test.append_line('raise KeyboardInterrupt()')
        self.test.expect_interruption()

    def skip(self, with_reason=True, decorator=False):
        if decorator:
            if with_reason:
                self.test.add_decorator('slash.skipped("reason")')
            else:
                self.test.add_decorator('slash.skipped')
        else:
            if with_reason:
                self.test.append_line('slash.skip_test("reason")')
            else:
                self.test.append_line('slash.skip_test()')
        self.test.expect_skip()
