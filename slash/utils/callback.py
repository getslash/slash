import itertools
import logbook
import sys

from .._compat import reraise
from ..conf import config
from ..utils.debug import launch_debugger

_declaration_index = itertools.count()
_logger = logbook.Logger(__name__)

class Callback(object):
    """
    Implements a hook to which callbacks can be registered
    """
    def __init__(self, arg_names=(), doc=""):
        super(Callback, self).__init__()
        self._arg_names = arg_names
        self._callbacks = []
        self.declaration_index = next(_declaration_index)
        self.doc = doc
    def get_argument_names(self):
        return set(self._arg_names)
    def __call__(self, **kwargs):
        last_exc_info = None
        uncalled = [callback for (_, callback) in self._callbacks]
        while len(uncalled) > 0:
            found_fulfilled_callback = False
            remaining = []
            for callback in uncalled:
                if not hasattr(callback, 'are_requirements_met') or callback.are_requirements_met():
                    found_fulfilled_callback = True
                    exc_info = self._call_callback(callback, kwargs)
                    if last_exc_info is None:
                        last_exc_info = exc_info
                else:
                    remaining.append(callback)
            uncalled = remaining
            if not found_fulfilled_callback:
                raise RequirementsNotMet("Some callback requirements for {} could not be met".format(callback))
        if last_exc_info and not config.root.hooks.swallow_exceptions:
            _logger.debug("Reraising first exception in callback")
            reraise(*last_exc_info) # pylint: disable=W0142
    def _call_callback(self, callback, kwargs):
        exc_info = None
        try:
            callback(**kwargs) # pylint: disable=W0142
        except:
            exc_info = sys.exc_info()
            _logger.warn("Exception occurred while calling {0}", callback, exc_info=exc_info)
            if config.root.debug.enabled and config.root.debug.debug_hooks:
                launch_debugger(exc_info)
        return exc_info
    def register(self, func, identifier=None):
        """
        Registers a function to this callback.

        Optional argument identifier for later removal by :func:`slash.utils.callback.Callback.unregister_by_identifier`.
        """
        self._callbacks.append((identifier, func))
        return func # useful for decorators

    def unregister_by_identifier(self, identifier):
        """
        Unregisters a callback identified by ``identifier``.
        """
        for index, (callback_id, _) in reversed(list(enumerate(self._callbacks))):
            if callback_id == identifier:
                self._callbacks.pop(index)

    def iter_registered(self):
        """
        Yields tuples of (identifier, callback) for each registered callback
        """
        return iter(self._callbacks)

def requires(callback):
    """
    Allows creating a requirement on a hook callback.
    Hook callback order will prefer calling fulfilled callbacks first. Eventually, all callbacks will be called, even those unfulfilled.
    This is useful to attempt ordering callbacks that depend on each other (for example, to resolve plugin activation dependencies)
    """
    def wrapper(f):
        if not hasattr(f, '_requirements'):
            f._requirements = []
        f._requirements.append(callback)
        def are_requirements_met():
            return all(requirement() for requirement in f._requirements)
        f.are_requirements_met = are_requirements_met
        return f
    return wrapper

class RequirementsNotMet(Exception):
    pass
