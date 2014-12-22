import pytest

from .utils.suite_writer import Suite

def test_fixture(suite):
    f = suite.slashconf.add_fixture()
    test = suite[1]
    test.depend_on_fixture(f)
    result = suite.run()
    result.events.assert_consecutive([
        ('fixture_start', f.id),
        ('test_start', test.id),
        ('test_end', test.id),
        ('fixture_end', f.id),
        ])

def test_parametrized_fixture():
    suite = Suite()
    test = suite.add_test()
    f1 = suite.slashconf.add_fixture()
    p = f1.add_parameter()
    test.depend_on_fixture(f1)
    summary = suite.run()
    assert summary.ok()
    assert len(summary.session.results) == len(p.values)

def test_regular_test_parametrization(suite, test):
    p = test.add_parameter()
    res = suite.run()

@pytest.fixture
def test(suite, is_method):
    if is_method:
        return suite.method_tests[0]
    return suite.function_tests[0]

@pytest.fixture(params=[True, False])
def is_method(request):
    return request.param

@pytest.fixture
def suite():
    s = Suite()
    for i in range(10):
        s.add_test()
    return s
