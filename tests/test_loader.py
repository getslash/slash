import os
from uuid import uuid4

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


def test_loader_sort_filenames(tmpdir):

    tests_dir = tmpdir.join(str(uuid4()))

    filenames = []

    for _ in range(10):
        filename = str(uuid4()).replace('-', '') + '.py'

        with tests_dir.join(filename).open('w', ensure=True) as f:
            f.write('def test_something():\n    pass')

        filenames.append(filename)

    with Session():
        runnables = Loader().get_runnables(str(tests_dir))

    assert [os.path.basename(runnable.__slash__.file_path) for runnable in runnables] == sorted(filenames)


def test_loader_skips_empty_dirs(tmpdir):
    tests_dir = tmpdir.join('tests')
    with tests_dir.join('.dir').join('test_something.py').open('w', ensure=True) as f:
        f.write('def test_something():\n    pass')

    with Session():
        runnables = Loader().get_runnables(str(tests_dir))

    assert runnables == []


def test_loader_warns_duplicate_test_funcs(tmpdir):
    tests_dir = tmpdir.join('tests')
    full_path = tests_dir.join('.dir').join('test_something.py')
    test_name = 'test_something'
    with full_path.open('w', ensure=True) as f:
        f.write('def {}():\n    assert True\n'.format(test_name))
        f.write('def {}():\n    assert True\n'.format(test_name))
    with Session() as session:
        Loader().get_runnables([str(full_path)])
        assert len(session.warnings) == 1
        assert 'Duplicate' in session.warnings.warnings[0].details['message']
        assert test_name in session.warnings.warnings[0].details['message']


def test_loader_warns_on_duplicate_fixtures(suite):
    fixture_name = 'fixture_name'
    fixture1 = suite.slashconf.add_fixture(name=fixture_name)
    fixture1.append_line('assert this == slash.context.fixture')
    fixture2 = suite.slashconf.add_fixture(name=fixture_name)
    fixture2.append_line('assert this == slash.context.fixture')
    summary = suite.run()
    assert len(summary.session.warnings) == 1
    assert 'Duplicate' in summary.session.warnings.warnings[0].details['message']
    assert fixture_name in summary.session.warnings.warnings[0].details['message']


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

    pattern = '{}:{}'.format(os.path.join(path, suite_test.file.get_relative_path()), factory_name)
    if suite_test.cls is not None and specific_method:
        assert len(suite_test.cls.tests) > 1
        pattern += '.{}'.format(suite_test.name)
    suite.run(args=[pattern])


def test_import_error_registers_as_session_error(active_slash_session, test_loader):
    with pytest.raises(CannotLoadTests):
        test_loader.get_runnables(["/non/existent/path"])
    errors = active_slash_session.results.global_result.get_errors()
    assert len(errors) == 1
    [error] = errors  # pylint: disable=unused-variable

def test_no_traceback_for_slash_exception():
    suite = Suite()
    summary = suite.run(expect_session_errors=True)
    assert not summary.session.results.is_success()
    [err] = summary.session.results.global_result.get_errors()
    assert err.exception_type is CannotLoadTests
    output = summary.get_console_output()
    assert 'Traceback' not in output

def test_no_traceback_for_marked_exceptions():
    suite = Suite()

    @suite.slashconf.append_body
    def __code__():  # pylint: disable=unused-variable
        from slash.exception_handling import inhibit_unhandled_exception_traceback
        raise inhibit_unhandled_exception_traceback(Exception('Some Error'))

    summary = suite.run(expect_session_errors=True)
    assert not summary.session.results.is_success()
    errors = summary.session.results.global_result.get_errors()
    assert [err.exception_type for err in errors] == [Exception]
    assert 'Some Error' in errors[0].exception_str
    output = summary.get_console_output()
    assert 'Traceback' not in output

def test_import_errors_with_session():

    suite = Suite()

    for _ in range(20):
        suite.add_test()

    problematic = suite.files[1]
    problematic.prepend_line('from nonexistent import nonexistent')

    for test in suite:
        test.expect_deselect()

    summary = suite.run(expect_session_errors=True)

    assert summary.exit_code != 0

    errs = summary.session.results.global_result.get_errors()
    for err in errs:
        assert 'No module named nonexistent' in err.message or "No module named 'nonexistent'" in err.message


    return suite
