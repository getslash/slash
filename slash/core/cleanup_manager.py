from contextlib import contextmanager

import logbook
from sentinels import Sentinel
from vintage import warn_deprecation

from .. import hooks
from ..ctx import context
from ..exception_handling import handling_exceptions
from ..exceptions import CannotAddCleanup, IncorrectScope

_logger = logbook.Logger(__name__)



_LAST_SCOPE = Sentinel('LAST_SCOPE')
_DEDUCE = Sentinel('DEDUCE')



class CleanupManager(object):

    def __init__(self):
        super(CleanupManager, self).__init__()
        self._scope_stack = []
        self._scopes_by_name = {}
        self._pending = []
        self._allow_implicit_scopes = True
        self._default_scope = None

    @contextmanager
    def forbid_implicit_scoping_context(self):
        prev = self._allow_implicit_scopes
        self._allow_implicit_scopes = False
        try:
            yield
        finally:
            self._allow_implicit_scopes = prev

    def add_cleanup(self, _func, *args, **kwargs):
        """
        Adds a cleanup function to the cleanup stack. Cleanups are executed in a LIFO order.

        Positional arguments and keywords are passed to the cleanup function when called.

        :param critical: If True, this cleanup will take place even when tests are interrupted by the user (Using Ctrl+C for instance)
        :param success_only: If True, execute this cleanup only if no errors are encountered
        :param scope: Scope at the end of which this cleanup will be executed
        :param args: positional arguments to pass to the cleanup function
        :param kwargs: keyword arguments to pass to the cleanup function
        """

        scope_name = kwargs.pop('scope', self._default_scope)

        critical = kwargs.pop('critical', False)
        success_only = kwargs.pop('success_only', False)

        new_kwargs = kwargs.pop('kwargs', {}).copy()
        new_args = list(kwargs.pop('args', ()))
        if args or kwargs:
            warn_deprecation('Passing *args/**kwargs to slash.add_cleanup is deprecated. '
                             'Use args=(...) and/or kwargs={...} instead', frame_correction=+2)
            new_args.extend(args)
            new_kwargs.update(kwargs)

        added = _Cleanup(_func, new_args, new_kwargs, critical=critical, success_only=success_only)


        if scope_name is None:
            if not self._allow_implicit_scopes:
                raise CannotAddCleanup('Cleanup added at a stage requiring explicit scoping')
            scope = self._scope_stack[-1] if self._scope_stack else None
        else:
            if scope_name not in self._scopes_by_name:
                raise IncorrectScope('Incorrect scope specified: {!r}'.format(scope_name))
            scope = self._scopes_by_name[scope_name][-1]

        if scope is None:
            self._pending.append(added)
        else:
            scope.cleanups.append(added)
        return _func

    @contextmanager
    def scope(self, scope):
        self.push_scope(scope)
        try:
            yield
        finally:
            self.pop_scope(scope)

    @contextmanager
    def default_scope_override(self, scope):
        prev = self._default_scope
        self._default_scope = scope
        try:
            yield
        finally:
            self._default_scope = prev

    @property
    def latest_scope(self):
        return self._scope_stack[-1]

    def push_scope(self, scope_name):
        _logger.trace('CleanupManager: pushing scope {0!r}', scope_name)
        scope = _Scope(scope_name)
        self._scope_stack.append(scope)
        self._scopes_by_name.setdefault(scope_name, []).append(scope)
        for p in self._pending:
            scope.cleanups.append(p)
        del self._pending[:]

    def pop_scope(self, scope_name):
        if context.result is None:
            in_failure = in_interruption = False
        else:
            in_failure = not context.result.is_success(allow_skips=True)
            in_interruption = context.result.is_interrupted()

        _logger.trace('CleanupManager: popping scope {0!r} (failure: {1}, interrupt: {2})', scope_name, in_failure, in_interruption)
        scope = self._scope_stack[-1]
        assert scope.name == scope_name, 'Attempted to pop scope {0!r}, but current scope is {1!r}'.format(scope_name, scope.name)
        try:
            self.call_cleanups(
                scope=scope,
                in_failure=in_failure, in_interruption=in_interruption)

        finally:
            self._scope_stack.pop()
            self._scopes_by_name[scope_name].pop()

    def call_cleanups(self, scope=_LAST_SCOPE, in_failure=False, in_interruption=False):

        _logger.trace('Calling cleanups of scope {0.name!r} (failure={1}, interrupt={2})', scope, in_failure, in_interruption)

        if scope is _LAST_SCOPE:
            scope = self._scope_stack[-1]
            _logger.trace('Deducing last scope={0.name!r}', scope)

        if scope.name == 'test': # pylint: disable=no-member
            with handling_exceptions():
                hooks.before_test_cleanups()  # pylint: disable=no-member

        stack = scope.cleanups # pylint: disable=no-member
        while stack:
            cleanup = stack.pop()
            if in_interruption and not cleanup.critical:
                continue
            if (in_failure or in_interruption) and cleanup.success_only:
                continue
            with handling_exceptions(swallow=True):
                _logger.trace("Calling cleanup: {0}", cleanup)
                cleanup()



class _Cleanup(object):

    def __init__(self, func, args, kwargs, critical=False, success_only=False):
        assert not (success_only and critical)
        super(_Cleanup, self).__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.critical = critical
        self.success_only = success_only
        self.result = context.result

    def __call__(self):
        try:
            return self.func(*self.args, **self.kwargs)
        except Exception:
            self.result.add_exception()
            raise

    def __repr__(self):
        return "{0} ({1},{2})".format(self.func, self.args, self.kwargs)


class _Scope(object):

    def __init__(self, name):
        super(_Scope, self).__init__()
        self.name = name
        self.cleanups = []
