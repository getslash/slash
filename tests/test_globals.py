from .utils import TestCase
import slash
from slash import Session
from slash import context


def test_current_test(suite):

    suite.add_test(regular_function=False).inject_line(
        'assert slash.test is self')
    suite.add_test(regular_function=False).inject_line(
        'assert slash.context.test is self')
    suite.add_test(regular_function=False).inject_line(
        'assert slash.context.test.id is self.__slash__.id')


def test_get_current_session():
    with Session() as s:
        assert context.session is s
        assert context.session is not slash.session
        assert s == slash.session
