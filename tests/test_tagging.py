# pylint: disable=redefined-outer-name
import itertools

import pytest
import slash
from sentinels import NOTHING
from slash.core.tagging import NO_TAGS, Tags, get_tags
from slash.exceptions import TaggingConflict
from slash.loader import Loader

from .utils.suite_writer.method_test import MethodTest


def test_setting_getting_tags(taggable):

    slash.tag('tagname')(taggable)

    assert 'tagname' in get_tags(taggable)
    assert 'other_tags' not in get_tags(taggable)


def test_no_tags_contains(taggable):
    assert 'bla' not in get_tags(taggable)


def test_tags_addition_no_tags_no_tags():
    assert NO_TAGS + NO_TAGS is NO_TAGS


def test_tags_addition_no_tags_regular():
    tags = Tags({'a': 'b'})
    assert NO_TAGS + tags is tags
    assert tags + NO_TAGS is tags


def test_tags_addition_regular():
    tags1 = Tags({'a': 'b'})
    tags2 = Tags({'c': 'd'})
    tags3 = tags1 + tags2
    assert tags3 is not tags1
    assert tags3 is not tags2

    # pylint: disable=protected-access
    assert tags1._tags == {'a': 'b'}
    assert tags2._tags == {'c': 'd'}
    assert tags3._tags == {'a': 'b', 'c': 'd'}


def test_tags_addition_conflicting_keys():
    tags1 = Tags({'a': 'b'})
    conlifcting_tags = Tags({'a': 'c'})
    assert (tags1 + tags1)._tags == tags1._tags # pylint: disable=protected-access
    with pytest.raises(TaggingConflict):
        tags1 + conlifcting_tags # pylint: disable=pointless-statement


def test_setting_getting_tags_on_metadata(taggable):

    slash.tag('tagname')(taggable)

    with slash.Session() as s:  # pylint: disable=unused-variable
        tests = Loader().get_runnables(taggable)
    assert tests
    for t in tests:
        assert 'tagname' in t.__slash__.tags


def test_metadata_tags(suite, suite_test, tagging_strategy, tags):
    tagging_strategy(suite_test, tags)
    summary = suite.run()
    [result] = summary.get_all_results_for_test(suite_test)
    for tag_name, tag_value in tags:
        assert result.test_metadata.tags.has_tag(tag_name)
        assert result.test_metadata.tags[tag_name] == tag_value


def test_tagging_twice_forbidden_different_values():
    @slash.tag('something', 1)
    def test_something():
        pass

    tagger = slash.tag('something', 2)
    with pytest.raises(TaggingConflict):
        tagger(test_something)


def test_tagging_twice_allowed_same_values():
    @slash.tag('something', 1)
    def test_something():
        pass

    tagger = slash.tag('something', 1)
    tagger(test_something)


def test_tagging_twice_allowed_no_value():
    @slash.tag('something')
    def test_something():
        pass

    tagger = slash.tag('something')
    tagger(test_something)


def test_tagging_fixture(suite_builder):
    # pylint: disable=unused-variable
    @suite_builder.first_file.add_code
    def __code__():
        import slash # pylint: disable=redefined-outer-name, reimported
        @slash.tag('tag-1')
        @slash.fixture
        def fixture1():
            pass

        @slash.tag('tag-2')
        @slash.fixture
        def fixture2(fixture1):  # pylint: disable=unused-argument
            pass

        @slash.tag('test-tag')
        def test_depend_composite_fixture(fixture2):  # pylint: disable=unused-argument
            assert set(slash.context.test.get_tags()) == {'tag-1', 'tag-2', 'test-tag'}

        @slash.tag('test-tag')
        def test_depend_simple_fixture(fixture1):  # pylint: disable=unused-argument
            assert set(slash.context.test.get_tags()) == {'tag-1', 'test-tag'}

        def test_no_fixtures():
            assert not set(slash.context.test.get_tags())

        @slash.tag('tag-1')
        def test_and_fixture_same_tag(fixture1):  # pylint: disable=unused-argument
            assert set(slash.context.test.get_tags()) == {'tag-1'}

    suite_builder.build().run().assert_success(4)

def test_fixture_and_test_overrides(suite_builder):
    # pylint: disable=unused-variable
    @suite_builder.first_file.add_code
    def __code__():
        import slash # pylint: disable=redefined-outer-name, reimported
        @slash.tag('tag-1', 'fixture_value')
        @slash.fixture
        def fixture1():
            pass

        @slash.tag('tag-1', 'test_value')
        def test_depend_composite_fixture(fixture1):  # pylint: disable=unused-argument
            pass

    suite_builder.build().run().assert_session_error("Conflicting tag")

# more tags in test_pattern_matching.py

_tagging_strategies = []


def _tagging_strategy(func):
    _tagging_strategies.append(func)
    return func


@_tagging_strategy
def _simple_tagging_strategy(taggable, tags):
    for tag_name, tag_value in tags:
        taggable.add_decorator(_get_slash_tag_string(tag_name, tag_value))


@_tagging_strategy
def _tag_class_only(taggable, tags):
    if isinstance(taggable, MethodTest):
        _simple_tagging_strategy(taggable.cls, tags)
    else:
        _simple_tagging_strategy(taggable, tags)


@_tagging_strategy
def _tag_class_and_method(taggable, tags):
    if not isinstance(taggable, MethodTest):
        return _simple_tagging_strategy(taggable, tags)

    for (tag_name, tag_value), taggable in zip(tags, itertools.cycle([taggable.cls, taggable])):
        taggable.add_decorator(_get_slash_tag_string(tag_name, tag_value))


def _get_slash_tag_string(tag_name, tag_value):
    returned = 'slash.tag({!r}'.format(tag_name)
    if tag_value is not NOTHING:
        returned += ', {!r}'.format(tag_value)
    returned += ')'
    return returned


@pytest.fixture(params=_tagging_strategies)
def tagging_strategy(request):
    return request.param


@pytest.fixture(params=[
    {'simple_tag_without_value': NOTHING},
    {'single_tag': 'string_value'},
    {'multiple_tags_1': 1.0, 'multiple_tags_2': True, 'multiple_tags_3': ['list', 'of', 'things']},
])
def tags(request):
    return list(request.param.items())


@pytest.fixture(params=['class', 'function'])
def taggable(request):
    if request.param == 'class':
        class TaggableTest(slash.Test):

            def test_1():  # pylint: disable=no-method-argument
                pass
        return TaggableTest
    elif request.param == 'function':
        def test_1():
            pass
        return test_1

    raise NotImplementedError()  # pragma: no cover
