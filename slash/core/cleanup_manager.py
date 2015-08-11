from contextlib import contextmanager
import logbook

from sentinels import Sentinel

_logger = logbook.Logger(__name__)

from .. import hooks
from ..ctx import context
from ..exception_handling import handling_exceptions


_LAST_SCOPE = Sentinel('LAST_SCOPE')
_DEDUCE = Sentinel('DEDUCE')



class CleanupManager(object):

    def __init__(self):
        super(CleanupManager, self).__init__()
        self._scope_stack = []
        self._scopes_by_name = {}

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

        critical = kwargs.pop('critical', False)
        success_only = kwargs.pop('success_only', False)
        scope_name = kwargs.pop('scope', None)
        if scope_name is None:
            scope = self._scope_stack[-1]
        else:
            scope = self._scopes_by_name[scope_name][-1]

        new_kwargs = kwargs.pop('kwargs', {}).copy()
        new_args = list(kwargs.pop('args', ()))
        if args or kwargs:
            _logger.warning(
                'Passing *args/**kwargs to slash.add_cleanup is deprecated', frame_correction=+2)
            new_args.extend(args)
            new_kwargs.update(kwargs)

        added = _Cleanup(_func, new_args, new_kwargs, critical=critical, success_only=success_only)
        scope.cleanups.append(added)
        return _func

    @contextmanager
    def scope(self, scope):
        self.push_scope(scope)
        try:
            yield
        finally:
            self.pop_scope(scope)

    @property
    def latest_scope(self):
        return self._scope_stack[-1]

    def push_scope(self, scope_name):
        _logger.debug('CleanupManager: pushing scope {0!r}', scope_name)
        scope = _Scope(scope_name)
        self._scope_stack.append(scope)
        self._scopes_by_name.setdefault(scope_name, []).append(scope)

    def pop_scope(self, scope_name, in_failure=None, in_interruption=None):
        _logger.debug('CleanupManager: popping scope {0!r} (failure: {1}, interrupt: {2})', scope_name, in_failure, in_interruption)
        scope = self._scope_stack[-1]
        assert scope.name == scope_name, 'Attempted to pop scope {0!r}, but current scope is {1!r}'.format(scope_name, scope.name)
        self._scope_stack.pop()
        self._scopes_by_name[scope_name].pop()

        self.call_cleanups(
            scope=scope,
            in_failure=in_failure, in_interruption=in_interruption)

    def call_cleanups(self, scope=_LAST_SCOPE, in_failure=False, in_interruption=False):

        _logger.debug('Calling cleanups of scope {0.name!r} (failure={1}, interrupt={2})', scope, in_failure, in_interruption)

        if scope is _LAST_SCOPE:
            scope = self._scope_stack[-1]
            _logger.debug('Deducing last scope={0.name!r}', scope)

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
                _logger.debug("Calling cleanup: {0}", cleanup)
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
