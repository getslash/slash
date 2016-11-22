from pyparsing import infixNotation, opAssoc, Word, alphanums


class Include(object):

    def __init__(self, t):
        super(Include, self).__init__()
        self.only_tags = False
        self.pattern = t[0]
        if self.pattern.startswith('tag:'):
            self.only_tags = True
            self.pattern = self.pattern.split(':', 1)[1]

    def matches(self, metadata):
        if isinstance(metadata, str):
            return self.pattern in metadata

        if metadata.tags.matches_pattern(self.pattern):
            return True
        if self.only_tags:
            return False
        return self.pattern in metadata.address

    def __repr__(self):
        return '<{0}{1}>'.format(self.pattern, ' (only tags)' if self.only_tags else '')


class BinaryMatching(object):

    aggregator = None

    def __init__(self, matchers):
        super(BinaryMatching, self).__init__()
        self.matchers = matchers

    @classmethod
    def from_tokens(cls, t):
        return cls(t[0][0::2])


    def matches(self, metadata):
        return self.aggregator(matcher.matches(metadata) for matcher in self.matchers)  # pylint: disable=not-callable


class AndMatching(BinaryMatching):
    aggregator = all


class OrMatching(BinaryMatching):
    aggregator = any


class Exclude(object):

    def __init__(self, t):
        super(Exclude, self).__init__()
        self.matcher = t[0][1]

    def matches(self, metadata):
        return not self.matcher.matches(metadata)


matcher = Word(alphanums + '._,-=:/')
matcher.setParseAction(Include)

boolExpr = infixNotation(matcher, [
    ("not", 1, opAssoc.RIGHT, Exclude),
    ("and", 2, opAssoc.LEFT, AndMatching.from_tokens),
    ("or", 2, opAssoc.LEFT, OrMatching.from_tokens),
])


class Matcher(object):

    def __init__(self, pattern):
        super(Matcher, self).__init__()
        self._matcher = boolExpr.parseString(pattern)[0]

    def __repr__(self):
        return repr(self._matcher)

    def matches(self, metadata):
        return self._matcher.matches(metadata)
