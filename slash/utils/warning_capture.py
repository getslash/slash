import sys


class warning_callback_context(object):

    """A context for installing callbacks for handling warnings.

    Code adopted from the built-in catch_warnings handler
    """

    def __init__(self, callback):
        self._callback = callback
        self._module = sys.modules['warnings']
        self._entered = False

    def __enter__(self):
        if self._entered:
            raise RuntimeError("Cannot enter %r twice" % self)
        self._entered = True
        self._showwarning = self._module.showwarning
        self._module.showwarning = self._callback

    def __exit__(self, *exc_info):
        if not self._entered:
            raise RuntimeError("Cannot exit %r without entering first" % self)
        self._module.showwarning = self._showwarning
