from sentinels import NOTHING

from ..exceptions import TaggingConflict

_TAGS_NAME = "__slash_tags__"


class Tagger(object):
    def __init__(self, tag_name, tag_value):
        self.tag_name = tag_name
        self.tag_value = tag_value

    def __call__(self, target):
        assert callable(target)
        return tag_test(target, self.tag_name, self.tag_value)

    def __rfloordiv__(self, other):
        from .fixtures.parameters import ParametrizationValue

        return ParametrizationValue(value=other, tags=[(self.tag_name, self.tag_value)])


def tag_test(test, tag_name, tag_value):
    tags = get_tags(test)
    if tags is NO_TAGS:
        tags = Tags()
        setattr(test, _TAGS_NAME, tags)
    if tags.get(tag_name, NOTHING) not in (tag_value, NOTHING):
        raise TaggingConflict("Tag {} is already set on {}".format(tag_name, test))
    tags[tag_name] = tag_value
    return test


def tag(tag_name, tag_value=NOTHING):
    """Decorator for tagging tests
    """
    return Tagger(tag_name=tag_name, tag_value=tag_value)


def get_tags(test):
    return getattr(test, _TAGS_NAME, NO_TAGS)


class Tags(object):
    def __init__(self, tags=None):
        super(Tags, self).__init__()
        if tags is None:
            tags = {}
        self._tags = tags

    def __setitem__(self, tag_name, value):
        self._tags[tag_name] = value

    def __getitem__(self, tag_name):
        return self._tags[tag_name]

    def __contains__(self, tag_name):
        return tag_name in self._tags

    has_tag = __contains__

    def _check_conflicting_tags(self, other):
        for (
            tag_name,
            tag_value,
        ) in other._tags.items():  # pylint: disable=protected-access
            if self.get(tag_name, NOTHING) not in (tag_value, NOTHING):
                raise TaggingConflict(
                    "Conflicting tag: {} when adding {}, {}".format(
                        tag_name, self, other
                    )
                )

    def __add__(self, other):
        if other is NO_TAGS:
            return self
        self._check_conflicting_tags(other)
        new_tags = self._tags.copy()
        new_tags.update(other._tags)  # pylint: disable=protected-access
        return Tags(new_tags)

    def copy(self):
        return Tags(self._tags.copy())

    def update(self, other):
        if other is NO_TAGS:
            return
        self._check_conflicting_tags(other)
        self._tags.update(other._tags)  # pylint: disable=protected-access

    def get(self, *args, **kwargs):
        return self._tags.get(*args, **kwargs)

    def matches_pattern(self, pattern, exact=False):
        if "=" in pattern:
            key, predicate = pattern.split("=", 1)
            value = self._tags.get(key, NOTHING)
            return value is not NOTHING and str(value) == predicate

        for key, value in self._tags.items():
            if exact:
                if pattern == key:
                    return True
            else:
                if pattern in key:
                    return True
        return False

    def __iter__(self):
        return iter(self._tags)


class _NoTags(object):
    def __contains__(self, tag_name):
        return False

    def __add__(self, other):
        return other

    has_tag = __contains__

    def matches_pattern(self, pattern, **_):  # pylint: disable=unused-argument
        return False

    def __iter__(self):
        return iter([])


NO_TAGS = _NoTags()
