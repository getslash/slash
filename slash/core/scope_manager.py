import functools

import logbook

from ..ctx import context
from ..utils.python import call_all_raise_first
from ..exceptions import SkipTest, INTERRUPTION_EXCEPTIONS

_logger = logbook.Logger(__name__)

class ScopeManager(object):

    def __init__(self, session):
        super(ScopeManager, self).__init__()
        self._session = session
        self._scopes = []
        self._last_module = self._last_test = None

    def begin_test(self, test):
        test_module = test.__slash__.module_name
        assert test_module

        if self._last_module is None:
            self._push_scope('session')


        if self._last_module != test_module:
            if self._last_module is not None:
                _logger.debug('Module scope has changed. Popping previous module scope')
                self._pop_scope('module', in_failure=False, in_interruption=False)
            assert self._scopes[-1] != 'module'
            self._push_scope('module')
        self._last_module = test_module
        self._push_scope('test')
        self._last_test = test

    def end_test(self, test, next_test, exc_info):
        assert test == self._last_test

        exc_type = exc_info[0]
        in_failure = exc_type is not None and not issubclass(exc_type, SkipTest)
        if context.result is not None:
            in_failure = in_failure or context.result.is_error() or context.result.is_failure()
        kw = {'in_failure': in_failure, 'in_interruption': exc_type in INTERRUPTION_EXCEPTIONS}

        self._pop_scope('test', **kw)

        if next_test is None:
            _logger.debug('No next test. Popping scopes')
            self._pop_scope('module', **kw)
            self._pop_scope('session', **kw)

    def get_current_stack(self):
        return self._scopes[:]

    def _push_scope(self, scope):
        self._scopes.append(scope)
        _logger.debug('Pushed scope {0}', scope)
        self._session.fixture_store.push_scope(scope)
        self._session.cleanups.push_scope(scope)

    def _pop_scope(self, scope, **kw):
        popped = self._scopes.pop()
        _logger.debug('Popped scope {0} (expected {1})', popped, scope)
        assert popped == scope
        call_all_raise_first([self._session.cleanups.pop_scope, self._session.fixture_store.pop_scope],
                             scope, **kw)

    def flush_remaining_scopes(self, **kw):
        call_all_raise_first([functools.partial(self._pop_scope, s)
                              for s in self._scopes[::-1]], **kw)
