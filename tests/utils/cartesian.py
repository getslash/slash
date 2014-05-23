import itertools

from slash._compat import itervalues


class Cartesian(object):

    def __init__(self):
        super(Cartesian, self).__init__()
        self.sets = {}

    def __getattr__(self, attr):
        if attr.startswith("_"):
            raise AttributeError(attr)
        return SetMaker(self, attr)

    def __len__(self):
        if not self.sets:
            return 0

        returned = 1
        for x in itervalues(self.sets):
            returned *= len(x)
        return returned

    def check(self, iterator):
        names = list(self.sets)
        sets = [self.sets[name] for name in names]
        expected = sorted({name: value for name, value in zip(names, combination)} for combination in itertools.product(*sets))
        got = sorted(iterator)
        assert got == expected

class SetMaker(object):

    def __init__(self, cartesian, name):
        super(SetMaker, self).__init__()
        self.cartesian = cartesian
        self.name = name

    def make_set(self, size=3):
        assert self.name not in self.cartesian.sets
        returned = self.cartesian.sets[self.name] = ["{0}{1}".format(self.name, i) for i in range(size)]
        return returned
