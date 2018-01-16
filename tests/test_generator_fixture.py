import slash
from .utils import run_tests_in_session


def test_generator_fixture(suite, suite_test, get_fixture_location):
    fixture = get_fixture_location(suite_test).add_generator_fixture()
    suite_test.depend_on_fixture(fixture)
    suite.run()


def test_generator_fixture_with_name():

    @slash.generator_fixture(name='a_generator')
    def my_generator():
        yield 5

    @slash.generator_fixture
    def second_generator():  # pylint: disable=unused-variable
        yield 10

    def test_something(a_generator, second_generator):
        assert a_generator == 5
        assert second_generator == 10

    session = slash.Session()
    session.fixture_store.add_fixture(my_generator)
    session.fixture_store.add_fixture(second_generator)
    session.fixture_store.resolve()

    with session, session.get_started_context():
        run_tests_in_session(test_something, session=session)
    assert session.results.is_success(), 'run failed'
