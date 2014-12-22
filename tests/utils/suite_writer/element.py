import itertools

_id_allocator = itertools.count()


class Element(object):

    def __init__(self, suite):
        super(Element, self).__init__()
        self.suite = suite
        self.id = '{0:05}'.format(next(_id_allocator))

    def __repr__(self):
        return '<{0} {1}>'.format(type(self).__name__, self.id)
