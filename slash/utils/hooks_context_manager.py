from .. import hooks

class HooksContextManager(object):
    """
    This class can be used to register and unregister multiple hooks
    within a context. The callbacks are collected by searching methods
    prefixed by "on_<hook name>" (.e.g: on_test_error).
    """
    PREFIX = "on_"
    def __init__(self):
        self._id = object()
    def _get_hooks_and_callbacks(self):
        return [(getattr(hooks, member.replace(self.PREFIX, "")), # the hook
                 getattr(self, member)) # the callback
                for member in dir(self)
                if member.startswith(self.PREFIX)]
    def __enter__(self):
        for hook, callback in self._get_hooks_and_callbacks():
            hook.register(callback, self._id)
        return self
    def __exit__(self, *e):
        for hook, _ in self._get_hooks_and_callbacks():
            hook.unregister_by_identifier(self._id)
