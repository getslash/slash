import gossip
import pytest
import slash
import slash.core.requirements

from .utils import make_runnable_tests


_UNMET_REQ_DECORATOR = 'slash.requires(lambda: False)'


def test_requirements_mismatch_session_success(suite, suite_test):
    suite_test.add_decorator('slash.requires(False)')
    suite_test.expect_skip()
    summary = suite.run()
    assert summary.session.results.is_success(allow_skips=True)


@pytest.mark.parametrize('requirement_fullfilled', [True, False])
@pytest.mark.parametrize('use_message', [True, False])
@pytest.mark.parametrize('use_fixtures', [True, False])
@pytest.mark.parametrize('message_in_retval', [True, False])
def test_requirements(suite, suite_test, requirement_fullfilled, use_fixtures, use_message, message_in_retval):

    message = "requires something very important"
    if use_message and message_in_retval:
        retval = '({}, {!r})'.format(requirement_fullfilled, message)
    else:
        retval = requirement_fullfilled

    suite_test.add_decorator('slash.requires((lambda: {0}), {1!r})'.format(retval, message if use_message and not message_in_retval else ''))
    if not requirement_fullfilled:
        suite_test.expect_skip()

    if use_fixtures:
        suite_test.depend_on_fixture(
            suite.slashconf.add_fixture())
    results = suite.run()
    if requirement_fullfilled:
        assert results[suite_test].is_success()
    else:
        assert not results[suite_test].is_started()
        assert results[suite_test].is_skip()
        if use_message:
            [skip] = results[suite_test].get_skips()
            assert message in skip


def test_requirements_functions_no_message(suite, suite_test):
    suite_test.add_decorator(_UNMET_REQ_DECORATOR)
    suite_test.expect_skip()
    results = suite.run()
    result = results[suite_test]
    [skip] = result.get_skips()
    assert 'lambda' in skip


def test_requirements_on_class():

    def req1():
        pass

    def req2():
        pass

    @slash.requires(req1)
    class Test(slash.Test):

        @slash.requires(req2)
        def test_something(self):
            pass

    with slash.Session():
        [test] = make_runnable_tests(Test)  # pylint: disable=unbalanced-tuple-unpacking

    assert [r._req for r in test.get_requirements()] == [req1, req2]  # pylint: disable=protected-access


def test_unmet_requirements_trigger_avoided_test_hook(suite, suite_test):

    suite_test.add_decorator(_UNMET_REQ_DECORATOR)
    suite_test.expect_skip()


    @gossip.register('slash.test_avoided')
    def test_avoided(reason):  # pylint: disable=unused-variable
        slash.context.result.data['avoided'] = {'reason': reason,
                                                'test_name': slash.context.test.__slash__.address}

    summary = suite.run()
    avoided_result = summary[suite_test]


    for r in summary.session.results.iter_all_results():
        if r is avoided_result:
            assert 'avoided' in r.data
            assert 'lambda' in r.data['avoided']['reason']
            assert 'unmet requirement' in r.data['avoided']['reason'].lower()
            assert r.data['avoided']['test_name'].split('_')[-1] == suite_test.id
        else:
            assert 'avoided' not in r.data


def test_adding_requirement_objects():

    class MyRequirement(slash.core.requirements.Requirement):
        pass

    req = MyRequirement('bla')

    @slash.requires(req)
    def test_something():
        pass

    with slash.Session():
        [test] = make_runnable_tests(test_something) # pylint: disable=unbalanced-tuple-unpacking

    reqs = test.get_requirements()
    assert len(reqs) == 1 and reqs[0] is req


def test_cannot_specify_message_with_requirement_object():

    class MyRequirement(slash.core.requirements.Requirement):
        pass

    with pytest.raises(AssertionError) as caught:
        slash.requires(MyRequirement(''), 'message')

    assert 'specify message' in str(caught.value)
