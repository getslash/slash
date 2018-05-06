import os
import dessert
from emport import import_file
from ..utils.python import check_duplicate_functions

class LocalConfig(object):

    def __init__(self):
        super(LocalConfig, self).__init__()
        self._slashconf_vars_cache = {}
        self._configs = []
        self.duplicate_funcs = set()

    def push_path(self, path):
        self._configs.append(self._build_config(path))

    def pop_path(self):
        self._configs.pop(-1)

    def get_dict(self):
        return self._configs[-1]

    def _build_config(self, path):
        confstack = []
        for dir_path in self._traverse_upwards(path):
            slashconf_vars = self._slashconf_vars_cache.get(dir_path)
            if slashconf_vars is None:
                slashconf_path = os.path.join(dir_path, 'slashconf.py')
                if os.path.isfile(slashconf_path):
                    self.duplicate_funcs |= check_duplicate_functions(slashconf_path)
                    with dessert.rewrite_assertions_context():
                        slashconf_vars = self._slashconf_vars_cache[dir_path] = vars(import_file(slashconf_path))

            if slashconf_vars is not None:
                confstack.append(slashconf_vars)

        returned = {}
        # start loading from the parent so that vars are properly overriden
        for slashconf_vars in reversed(confstack):
            returned.update(slashconf_vars)
        return returned

    def _traverse_upwards(self, path):
        path = os.path.abspath(path)
        if not os.path.exists(path):
            raise RuntimeError("Path doesn't exist: {}".format(path))

        if os.path.isfile(path):
            path = os.path.dirname(path)

        while True:
            yield path
            if os.path.normcase(path) == os.path.normcase(os.path.abspath(os.path.sep)):
                break
            new_path = os.path.dirname(path)
            assert new_path != path
            path = new_path
