
class Metadata(object):

    def __init__(self, factory, test, file_path, factory_name, address_in_factory=None):
        super(Metadata, self).__init__()
        self.id = None
        self.factory = factory
        self.test = test
        self.file_path = file_path
        self.factory_name = factory_name
        self.address_in_file = self.factory_name
        self.address_in_factory = address_in_factory
        if address_in_factory is not None:
            self.address_in_file += address_in_factory
        self.address = '{0}:{1}'.format(file_path, self.address_in_file)

    def __repr__(self):
        return '<{0}>'.format(self.address)


def ensure_test_metadata(test):
    returned = getattr(test, "__slash__", None)
    if returned is None:
        returned = test.__slash__ = Metadata(None, test, '', '')
    return returned
