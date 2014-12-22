import pytest

from .utils.suite_writer import Suite


@pytest.mark.parametrize('num_tests', [1, 10])
def test_len(num_tests):
    s = Suite()
    for i in range(num_tests):
        s.add_test()

    assert len(s) == num_tests


def test_no_debug_info():
    s = Suite()
    s.debug_info = False

    for i in range(10):
        s.add_test()

    f = s.slashconf.add_fixture()
    s[3].depend_on_fixture(f)
    assert s.run().ok()
