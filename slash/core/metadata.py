import itertools
import sys

from ..ctx import context

_sort_key_generator = itertools.count()

class Metadata(object):

    """Class representing the metadata associated with a test object. Generally available
    as test.__slash__
    """

    #: The index of the test in the current execution, 0-based
    test_index0 = None

    def __init__(self, factory, test):
        super(Metadata, self).__init__()
        #: The test's unique id
        self.id = None
        self.tags = test.get_tags()
        self._sort_key = next(_sort_key_generator)
        if factory is not None:
            #: The path to the file from which this test was loaded
            self.module_name = factory.get_module_name()
            assert self.module_name, 'Could not find module for {0}'.format(test)
            self.file_path = factory.get_filename()
            self.factory_name = factory.get_factory_name()
        else:
            self.module_name = type(test).__module__
            self.file_path = sys.modules[self.module_name].__file__
            self.factory_name = '?'
        self.variation = test.get_variation()
        assert self.variation is not None

        #: Address string to identify the test inside the file from which it was loaded
        self.address_in_file = self.factory_name
        self.address_in_factory = test.get_address_in_factory()
        if self.address_in_factory is not None:
            self.address_in_file += self.address_in_factory
        #: String identifying the test, to be used when logging or displaying results in the console
        #: generally it is composed of the file path and the address inside the file
        self.address = '{0}:{1}'.format(self.file_path, self.address_in_file)
        if self.variation:
            self.address += '({})'.format(self.variation.safe_repr)
        if factory is not None:
            self._class_name = factory.get_class_name()
        else:
            testfunc = test.get_test_function()
            if hasattr(testfunc, '__self__'):
                self._class_name = testfunc.__self__.__class__.__name__
            else:
                self._class_name = None

        self._interactive = False

    def allocate_id(self):
        assert self.id is None
        self.id = context.session.id_space.allocate()


    def set_sort_key(self, key):
        self._sort_key = key

    def get_sort_key(self):
        return self._sort_key

    def set_test_full_name(self, name):
        assert hasattr(self, 'address')
        self.address = name

    def is_interactive(self):
        return self._interactive

    def mark_interactive(self):
        self._interactive = True
        assert hasattr(self, 'file_path')
        self.file_path = '<Interactive>'
        self.factory_name = self.address = 'Interactive'

    @property
    def class_name(self):
        return self._class_name

    @property
    def function_name(self):
        returned = self.address_in_file
        if self._class_name:
            prefix = self._class_name + '.'
            assert returned.startswith(prefix)
            returned = returned[len(prefix):]

        return returned.split('(')[0]

    @property
    def test_index1(self):
        """Same as ``test_index0``, only 1-based
        """
        if self.test_index0 is None:
            return None
        return self.test_index0 + 1

    def __repr__(self):
        return '<{0}>'.format(self.address)


def ensure_test_metadata(test):
    returned = getattr(test, "__slash__", None)
    if returned is None:
        returned = test.__slash__ = Metadata(None, test)
    return returned
