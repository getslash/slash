from .exceptions import SlashInternalError
from .reporting.null_reporter import NullReporter

__all__ = ["context", "session", "test", "test_id", "g", "internal_globals"]


class GlobalStorage(object):
    pass


class Context(object):
    session = test = test_id = result = fixture = None

    def __init__(self):
        super(Context, self).__init__()
        self.g = GlobalStorage()
        self.internal_globals = GlobalStorage()

    @property
    def test_filename(self):
        return self._get_test_address_field("file_path")

    @property
    def session_id(self):
        s = self.session
        if s is None:
            return None
        return s.id

    @property
    def reporter(self):
        if self.session is None:
            return NullReporter()
        return self.session.reporter

    def _get_test_address_field(self, field_name):
        current_test = self.test
        if current_test is None:
            return None
        return getattr(current_test.__slash__, field_name)


class NullContext(object):

    def __setattr__(self, attr, value):
        raise AttributeError(
            "Cannot set attribute {!r} on null context".format(attr))

    @property
    def _always_none(self):
        pass

    session = test = test_id = g = internal_globals = \
        test_filename = test_classname = test_methodname = result = fixture = _always_none

    reporter = NullReporter()


class _ContextStack(object):

    def __init__(self):
        super(_ContextStack, self).__init__()
        self._stack = [NullContext()]

    def __getattr__(self, attr):
        assert self._stack
        return getattr(self._stack[-1], attr)

    def __dir__(self):
        assert self._stack
        return dir(self._stack[-1])

    def __setattr__(self, attr, value):
        if attr.startswith("_"):
            return super(_ContextStack, self).__setattr__(attr, value)
        setattr(self._stack[-1], attr, value)

    def push(self, ctx):
        self._stack.append(ctx)
        return ctx

    def pop(self):
        if not self._stack:
            raise SlashInternalError('Attempting to pop context with empty stack')

        if len(self._stack) == 1:
            raise RuntimeError("No more contexts to pop")
        return self._stack.pop(-1)

context = _ContextStack()


class ContextAttributeProxy(object):

    def __init__(self, name):
        super(ContextAttributeProxy, self).__init__()
        self._proxy__name = name

    @property
    def _obj(self):
        return getattr(context, self._proxy__name)

    def __getattr__(self, attr):
        return getattr(self._obj, attr)

    def __setattr__(self, attr, value):
        if attr == "_proxy__name":
            return super(ContextAttributeProxy, self).__setattr__(attr, value)
        setattr(self._obj, attr, value)

    def __eq__(self, other):
        return self._obj == other

    def __ne__(self, other):
        return self._obj != other

    def __call__(self, *args, **kwargs):
        return self._obj(*args, **kwargs)  # pylint: disable=not-callable

    def __repr__(self):
        return repr(self._obj)

    def __dir__(self):
        return dir(self._obj)

    __members__ = __dir__

    def __str__(self):
        return str(self._obj)


session = ContextAttributeProxy("session")
test = ContextAttributeProxy("test")
test_id = ContextAttributeProxy("test_id")
g = ContextAttributeProxy("g")
internal_globals = ContextAttributeProxy("internal_globals")
reporter = ContextAttributeProxy("reporter")


def push_context():
    context.push(Context())

def pop_context():
    context.pop()
