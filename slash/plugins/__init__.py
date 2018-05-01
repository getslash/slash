from ..utils.marks import mark
from ..utils import parallel_utils
from .interface import PluginInterface # pylint: disable=unused-import



def registers_on(hook_name, **kwargs):
    """Marks the decorated plugin method to register on a custom hook, rather than
    the method name in the 'slash' group, which is the default behavior for plugins

    Specifying ``registers_on(None)`` means that this is not a hook entry point at all.

    .. note:: All keyword arguments are forwarded to gossip's ``register`` API
    """
    return mark("register_on", RegistrationInfo(hook_name, expect_exists=False, register_kwargs=kwargs), append=True)


def parallel_mode(mode):
    """Marks compatibility of a specific plugin to parallel execution.

    :param mode: Can be either ``disabled``, ``enabled``, ``parent-only`` or ``child-only``
    """
    possible_values = parallel_utils.ParallelPluginModes.MODES
    assert mode in possible_values, "parallel mode value must be one of {}".format(possible_values)
    return mark("parallel_mode", mode)


def register_if(condition):
    """Marks the decorated plugins method to only be registered if *condition* is ``True``
    """
    return mark("register_if", condition)


def active(plugin_class):
    """Decorator for automatically installing and activating a plugin upon definition
    """
    plugin = plugin_class()
    manager.install(plugin)
    manager.activate(plugin)

    return plugin_class


def needs(what):
    return mark("plugin_needs", what, append=True)


def provides(what):
    return mark("plugin_provides", what, append=True)


from .plugin_manager import manager, IncompatiblePlugin, UnknownPlugin, IllegalPluginName, RegistrationInfo # pylint: disable=unused-import
