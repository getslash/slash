import sys
from .utils.fqn import TestFQN, ModuleTestAddress

class Metadata(object):

    def __init__(self, test, factory=None, factory_index=0):
        super(Metadata, self).__init__()
        self.id = None
        self.factory = factory
        self.factory_index = factory_index

        factory_class = factory if factory is not None else type(test)
        address_in_module = test.get_address_in_module()
        if address_in_module is None:
            # the test does not know how to report itself...
            address_in_module = ModuleTestAddress(factory_name=factory_class.__name__, method_name=factory_index)

        self.fqn = TestFQN(
            path=sys.modules[factory_class.__module__].__file__,
            address_in_module=address_in_module,
            )

    def __repr__(self):
        return repr(self.fqn)

def ensure_test_metadata(test):
    returned = getattr(test, "__slash__", None)
    if returned is None:
        returned = test.__slash__ = Metadata(test)
    return returned
