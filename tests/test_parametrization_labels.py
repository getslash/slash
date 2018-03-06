import pytest
import slash
from slash._compat import izip_longest


def test_parametrization_labels(suite, suite_test):
    param = suite_test.add_parameter()
    param.add_labels()

    @suite_test.append_body
    def __code__(): # pylint: disable=unused-variable
        # pylint: disable=undefined-variablepylint: disable=no-member, protected-access, undefined-variable
        slash.context.result.data['params'] = locals().copy()
        slash.context.result.data['params'].pop('self', None)

    res = suite.run()

    for label, value, result in izip_longest(
            param.labels, param.values, res.get_all_results_for_test(suite_test)):
        assert label
        assert value
        assert result
        #assert result.test_metadata.variation.id[param.name] == label
        assert result.data['params'] == {param.name: value}
        assert label in result.test_metadata.address


def test_parametrization_labels_multiple_params(suite_builder):
    # pylint: disable=unused-variable
    @suite_builder.first_file.add_code
    def __code__():
        import slash # pylint: disable=redefined-outer-name, reimported

        @slash.parametrize(('x', 'y'),
                           [slash.param('label1', (666, 777)),
                            slash.param('label2', (888, 999)),
                           ])
        def test_1(x, y):
            slash.context.result.data['params'] = [x, y]

    suite_builder.build().run().assert_success(2).with_data([
        {'params': [666, 777]},
        {'params': [888, 999]},
    ])


def test_alternate_labeling_syntax(suite_builder):
    # pylint: disable=unused-variable
    @suite_builder.first_file.add_code
    def __code__():
        import slash # pylint: disable=reimported, redefined-outer-name

        @slash.parametrize(('x', 'y'), [
            (1, 2) // slash.param('label1'),
            (3, 4) // slash.param('label2'),
        ])
        def test_something(x, y):
            slash.context.result.data['params'] = (x, y)


    suite_builder.build().run().assert_success(2).with_data([
        {'params': (1, 2)},
        {'params': (3, 4)},
    ])


def test_must_provide_parameter_value(suite_builder):
    # pylint: disable=unused-variable,unused-argument
    @suite_builder.first_file.add_code
    def __code__():
        import slash # pylint: disable=reimported, redefined-outer-name

        @slash.parametrize('x', [
            slash.param('label1'),
        ])
        def test_something(x):
            pass

    suite_builder.build().run().assert_session_error('Parameter label1 has no value defined')


@pytest.mark.parametrize('invalid_value', [
    'x' * 31,
    '123xy',
    '123',
])
def test_invalid_param_values(invalid_value):
    with pytest.raises(RuntimeError) as caught:
        slash.param(invalid_value)
    assert 'invalid label' in str(caught.value).lower()


@pytest.mark.parametrize('valid_value', [
    'hello',
    'hello123',
    'variable_1',
    'x' * 30,
])
def test_valid_param_values(valid_value):
    slash.param(valid_value)


def test_generator_fixture_param_labels(suite_builder):
    # pylint: disable=no-member, protected-access, undefined-variable,unused-variable, reimported, redefined-outer-name
    @suite_builder.first_file.add_code
    def __code__():
        import slash

        @slash.generator_fixture
        def param():
            yield 'value1' // slash.param('first_value')
            yield 'value2' // slash.param('second_value')

        def test_1(param):
            slash.context.result.data['value'] = param

    suite_builder.build().run().assert_success(2).with_data([
        {'value': 'value1'},
        {'value': 'value2'},
    ])
