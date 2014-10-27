
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
        #: Back reference to the test to which this metadata placeholder belongs
        self.test = test
        #: The path to the file from which this test was loaded
        self.file_path = factory.file_path
        self.module_name = factory.module_name
        self.factory_name = factory.factory_name
        #: Address string to identify the test inside the file from which it was loaded
        self.address_in_file = self.factory_name
        self.address_in_factory = address_in_factory
        if address_in_factory is not None:
            self.address_in_file += address_in_factory
        #: String identifying the test, to be used when logging or displaying results in the console
        #: generally it is composed of the file path and the address inside the file
        self.address = '{0}:{1}'.format(self.file_path, self.address_in_file)

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
