from slash.utils.pattern_matching import Matcher
from slash.core.tagging import NO_TAGS, Tags


def test_string_patterns(suite, config_override):
    selected_test = suite[len(suite) // 2]

    config_override("run.filter_strings", [selected_test.id])

    for i, test in enumerate(suite):  # pylint: disable=unused-variable
        if test is not selected_test:
            test.expect_deselect()

    suite.run()


def test_string_patterns_and(suite, config_override):
    selected_test = suite[len(suite) // 2]
    other_test = suite[-1]

    config_override("run.filter_strings", [selected_test.id, other_test.id])

    for i, test in enumerate(suite):  # pylint: disable=unused-variable
        test.expect_deselect()

    suite.run()


def test_matcher():
    for pattern, matching, not_matching in [
            ('xy', ['blapxy'], ['blap']),
            ('not x', ['blap', 'yyy'], ['blapx', 'xy']),
            ('x and y', ['xy', 'yx', 'x kjfldkjfd y'], ['x', 'y', 'xx']),
            ('(x and some.string) and not z', ['xysome.string', 'some.stringyx'], ['z', 'xysome.stringz']),
            ('exact(x=y)(y=z)', ['exact(x=y)(y=z)'], ['exlact(x=y)(y=z)']),
    ]:

        matcher = Matcher(pattern)
        for string in matching:
            assert matcher.matches(FakeMetadata(string))
        for string in not_matching:
            assert not matcher.matches(FakeMetadata(string))


def test_test_name_matcher():
    test_name = '/path/to/testfile.py:TestName'
    m = FakeMetadata(test_name)
    assert not Matcher('not {}'.format(test_name)).matches(m)
    assert Matcher(test_name).matches(m)


def test_matches_tag():
    assert Matcher('bla').matches(FakeMetadata('something', {'bla': 2}))
    assert not Matcher('bla').matches(FakeMetadata('something', {'bloop': 2}))
    assert Matcher('substring').matches(FakeMetadata('something', {'xxxxsubstringxxx': 2}))


def test_matches_tag_exclusively():
    assert Matcher('tag:bla').matches(FakeMetadata('something', {'bla': 2}))
    assert not Matcher('tag:bla').matches(FakeMetadata('bla', {'bloop': 2}))


def test_matches_values():
    assert Matcher('tag:bla=2').matches(FakeMetadata('something', {'bla': 2}))
    assert not Matcher('tag:bla=2').matches(FakeMetadata('something', {'bla': 3}))
    assert Matcher('tag:bla=hello').matches(FakeMetadata('something', {'bla': 'hello'}))
    assert not Matcher('tag:bla=bye').matches(FakeMetadata('something', {'bla': 'hello'}))


class FakeMetadata(object):

    def __init__(self, address, tags=NO_TAGS):
        super(FakeMetadata, self).__init__()
        if isinstance(tags, dict):
            tags = Tags(tags)
        self.address = address
        self.tags = tags
