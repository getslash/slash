from .local import LocalStack
from .local import LocalProxy
import functools

__all__ = ["context", "session", "suite", "test"]

class Context(object):
    session = suite = test = None

class NullContext(object):
    def __setattr__(self, attr, value):
        raise AttributeError("Cannot set attribute {0!r} on null context".format(attr))
    @property
    def session(self):
        return None
    @property
    def suite(self):
        return None
    @property
    def test(self):
        return None

_ctx = LocalStack()
_ctx.push(NullContext())
context = _ctx() # proxy

def _lookup_object(name):
    top = _ctx.top
    if top is None:
        raise RuntimeError('Context stack is empty')
    return getattr(top, name)


session = LocalProxy(functools.partial(_lookup_object, "session"))
suite   = LocalProxy(functools.partial(_lookup_object, "suite"))
test    = LocalProxy(functools.partial(_lookup_object, "test"))

def push_context():
    _ctx.push(Context())
def pop_context():
    if isinstance(_ctx.top, NullContext):
        raise RuntimeError("Attempt to pop root context")
    _ctx.pop()
