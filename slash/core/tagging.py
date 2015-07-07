import functools

from sentinels import NOTHING

_TAGS_NAME = '__slash_tags__'


def tag_test(test, tag_name, tag_value):
    tags = get_tags(test)
    if tags is NO_TAGS:
        tags = Tags()
        setattr(test, _TAGS_NAME, tags)
    assert tag_name not in tags
    tags[tag_name] = tag_value
    return test


def tag(tag_name, tag_value=NOTHING):
    """Decorator for tagging tests
    """
    return functools.partial(tag_test, tag_name=tag_name, tag_value=tag_value)


def get_tags(test):
    return getattr(test, _TAGS_NAME, NO_TAGS)


class Tags(object):

    def __init__(self, tags=None):
        super(Tags, self).__init__()
        if tags is None:
            tags = {}
        self._tags = tags

    def __setitem__(self, tag, value):
        self._tags[tag] = value

    def __getitem__(self, tag):
        return self._tags[tag]

    def __contains__(self, tag):
        return tag in self._tags

    has_tag = __contains__

    def __add__(self, other):
        if other is NO_TAGS:
            return self
        new_tags = self._tags.copy()
        new_tags.update(other._tags)
        return Tags(new_tags)


class _NoTags(object):

    def __contains__(self, tag):
        return False

    def __add__(self, other):
        return other

    has_tag = __contains__

NO_TAGS = _NoTags()
