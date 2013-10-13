import collections
from contextlib import contextmanager
import functools
import logbook

from .cleanups import add_cleanup
from ._compat import xrange
from .ctx import internal_globals

_logger = logbook.Logger(__name__)

class TestContext(object):
    """
    Represents a context in which test cases are run
    """

    def before(self):
        """Called when the context kicks into effect"""
        pass

    def after(self):
        """Called when the context is discarded when no longer needed"""
        pass

    def before_case(self):
        """Called before each test case is run in this context"""
        pass

    def after_case(self):
        """
        Called after each test case is run in this context
        (regardless of success/failure status)
        """
        pass

def _add_context_to_class(context, cls):
    if cls.__slash_needed_contexts__ is None:
        cls.__slash_needed_contexts__ = collections.deque()
    # we call appendleft because class decorators are executed bottom-up
    # this will cause iteration to happen in the right order
    cls.__slash_needed_contexts__.appendleft(context)
    return cls

def with_context(ctx):
    return functools.partial(_add_context_to_class, ctx)

@contextmanager
def get_test_context_setup(current_test, next_test):
    """
    Given a set of test contexts, sets up all uninitialized test contexts before entry.

    After the context is departed, each context not needed anymore is torn down.
    """
    needed_contexts = _get_needed_contexts(current_test)
    next_needed_contexts = _get_needed_contexts(next_test)
    currently_active = _get_currently_active_contexts()
    for needed_context in needed_contexts:
        currently_active.push(needed_context)
    currently_active.trigger_before_case()
    # NB order is reversed in cleanups, so we need to make sure the `after_case` is triggered before the needed context
    # is popped
    add_cleanup(currently_active.pop_all_except, next_needed_contexts)
    add_cleanup(currently_active.trigger_after_case)
    yield

def _get_needed_contexts(test):
    needed = getattr(getattr(getattr(test, "__slash__", None), "factory", None), "__slash_needed_contexts__", None)
    if needed is None:
        needed = ()
    return needed

def _get_currently_active_contexts():
    returned = getattr(internal_globals, "active_test_contexts", None)
    if returned is None:
        returned = internal_globals.active_test_contexts = ActiveContexts()
    return returned

class ActiveContexts(object):
    def __init__(self):
        super(ActiveContexts, self).__init__()
        self.stack = []
        self.by_type = {}
    def push(self, context_type):
        if context_type in self.by_type:
            return
        ctx = context_type()
        ctx.before()
        self.by_type[context_type] = ctx
        self.stack.append(ctx)

    def pop_all_except(self, needed_context_types):
        needed_context_types = set(needed_context_types)
        for index in xrange(len(self.stack)-1, -1, -1):
            ctx = self.stack[index]
            if type(ctx) not in needed_context_types:
                _logger.debug("{0} no longer needed. Discarding...", ctx)
                self.stack.pop(index)
                self.by_type.pop(type(ctx))
                ctx.after()

    def trigger_before_case(self):
        for ctx in self.stack:
            ctx.before_case()
    def trigger_after_case(self):
        for ctx in reversed(self.stack):
            ctx.after_case()
