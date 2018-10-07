import functools

import logbook

from ..exceptions import SlashInternalError
from ..utils.python import call_all_raise_first

_logger = logbook.Logger(__name__)

class ScopeManager(object):

    def __init__(self, session):
        super(ScopeManager, self).__init__()
        self._session = session
        self._scopes = []
        self._last_module = self._last_test = None

    def begin_test(self, test):
        test_module = test.__slash__.module_name
        if not test_module:
            raise SlashInternalError("{!r} has no module name".format(test))

        if self._last_module is None:
            self._push_scope('session')


        if self._last_module != test_module:
            if self._last_module is not None:
                _logger.trace('Module scope has changed. Popping previous module scope')
                self._pop_scope('module')
            assert self._scopes[-1] != 'module'
            self._push_scope('module')
        self._last_module = test_module
        self._push_scope('test')
        self._last_test = test

    def end_test(self, test):
        if test != self._last_test:
            raise SlashInternalError("Expected to pop {}, received {} instead".format(self._last_test, test))

        self._pop_scope('test')

    def get_current_stack(self):
        return self._scopes[:]

    def has_active_scopes(self):
        return bool(self._scopes)

    def _push_scope(self, scope):
        self._scopes.append(scope)
        _logger.trace('Pushed scope {0}', scope)
        self._session.fixture_store.push_scope(scope)
        self._session.cleanups.push_scope(scope)

    def _pop_scope(self, scope):
        popped = self._scopes.pop()
        _logger.trace('Popping scope {0} (expected {1})', popped, scope)
        if popped != scope:
            raise SlashInternalError('Popped scope {}, expected {}'.format(popped, scope))

        call_all_raise_first([self._session.cleanups.pop_scope, self._session.fixture_store.pop_scope],
                             scope)
        _logger.trace('Popped scope {0}', popped)

    def flush_remaining_scopes(self):
        _logger.trace('Flushing remaining scopes: {}', self._scopes)
        call_all_raise_first([functools.partial(self._pop_scope, s)
                              for s in self._scopes[::-1]])
