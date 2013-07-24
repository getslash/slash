import itertools
import logbook
import sys

from .._compat import reraise
from ..conf import config

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
        for (_, callback) in self._callbacks:
            try:
                callback(**kwargs)
            except:
                _logger.warn("Ignoring error occurred while calling {0}", callback, exc_info=sys.exc_info())
                if last_exc_info is None:
                    last_exc_info = sys.exc_info()
        if last_exc_info and not config.root.hooks.swallow_exceptions:
            reraise(*last_exc_info) # pylint: disable=W0142
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
