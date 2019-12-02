# pylint: disable=redefined-outer-name
from uuid import uuid1

import slash
import pytest
from sentinels import NOTHING
from slash.core.local_config import LocalConfig


def test_local_conf(local_conf, expected_dict):
    conf = local_conf.get_dict()
    for key, value in expected_dict.items():
        assert [value] == conf[key]


def test_local_conf_loading_multiple_times(local_conf_dir, expected_dict):
    items = list(expected_dict.items())
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


def test_local_conf_with_both_slashconf_file_and_dir(tmpdir):
    with tmpdir.join('slashconf.py').open('w') as f:
        f.write("x = 1")
    conf_dir = tmpdir.join("slashconf")
    conf_dir.mkdir()
    with tmpdir.join('slashconf.py').open('w') as f:
        f.write("y = 2")
    local_config = LocalConfig()
    with pytest.raises(AssertionError) as caught:
        local_config.push_path(str(tmpdir))
    assert str(tmpdir) in str(caught.value)


def test_local_conf_with_slashconf_dir(tmpdir):
    conf_dir = tmpdir.join("slashconf")
    conf_dir.mkdir()
    with conf_dir.join('some_file.py').open('w') as f:
        f.write("x = 42")
    with conf_dir.join("other_file.py").open("w") as f:
        f.write("a = 1\n")
        f.write("b = 2")
    with conf_dir.join("__init__.py").open("w") as f:
        f.write("import slash\n")
        f.write("c = 1")
    local_config = LocalConfig()
    local_config.push_path(str(tmpdir))
    expected = {"a": 1, "b": 2, "c": 1, "x": 42, "slash": slash}
    config_dict = local_config.get_dict()
    got = {key: config_dict.get(key, NOTHING) for key in expected}
    assert expected == got



@pytest.fixture
def local_conf(local_conf_dir):
    returned = LocalConfig()
    returned.push_path(str(local_conf_dir))
    return returned


@pytest.fixture(params=[True, False])
def local_conf_dir(request, tmpdir, expected_dict):
    root_dir = returned = tmpdir
    is_conf_dir = request.param
    if is_conf_dir:
        returned = conf_dir = root_dir.join("slashconf")
        returned.mkdir()
    for i, (key, value) in enumerate(expected_dict.items()):
        returned = returned.join('subdir{}'.format(i))
        returned.mkdir()

        filename = f"{i}.py" if is_conf_dir else "slashconf.py"
        with returned.join(filename).open('w') as f:
            f.write('{} = [{!r}]'.format(key, value))
    if is_conf_dir:
        return conf_dir
    return returned


@pytest.fixture
def expected_dict():
    return dict(('key_{}'.format(i), 'value_{}_{}'.format(i, uuid1())) for i in range(10))
