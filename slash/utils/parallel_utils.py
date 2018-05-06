from ..conf import config

def is_parallel_session():
    return config.root.parallel.num_workers != 0


def is_parent_session():
    return is_parallel_session() and config.root.parallel.worker_id is None


def is_child_session():
    return config.root.parallel.worker_id is not None


class ParallelPluginModes(object):
    DISABLED, ENABLED, PARENT_ONLY, CHILD_ONLY = MODES = (
        'disabled', 'enabled', 'parent-only', 'child-only'
    )
