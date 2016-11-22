# pylint: disable=redefined-outer-name
from uuid import uuid4

import gossip

import pytest


def test_facts(suite, suite_test, fact_name, fact_value):

    facts = []

    @gossip.register('slash.fact_set')
    def fact_set(name, value): # pylint: disable=unused-variable
        facts.append((name, value))

    suite_test.append_line('slash.context.result.facts.set({!r}, {!r})'.format(fact_name, fact_value))
    res = suite.run()[suite_test]
    assert res.facts.all() == {fact_name : fact_value}
    assert facts == [(fact_name, fact_value)]


@pytest.fixture
def fact_name():
    return 'some_fact'


@pytest.fixture
def fact_value():
    return str(uuid4())
