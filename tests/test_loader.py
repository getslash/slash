import os

import pytest
from slash import Session
from slash.exceptions import CannotLoadTests
from slash.loader import Loader

from .utils.suite_writer import Suite


def test_total_num_tests(suite):
    suite.debug_info = False

    path = suite.commit()

    with Session() as s:
        Loader().get_runnables(path)
        assert s.get_total_num_tests() == len(suite)


def test_loader_skips_empty_dirs(tmpdir):
    tests_dir = tmpdir.join('tests')
    with tests_dir.join('.dir').join('test_something.py').open('w', ensure=True) as f:
        f.write('def test_something():\n    pass')

    with Session():
        runnables = Loader().get_runnables(str(tests_dir))
    assert runnables == []


@pytest.mark.parametrize('specific_method', [True, False])
@pytest.mark.parametrize('with_parameters', [True, False])
def test_iter_specific_factory(suite, suite_test, specific_method, with_parameters):

    if suite_test.cls is not None and specific_method:
        suite_test.cls.add_method_test()

    if with_parameters:
        suite_test.add_parameter()

    for test in suite:
        if suite_test.cls is None and test is not suite_test:
            # we are selecting a specific function, and that's not it:
            test.expect_deselect()
        elif suite_test.cls is not None and test.cls is not suite_test.cls:
            test.expect_deselect()
        elif specific_method and suite_test.cls is test.cls and suite_test is not test:
            test.expect_deselect()

    path = suite.commit()
    if suite_test.cls:
        assert suite_test.cls.tests
        factory_name = suite_test.cls.name
    else:
        factory_name = suite_test.name

    pattern = '{0}:{1}'.format(os.path.join(path, suite_test.file.get_relative_path()), factory_name)
    if suite_test.cls is not None and specific_method:
        assert len(suite_test.cls.tests) > 1
        pattern += '.{0}'.format(suite_test.name)
    suite.run(args=[pattern])


def test_import_error_registers_as_session_error(active_slash_session, test_loader):
    with pytest.raises(CannotLoadTests):
        test_loader.get_runnables(["/non/existent/path"])
    errors = active_slash_session.results.global_result.get_errors()
    assert len(errors) == 1
    [error] = errors


def test_import_errors_with_session():

    suite = Suite()

    for i in range(20):
        suite.add_test()

    problematic = suite.files[1]
    problematic.prepend_line('from nonexistent import nonexistent')

    for test in suite:
        test.expect_deselect()

    summary = suite.run()

    assert 0 != summary.exit_code

    errs = summary.session.results.global_result.get_errors()
    for err in errs:
        assert 'No module named nonexistent' in err.message or "No module named 'nonexistent'" in err.message


    return suite
