import itertools
import logbook
import sys
import six

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
        for callback in self._callbacks:
            try:
                callback(**kwargs)
            except:
                _logger.warn("Ignoring error occurred while calling {0}", callback, exc_info=sys.exc_info())
                if last_exc_info is None:
                    last_exc_info = sys.exc_info()
        if last_exc_info and not config.root.hooks.swallow_exceptions:
            six.reraise(*last_exc_info) # pylint: disable=W0142
    def register(self, func):
        self._callbacks.append(func)
        return func # useful for decorators
