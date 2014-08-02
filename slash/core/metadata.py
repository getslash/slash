
class Metadata(object):

    def __init__(self, factory, test, address_in_factory=None):
        super(Metadata, self).__init__()
        self.id = None
        self.test = test
        self.file_path = factory.file_path
        self.factory_name = factory.factory_name
        self.address_in_file = self.factory_name
        self.address_in_factory = address_in_factory
        if address_in_factory is not None:
            self.address_in_file += address_in_factory
        self.address = '{0}:{1}'.format(self.file_path, self.address_in_file)

    def __repr__(self):
        return '<{0}>'.format(self.address)


def ensure_test_metadata(test):
    returned = getattr(test, "__slash__", None)
    if returned is None:
        returned = test.__slash__ = Metadata(None, test, '')
    return returned
