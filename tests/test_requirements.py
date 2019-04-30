# pylint: disable=redefined-outer-name
import gossip
import pytest
import slash
import slash.core.requirements
from .utils import make_runnable_tests
from .utils.suite_writer.suite import Suite
from .utils.code_formatter import CodeFormatter
from slash._compat import ExitStack, PY2

if PY2:
    from slash.utils.python import wraps
else:
    from functools import wraps

_UNMET_REQ_DECORATOR = "slash.requires(lambda: False)"
_MET_REQ_DECORATOR = "slash.requires(lambda: True)"


def test_ensure_requirements_called_eagerly(checkpoint1, checkpoint2):
    def predicate_1():
        checkpoint1()
        return False

    def predicate_2():
        checkpoint2()
        return False

    @slash.requires(predicate_1)
    @slash.requires(predicate_2)
    def test_something():
        pass

    with slash.Session() as session:
        with session.get_started_context():
            slash.runner.run_tests(make_runnable_tests(test_something))
    [result] = [
        res for res in session.results.iter_all_results() if not res.is_global_result()
    ]
    assert result.is_skip()
    assert checkpoint1.called
    assert checkpoint2.called


def test_requirements_raises_exception(suite, suite_test):
    @suite_test.file.append_body
    def __code__():  # pylint: disable=unused-variable
        def fail_predicate():  # pylint: disable=unused-variable
            raise Exception("Failing")

    suite_test.add_decorator("slash.requires(fail_predicate)")
    suite_test.expect_error()
    summary = suite.run()
    assert not summary.session.results.is_success(allow_skips=True)


def test_requirements_mismatch_session_success(suite, suite_test):
    suite_test.add_decorator("slash.requires(False)")
    suite_test.expect_skip()
    summary = suite.run()
    assert summary.session.results.is_success(allow_skips=True)


@pytest.mark.parametrize("requirement_fullfilled", [True, False])
@pytest.mark.parametrize("use_message", [True, False])
@pytest.mark.parametrize("use_fixtures", [True, False])
@pytest.mark.parametrize("message_in_retval", [True, False])
def test_requirements(
    suite,
    suite_test,
    requirement_fullfilled,
    use_fixtures,
    use_message,
    message_in_retval,
):

    message = "requires something very important"
    if use_message and message_in_retval:
        retval = "({}, {!r})".format(requirement_fullfilled, message)
    else:
        retval = requirement_fullfilled

    suite_test.add_decorator(
        "slash.requires((lambda: {}), {!r})".format(
            retval, message if use_message and not message_in_retval else ""
        )
    )
    if not requirement_fullfilled:
        suite_test.expect_skip()

    if use_fixtures:
        suite_test.depend_on_fixture(suite.slashconf.add_fixture())
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
    assert "lambda" in skip


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

    assert set([r._req for r in test.get_requirements()]) == set( # pylint: disable=protected-access
        [req1, req2]
    )


@pytest.fixture
def filename_test_fixture(tmpdir):
    returned = str(tmpdir.join("testfile.py"))

    with open(returned, "w") as f:
        with ExitStack() as stack:
            code = CodeFormatter(f)

            code.writeln("import slash")
            code.writeln("@slash.fixture")
            code.writeln(
                "@slash.requires({}, {})".format(_UNMET_REQ_DECORATOR, '"msg1"')
            )
            code.writeln("def fixture():")
            with code.indented():
                code.writeln("return 1")

            code.writeln("@slash.fixture(autouse=True)")
            code.writeln("@slash.requires({}, {})".format(_MET_REQ_DECORATOR, '"msg2"'))
            code.writeln("def fixture1():")
            with code.indented():
                code.writeln("return 1")

            code.writeln("class Test(slash.Test):")
            stack.enter_context(code.indented())

            code.write("def test_1(")
            code.write("self, ")
            code.writeln("fixture):")
            with code.indented():
                code.writeln("pass")
    return returned


def test_requirements_on_class_with_fixture_and_autouse_fixture(filename_test_fixture):
    with slash.Session():
        [test] = make_runnable_tests( # pylint: disable=unbalanced-tuple-unpacking
            filename_test_fixture
        )
    assert sorted([str(r) for r in test.get_requirements()]) == ["msg1", "msg2"]


def test_unmet_requirements_trigger_avoided_test_hook(suite, suite_test):

    suite_test.add_decorator(_UNMET_REQ_DECORATOR)
    suite_test.expect_skip()

    @gossip.register("slash.test_avoided")
    def test_avoided(reason):  # pylint: disable=unused-variable
        slash.context.result.data["avoided"] = {
            "reason": reason,
            "test_name": slash.context.test.__slash__.address,
        }

    summary = suite.run()
    avoided_result = summary[suite_test]

    for r in summary.session.results.iter_all_results():
        if r is avoided_result:
            assert "avoided" in r.data
            assert "lambda" in r.data["avoided"]["reason"]
            assert "unmet requirement" in r.data["avoided"]["reason"].lower()
            assert r.data["avoided"]["test_name"].split("_")[-1] == suite_test.id
        else:
            assert "avoided" not in r.data


