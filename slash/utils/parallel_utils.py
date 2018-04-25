from ..conf import config

def is_parallel_session():
    return config.root.parallel.num_workers != 0


def is_parent_session():
    return is_parallel_session() and config.root.parallel.worker_id is None


def is_child_session():
    return config.root.parallel.worker_id is not None


class ParallelPluginModes(object):
    DISABLED = 'disabled'
    ENABLED = 'enabled'
    PARENT_ONLY = 'parent-only'
    CHILD_ONLY = 'child-only'

parallel_mark_values = [ParallelPluginModes.DISABLED, ParallelPluginModes.ENABLED, ParallelPluginModes.PARENT_ONLY, ParallelPluginModes.CHILD_ONLY]
