import pytest
import slash

def test_compute_parameter_sanity(suite_builder):
    @suite_builder.first_file.add_code
    def __code__(): # pylint: disable=unused-variable
        import slash # pylint: disable=redefined-outer-name, reimported

        def get_parameter_value():
            return 'value1'

        @slash.parametrize('x', [slash.param('label', compute=get_parameter_value)])
        def test_something(x): # pylint: disable=unused-variable
            slash.context.result.data['params'] = x


    suite_builder.build().run().assert_success(1).with_data([
        {'params': 'value1'},
    ])

def test_compute_parameter_called_multiple_times_from_repeat_gets_different_values(suite_builder):
    @suite_builder.first_file.add_code
    def __code__(): # pylint: disable=unused-variable
        import slash # pylint: disable=redefined-outer-name, reimported
        from itertools import count
        x = count(1) # pylint: disable=unused-variable

        @slash.parametrize('x', [slash.param('label', compute=lambda: next(x))])
        @slash.repeat(2)
        def test_something(x): # pylint: disable=unused-variable
            slash.context.result.data['params'] = x

    suite_builder.build().run().assert_success(2).with_data([
        {'params': 1}, {'params': 2},
    ])

def test_compute_parameter_called_after_test_start_happened(suite_builder):
    @suite_builder.first_file.add_code
    def __code__(): # pylint: disable=unused-variable
        import slash # pylint: disable=redefined-outer-name, reimported

        def get_test_id_from_scope_manager():
            return slash.ctx.session.scope_manager._last_test.id # pylint: disable=protected-access

        @slash.parametrize('x', [slash.param('label', compute=get_test_id_from_scope_manager)])
        def test_something(x): # pylint: disable=unused-variable
            slash.context.result.data['params'] = x
    res = suite_builder.build().run()
    res.assert_success(1).with_data([
        {'params': res.slash_app.session.results[0].test_id}
    ])

def test_compute_parameter_for_exclusion_raises_exception(suite_builder):
    @suite_builder.first_file.add_code
    def __code__(): # pylint: disable=unused-variable
        import slash # pylint: disable=redefined-outer-name, reimported

        def get_value():
            return 1

        @slash.parametrize('x', [slash.param('label', compute=get_value)])
        @slash.exclude('x', [1])
        def test_something(x): # pylint: disable=unused-variable
            slash.context.result.data['params'] = x

    [res] = suite_builder.build().run().assert_results(1)
    [err] = res.get_errors()
    assert err.exception_type == slash.exceptions.ComputedParameterExcluded
    assert "computed parameter values cannot be excluded" in err.message

def test_compute_parameter_and_value_raises_exception(suite_builder):
    @suite_builder.first_file.add_code
    def __code__(): # pylint: disable=unused-variable
        import slash # pylint: disable=redefined-outer-name, reimported

        def get_parameter_value():
            return 'value1'

        @slash.parametrize('x', [slash.param('label', 'value', compute=get_parameter_value)])
        def test_something(x): # pylint: disable=unused-variable
            slash.context.result.data['params'] = x

    suite_builder.build().run().assert_session_error("has both value and compute defined")


@pytest.mark.parametrize('raw_values', [True, False])
def test_info_log_on_compute_if_raw_param_values_used(suite_builder, config_override, raw_values, tmpdir):
    config_override('log.show_raw_param_values', raw_values)
    config_override('log.root', str(tmpdir.join('logs')))
    @suite_builder.first_file.add_code
    def __code__(): # pylint: disable=unused-variable
        import slash # pylint: disable=redefined-outer-name, reimported

        def get_parameter_value():
            return 'value1'

        @slash.parametrize('x', [slash.param('label', compute=get_parameter_value)])
        def test_something(x): # pylint: disable=unused-variable
            slash.context.result.data['params'] = x
    res = suite_builder.build().run()
    res.assert_success(1).with_data([
        {'params': 'value1'},
    ])
    with open(res.slash_app.session.results[0].get_log_path()) as f:
        lines = f.read()
    found_in_logs = "INFO: slash.core.fixtures.parameters: Value of parameter label changed to value1" in lines
    if raw_values:
        assert found_in_logs
    else:
        assert not found_in_logs

def test_forgetting_compute_parameters_after_test_end(suite_builder):
    @suite_builder.first_file.add_code
    def __code__(): # pylint: disable=unused-variable
        import slash # pylint: disable=redefined-outer-name, reimported

        def get_parameter_value():
            return 'value1'

        @slash.parametrize('x', [slash.param('label', compute=get_parameter_value)])
        @slash.parametrize('y', [slash.param('label2', [1, 2, 3])])
        def test_something(x, y): # pylint: disable=unused-variable
            slash.context.result.data['params_x'] = x
            slash.context.result.data['params_y'] = y

    for result in suite_builder.build().run().slash_app.session.results:
        assert result.test_metadata.variation.values['x'] is None
        assert result.test_metadata.variation.values['y'] is not None
