import sys


class Metadata(object):

    """Class representing the metadata associated with a test object. Generally available
    as test.__slash__
    """

    #: The index of the test in the current execution, 0-based
    test_index0 = None

    def __init__(self, factory, test, address_in_factory=None):
        super(Metadata, self).__init__()
        #: The test's unique id
        self.id = None
        self.tags = test.get_tags()
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
        #: Address string to identify the test inside the file from which it was loaded
        self.address_in_file = self.factory_name
        self.address_in_factory = address_in_factory
        if address_in_factory is not None:
            self.address_in_file += address_in_factory
        #: String identifying the test, to be used when logging or displaying results in the console
        #: generally it is composed of the file path and the address inside the file
        self.address = '{0}:{1}'.format(self.file_path, self.address_in_file)

    @property
    def class_name(self):
        if '.' in self.address_in_file:
            return self.address_in_file.split('.', 1)[0]
        return None

    @property
    def function_name(self):
        returned = self.address_in_file
        if '.' in returned:
            returned = returned.rsplit('.', 1)[-1]
        return returned.split('(', 1)[0]

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
        returned = test.__slash__ = Metadata(None, test, '')
    return returned
