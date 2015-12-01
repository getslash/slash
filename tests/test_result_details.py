import pytest


def test_set_test_detail(result):
    result.set_test_detail('x', 'y')
    assert result.details.all() == {'x': 'y'}


def test_set(result):
    result.details.set('x', 'y')
    assert result.details.all() == {'x': 'y'}


def test_append(result):
    result.details.append('x', 'y')
    assert result.details.all() == {'x': ['y']}


def test_append_invalid_type(result):
    result.details.set('x', 'y')
    with pytest.raises(TypeError):
        result.details.append('x', 'y')
    assert result.details.all() == {'x': 'y'}

def test_bool(result):
    assert not result.details
    assert not bool(result.details)
    result.details.set('x', 'y')
    assert result.details
    assert bool(result.details)

def test_contains(result):
    assert 'x' not in result.details
    result.details.set('x', 'y')
    assert 'x' in result.details