def test_adding_requirement_objects():
    class MyRequirement(slash.core.requirements.Requirement):
        pass

    req = MyRequirement("bla")

    @slash.requires(req)
    def test_something():
        pass

    with slash.Session():
        [test] = make_runnable_tests( # pylint: disable=unbalanced-tuple-unpacking
            test_something
        )  # pylint: disable=unbalanced-tuple-unpacking

    reqs = test.get_requirements()
    assert len(reqs) == 1 and reqs[0] is req


def test_cannot_specify_message_with_requirement_object():
    class MyRequirement(slash.core.requirements.Requirement):
        pass

    with pytest.raises(AssertionError) as caught:
        slash.requires(MyRequirement(""), "message")

    assert "specify message" in str(caught.value)


@pytest.mark.parametrize("is_fixture_requirement_unmet", [True, False])
def test_fixture_and_test_requirements(suite, suite_test, is_fixture_requirement_unmet):
    suite_test.depend_on_fixture(suite.slashconf.add_fixture())
    if is_fixture_requirement_unmet:
        suite_test._fixtures[0][1].add_decorator( # pylint: disable=protected-access
            _UNMET_REQ_DECORATOR
        )
        suite_test.add_decorator(_MET_REQ_DECORATOR)
    else:
        suite_test._fixtures[0][1].add_decorator( # pylint: disable=protected-access
            _MET_REQ_DECORATOR
        )
        suite_test.add_decorator(_UNMET_REQ_DECORATOR)

    suite_test.expect_skip()
    results = suite.run()
    assert results[suite_test].is_skip()
    result = results[suite_test]
    [skip] = result.get_skips()
    assert "lambda" in skip


def test_fixture_of_fixture_requirement(suite, suite_test):
    suite_test.add_decorator(_UNMET_REQ_DECORATOR)
    suite_test.depend_on_fixture(suite.slashconf.add_fixture())
    suite_test._fixtures[0][1].add_decorator( # pylint: disable=protected-access
        _MET_REQ_DECORATOR
    )
    suite_test.expect_skip()
    results = suite.run()
    assert results[suite_test].is_skip()

    result = results[suite_test]
    [skip] = result.get_skips()
    assert "lambda" in skip


def test_autouse_fixture_requirement():
    suite = Suite()
    for _ in range(5):
        test = suite.add_test(type="function")
        test.expect_skip()
    fixture = suite.get_last_file().add_fixture(autouse=True)
    fixture.add_decorator(_UNMET_REQ_DECORATOR)
    suite.run()


def test_class_requirements_siblings(suite_builder):
    @suite_builder.first_file.add_code
    def __code__():  # pylint: disable=unused-variable
        import slash  # pylint: disable=redefined-outer-name, reimported

        @slash.requires(lambda: True)
        class BaseTest(slash.Test):
            pass

        @slash.requires(lambda: False) # pylint: disable=unused-variable
        class FirstTest(BaseTest):
            def test(self):
                pass

        class SecondTest(BaseTest): # pylint: disable=unused-variable
            def test(self):
                pass

    suite_builder.build().run().assert_results_breakdown(skipped=1, success=1)


@pytest.mark.parametrize("class_can_run", [True, False])
@pytest.mark.parametrize("method_can_run", [True, False])
def test_class_requirements_class_and_method(class_can_run, method_can_run):
    @slash.requires(lambda: class_can_run)
    class Test(slash.Test):
        @slash.requires(lambda: method_can_run)
        def test(self):
            pass

    with slash.Session() as session:
        with session.get_started_context():
            slash.runner.run_tests(make_runnable_tests(Test))
    results = [res for res in session.results.iter_test_results()]
    assert len(results) == 1
    if class_can_run and method_can_run:
        assert results[0].is_success()
    else:
        assert results[0].is_skip()


def test_attach_requirements_through_wraps_on_function():

    def decorator(func):
        @wraps(func)
        def new_func():
            pass
        return new_func

    req1, req2, req3, req4 = requirements = [object() for _ in range(4)]

    @slash.requires(req4)
    @slash.parametrize('x', [1, 2, 3])
    @slash.requires(req3)
    @slash.parametrize('y', [2, 3, 4])
    @slash.requires(req2)
    @decorator
    @slash.requires(req1)
    def test_something(x, y): # pylint: disable=unused-argument
        pass

    found_reqs = slash.core.requirements.get_requirements(test_something)
    assert len(found_reqs) == len(requirements)
    for expected, found in zip(requirements, found_reqs):
        assert expected is found._req # pylint: disable=trailing-whitespace, protected-access
