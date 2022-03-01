# pylint: disable=redefined-outer-name
import os
import sys

import pytest

from xml.etree import ElementTree


def test_xunit_plugin(results, xunit_filename): # pylint: disable=unused-argument
    assert os.path.exists(xunit_filename), 'xunit file not created'

    validate_xml(xunit_filename, results=results)


def test_session_errors(suite, xunit_filename):
    # pylint: disable=unused-argument

    @suite.slashconf.append_body
    def __code__():  # pylint: disable=unused-variable
        1/0  # pylint: disable=pointless-statement

    for test in suite:
        # tests are not going to even be loaded
        test.expect_deselect()

    summary = suite.run(expect_session_errors=True)

    assert 'ZeroDivision' in summary.get_console_output()



def test_xunit_plugin_test_details(suite, suite_test, xunit_filename, details):
    for key, value in details.items():
        suite_test.append_line('slash.context.result.set_test_detail({!r}, {!r})'.format(key, value))

    suite.run()
    testcase_xml = _get_testcase_xml(suite_test, xunit_filename)
    saved_details = {}
    for d in testcase_xml.findall('detail'):
        k = d.attrib['name']
        if 'value' in d.attrib:
            v = d.attrib['value']
        else:
            v = [child for child in d]
        saved_details[k] = v

    assert saved_details


@pytest.mark.parametrize('errtype', ['error', 'failure'])
def test_xunit_plugin_add_failure_error(suite, suite_test, xunit_filename, errtype):
    num_errors = 3
    for _ in range(num_errors):
        suite_test.append_line('slash.add_{}("some message")'.format(errtype))
    if errtype == 'error':
        suite_test.expect_error()
    else:
        suite_test.expect_failure()

    suite.run()
    testcase_xml = _get_testcase_xml(suite_test, xunit_filename)
    errors = testcase_xml.findall(errtype)
    assert len(errors) == num_errors
    for error in errors:
        assert error.attrib['message'] == 'some message'
        assert error.attrib['type'] == errtype
    assert errors



def _get_testcase_xml(suite_test, filename):
    with open(filename) as f:
        xml = ElementTree.parse(f)
    match = [testcase for testcase in list(xml.getroot()) if testcase.get('name').split('_')[-1] == suite_test.id]
    assert len(match) == 1
    return match[0]


@pytest.fixture(params=['set', 'append', 'complex', 'float', 'int'])
def details(request, result):

    if request.param == 'set':
        result.details.set('detail1', 'value1')
        result.details.set('detail2', 'value2')

    if request.param == 'append':
        result.details.append('detail1', 'value1')
        result.details.append('detail1', 'value2')

    if request.param == 'complex':
        result.details.append('detail1', 'value1')
        result.details.append(
            'detail1', {'complex': ['value2', 'value3']})

    if request.param == 'float':
        result.details.append('detail1', 12.3456)
        result.details.append('detail1', {'complex': [9.7531]})

    if request.param == 'int':
        result.details.append('detail1', 1)
        result.details.append('detail1', {'complex': [2]})

    return result.details.all()


@pytest.fixture  # pylint: disable=unused-argument
def results(suite, suite_test, test_event, xunit_filename): # pylint: disable=unused-argument
    test_event(suite_test)
    summary = suite.run()
    assert 'Traceback' not in summary.get_console_output()
    return summary

@pytest.fixture(params=['normal', 'skip_decorator_without_reason', 'skip_without_reason', 'skip_with_reason',
                        'error', 'failure', 'add_error', 'add_failure'])
def test_event(request):
    flavor = request.param

    def func(test):
        if flavor != 'normal':
            if flavor == 'skip_without_reason':
                test.when_run.skip(with_reason=False)
            elif flavor == 'skip_decorator_without_reason':
                test.when_run.skip(with_reason=False, decorator=True)
            elif flavor == 'skip_with_reason':
                test.when_run.skip(with_reason=True)
            elif flavor == 'error':
                test.when_run.error()
            elif flavor == 'failure':
                test.when_run.fail()
            elif flavor == 'add_error':
                test.append_line('slash.add_error("error")')
                test.expect_error()
            elif flavor == 'add_failure':
                test.append_line('slash.add_failure("failure")')
                test.expect_failure()
            else:
                raise NotImplementedError()  # pragma: no cover
    return func


@pytest.mark.skipif(sys.platform == 'win32', reason="does not run on windows")
@pytest.mark.parametrize('action', ['skipped', 'error', 'failure', 'success'])
def test_xunit_parallel_suite(parallel_suite, xunit_filename, action):
    test = parallel_suite[3]
    if action == 'skipped':
        test.when_run.skip()
    elif action == 'failure':
        test.when_run.fail()
    elif action == 'error':
        test.when_run.raise_exception()
    else:
        assert action == 'success', 'Unsupported action'
    parallel_suite.run()

    root = validate_xml(xunit_filename, suite=parallel_suite)
    if action != 'success':
        for child in root:
            if len(child) > 0: # pylint: disable=len-as-condition
                [element] = child
                break
        else:
            assert False, 'no child matching test found'
        assert element.tag == action


def validate_xml(xml_filename, suite=None, results=None):
    with open(xml_filename) as f:
        etree = ElementTree.parse(f)

    root = etree.getroot()
    assert root.tag == 'testsuite'

    test_count = _get_test_counts(root)

    if suite is not None:
        assert len(root) == len(suite)

    if results is not None:
        run_tests_results = list(
            filter(lambda result: result.is_started(),
                   results.session.results.iter_test_results())
        )
        assert len(list(root)) == len(run_tests_results)

    test_case_tag_count = {'error': 0, 'failure': 0, 'skipped': 0}

    for child in list(root):
        assert child.tag == 'testcase'
        assert child.get('name')
        assert child.get('time')

        for subchild in iter(child):
            assert subchild.tag in ['skipped', 'error', 'failure']
            test_case_tag_count.update(
                {subchild.tag: test_case_tag_count[subchild.tag] + 1}
            )

    assert test_count['skipped'] == test_case_tag_count['skipped']
    assert test_count['failures'] == test_case_tag_count['failure']
    assert test_count['errors'] == test_case_tag_count['error']

    return root


def _get_test_counts(element):
    test_count = {}

    for number in ['errors', 'failures', 'skipped']:
        test_count.update({number: int(element.get(number))})

    return test_count
