from .local import LocalStack
from .local import LocalProxy
import functools

__all__ = ["context", "session", "test", "test_id", "g", "internal_globals"]

class GlobalStorage(object):
    pass

class Context(object):
    session = test = test_id = None
    def __init__(self):
        super(Context, self).__init__()
        self.g = GlobalStorage()
        self.internal_globals = GlobalStorage()

    @property
    def test_filename(self):
        return self._get_fqn_field("abspath")

    @property
    def test_classname(self):
        return self._get_fqn_module_address_field("factory_name")

    @property
    def test_methodname(self):
        return self._get_fqn_module_address_field("method_name")

    def _get_fqn_module_address_field(self, field_name):
        current_test = self.test
        if current_test is None:
            return None
        return getattr(current_test.__slash__.fqn.address_in_module, field_name)

    def _get_fqn_field(self, field_name):
        return getattr(getattr(self.test.__slash__, "fqn", None), field_name, None)

class NullContext(object):
    def __setattr__(self, attr, value):
        raise AttributeError("Cannot set attribute {0!r} on null context".format(attr))
    @property
    def _always_none(self):
        pass
    session = test = test_id = g = internal_globals = \
              test_filename = test_classname = test_methodname = _always_none

_ctx = LocalStack()
_ctx.push(NullContext())
context = _ctx() # proxy

def _lookup_object(name):
    top = _ctx.top
    if top is None:
        raise RuntimeError('Context stack is empty')
    return getattr(top, name)


session = LocalProxy(functools.partial(_lookup_object, "session"))
test    = LocalProxy(functools.partial(_lookup_object, "test"))
test_id    = LocalProxy(functools.partial(_lookup_object, "test_id"))
g = LocalProxy(functools.partial(_lookup_object, "g"))
internal_globals = LocalProxy(functools.partial(_lookup_object, "internal_globals"))

def push_context():
    _ctx.push(Context())
def pop_context():
    if isinstance(_ctx.top, NullContext):
        raise RuntimeError("Attempt to pop root context")
    _ctx.pop()
