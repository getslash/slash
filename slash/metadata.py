import os
import sys

class Metadata(object):

    def __init__(self, test, factory=None, factory_index=0):
        super(Metadata, self).__init__()
        self.id = None
        self.factory = factory
        self.factory_index = factory_index

        self.fqdn = TestFQDN(test, factory=factory, factory_index=factory_index)

    def __repr__(self):
        return repr(self.fqdn)

class TestFQDN(object):

    def __init__(self, test, factory=None, factory_index=0):
        super(TestFQDN, self).__init__()

        factory_class = factory if factory is not None else type(test)

        self._factory_name = factory_class.__name__
        self.set_path(sys.modules[factory_class.__module__].__file__)
        self._address_in_factory = test.get_address_in_factory()
        if self._address_in_factory is None:
            self._address_in_factory = ".{0}".format(factory_index)

    def set_path(self, path):
        if path.endswith(".pyc"):
            non_pyc = path[:-1]
            if os.path.isfile(non_pyc):
                path = non_pyc
        self._abspath = os.path.abspath(path)
        self._path = os.path.relpath(self._abspath, ".")
        if self._path.startswith(".."):
            self._path = self._abspath

    def get_abspath(self):
        return self._abspath

    def get_path(self):
        return self._path

    def get_factory_name(self):
        return self._factory_name

    def __repr__(self):
        return "{0}:{1}{2}".format(self._path, self._factory_name, self._address_in_factory)

def ensure_test_metadata(test):
    returned = getattr(test, "__slash__", None)
    if returned is None:
        returned = test.__slash__ = Metadata(test)
    return returned
