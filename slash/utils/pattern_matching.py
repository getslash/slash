from pyparsing import infixNotation, opAssoc, Word, alphanums


class Include(object):

    def __init__(self, t):
        super(Include, self).__init__()
        self.pattern = t[0]

    def matches(self, s):
        return self.pattern in s


class BinaryMatching(object):

    aggregator = None

    def __init__(self, t):
        super(BinaryMatching, self).__init__()
        self.matchers = t[0][0::2]

    def matches(self, s):
        return self.aggregator(matcher.matches(s) for matcher in self.matchers)  # pylint: disable=not-callable


class AndMatching(BinaryMatching):
    aggregator = all


class OrMatching(BinaryMatching):
    aggregator = any


class Exclude(object):

    def __init__(self, t):
        super(Exclude, self).__init__()
        self.matcher = t[0][1]

    def matches(self, s):
        return not self.matcher.matches(s)


matcher = Word(alphanums + '._,-=')
matcher.setParseAction(Include)

boolExpr = infixNotation(matcher, [
    ("not", 1, opAssoc.RIGHT, Exclude),
    ("and", 2, opAssoc.LEFT, AndMatching),
    ("or", 2, opAssoc.LEFT, OrMatching),
])


class Matcher(object):

    def __init__(self, pattern):
        super(Matcher, self).__init__()
        self._pattern = pattern
        self._matcher = boolExpr.parseString(pattern)[0]

    def __repr__(self):
        return repr(self._pattern)

    def matches(self, s):
        if self._pattern in s:
            return True
        return self._matcher.matches(s)
