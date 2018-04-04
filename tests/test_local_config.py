# pylint: disable=redefined-outer-name
from uuid import uuid1

import pytest
from slash._compat import iteritems, OrderedDict
from slash.core.local_config import LocalConfig


def test_local_conf(local_conf, expected_dict):
    conf = local_conf.get_dict()
    for key, value in iteritems(expected_dict):
        assert [value] == conf[key]


def test_local_conf_loading_multiple_times(local_conf_dir, expected_dict):
    items = list(iteritems(expected_dict))
    local_conf = LocalConfig()

    local_conf.push_path(str(local_conf_dir.join('..')))
    var_name, var_value = items[0]
    var = local_conf.get_dict()[var_name]
    assert var == [var_value]

    local_conf.push_path(str(local_conf_dir))

    assert var is local_conf.get_dict()[var_name]


def test_local_conf_nonexistent_dir():
    with pytest.raises(RuntimeError):
        LocalConfig().push_path('/nonexistent/dir')


@pytest.fixture
def local_conf(local_conf_dir):
    returned = LocalConfig()
    returned.push_path(str(local_conf_dir))
    return returned


@pytest.fixture
def local_conf_dir(tmpdir, expected_dict):
    returned = tmpdir
    for i, (key, value) in enumerate(iteritems(expected_dict)):
        returned = returned.join('subdir{}'.format(i))
        returned.mkdir()

        with returned.join('slashconf.py').open('w') as f:
            f.write('{} = [{!r}]'.format(key, value))
    return returned


@pytest.fixture
def expected_dict():
    return OrderedDict(('key_{}'.format(i), 'value_{}_{}'.format(i, uuid1())) for i in range(10))
