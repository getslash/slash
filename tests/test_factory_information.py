import pytest

import slash
from slash.core.function_test import FunctionTestFactory
from slash.core.test import TestTestFactory


def test_factory_name(factory, expected_factory_name):
    assert factory.get_factory_name() == expected_factory_name

def test_module_name(factory, expected_module_name):
    assert factory.get_module_name() == expected_module_name

def test_filename(factory, expected_filename):
    assert factory.get_filename() == expected_filename

################################################################################

@pytest.fixture
def factory(explicit, factory_class, factory_param):
    returned = factory_class(factory_param)
    return returned

@pytest.fixture
def expected_factory_name(factory, explicit, factory_param):
    if explicit:
        returned = 'SomeFactoryNameHere'
        factory.set_factory_name(returned)
        return returned
    else:
        return factory_param.__name__

@pytest.fixture
def expected_filename(factory, explicit):
    if explicit:
        returned = 'some_nonexisting_file.py'
        factory.set_filename(returned)
        return returned
    else:
        returned = __file__
        if returned.endswith('.pyc'):
            returned = returned[:-1]
        return returned

@pytest.fixture
def expected_module_name(factory, explicit):
    if explicit:
        returned = 'some_module'
        factory.set_module_name(returned)
        return returned
    else:
        returned = __name__
        return returned


@pytest.fixture(params=[True, False])
def explicit(request):
    return request.param

@pytest.fixture(params=[FunctionTestFactory, TestTestFactory])
def factory_class(request):
    return request.param

@pytest.fixture
def factory_param(factory_class):
    if factory_class is FunctionTestFactory:
        def test_something():
            pass

        return test_something
    elif factory_class is TestTestFactory:

        class ExampleTest(slash.Test):

            def test_something(self):
                pass

        return ExampleTest

    else:
        raise NotImplementedError("Unknown factory class")
