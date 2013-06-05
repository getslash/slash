class Metadata(object):
    def __init__(self, test):
        super(Metadata, self).__init__()
        # we don't keep a copy of the test itself. The metadata should be preserved
        # separately, saving memory for very large runs
        self.canonical_name = test.get_canonical_name()
    def __repr__(self):
        return self.canonical_name

def ensure_slash_metadata(test):
    returned = getattr(test, "__slash__", None)
    if returned is None:
        returned = test.__slash__ = Metadata(test)
    return returned
