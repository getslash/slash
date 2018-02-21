import slash
import os
import signal
from .utils.suite_writer import Suite
from slash.resuming import get_tests_from_previous_session
from slash.exceptions import InteractiveParallelNotAllowed, ParallelTimeout
from slash.parallel.server import ServerStates
from slash.parallel.parallel_manager import ParallelManager
from slash import Session
from slash.loader import Loader
import time
import tempfile
import pytest

@pytest.fixture(scope='module', autouse=True)
def no_parallel_user_config(request):
    tmpdir = tempfile.mkdtemp()
    path = os.path.join(tmpdir, 'slashrc')
    os.environ["SLASH_USER_SETTINGS"] = path

    @request.addfinalizer
    def cleanup():  # pylint: disable=unused-variable
        os.rmdir(tmpdir)
        del os.environ["SLASH_USER_SETTINGS"]

#basic features of parallel
def run_specific_workers_and_tests_num(workers_num, tests_num=10):
    suite = Suite(debug_info=False, is_parallel=True)
    suite.populate(num_tests=tests_num)
    summary = suite.run(num_workers=workers_num)
    assert len(summary.session.parallel_manager.server.worker_session_ids) == workers_num
    assert summary.session.results.get_num_successful() == tests_num
    assert summary.session.results.is_success()
    return summary

def test_one_worker():
    run_specific_workers_and_tests_num(workers_num=1)

def test_many_workers():
    run_specific_workers_and_tests_num(workers_num=3, tests_num=50)

def test_zero_workers(parallel_suite):
    summary = parallel_suite.run(num_workers=0) #should act like regular run of slash, not parallel
    assert summary.session.results.is_success()
    assert summary.session.parallel_manager is None

def test_test_causes_worker_exit(parallel_suite, config_override):
    config_override("parallel.communication_timeout_secs", 2)
    parallel_suite[0].append_line("import os")
    parallel_suite[0].append_line("os._exit(0)")
    parallel_suite[0].expect_interruption()
    workers_num = 1
    summary = parallel_suite.run(num_workers=workers_num, verify=False)
    assert len(summary.session.parallel_manager.server.worker_session_ids) == workers_num
    [result] = summary.get_all_results_for_test(parallel_suite[0])
    assert result.is_interrupted()

def test_keepalive_works(parallel_suite, config_override):
    config_override("parallel.communication_timeout_secs", 2)
    parallel_suite[0].append_line("import time")
    parallel_suite[0].append_line("time.sleep(6)")
    workers_num = 1
    summary = parallel_suite.run(num_workers=workers_num)
    assert len(summary.session.parallel_manager.server.worker_session_ids) == workers_num
    assert summary.session.results.is_success()

def test_server_fails(parallel_suite):

    @slash.hooks.worker_connected.register  # pylint: disable=no-member, unused-argument
    def simulate_ctrl_c(session_id):  # pylint: disable=unused-variable, unused-argument
        pid = os.getpid()
        os.kill(pid, signal.SIGINT)

    @slash.hooks.session_interrupt.register  # pylint: disable=no-member
    def check_workers_and_server_down():  # pylint: disable=unused-variable
        for worker in slash.context.session.parallel_manager.workers.values():
            ret = worker.poll()
            assert not ret is None
        assert slash.context.session.parallel_manager.server.interrupted
        assert not slash.context.session.parallel_manager.server.finished_tests

    for test in parallel_suite:
        test.expect_deselect()
    parallel_suite.run(expect_interruption=True)


#test slash features with parallel
def test_test_success(parallel_suite):
    results = parallel_suite.run().session.results
    assert results.is_success()
    assert results.get_num_successful() == len(parallel_suite)

def test_test_failure(parallel_suite):
    parallel_suite[0].when_run.fail()
    summary = parallel_suite.run()
    [result] = summary.get_all_results_for_test(parallel_suite[0])
    [failures] = result.get_failures()
    assert 'AssertionError' in str(failures)
    assert 'assert False' in str(failures)

def test_stop_on_error(parallel_suite, parallel_suite_test):
    parallel_suite_test.when_run.fail()
    summary = parallel_suite.run(additional_args=['-x'], verify=False)
    [result] = summary.get_all_results_for_test(parallel_suite_test)
    assert result.is_failure()

    found_failure = False
    for result in summary.session.results:
        if result.is_failure():
            found_failure = True
            continue
        if found_failure:
            assert result.is_not_run()
    assert found_failure

def test_pass_override_conf_flag(parallel_suite):
    summary = parallel_suite.run(additional_args=['-o', 'parallel.server_port=8001'])
    results = summary.session.results
    assert results.is_success()
    assert results.get_num_successful() == len(parallel_suite)
    assert summary.session.parallel_manager.server.port == 8001

def test_test_error(parallel_suite):
    parallel_suite[0].append_line('slash.add_error()')
    parallel_suite[0].expect_error()
    summary = parallel_suite.run()
    [result] = summary.get_all_results_for_test(parallel_suite[0])
    [err] = result.get_errors()
    assert 'RuntimeError' in str(err)
    assert 'add_error() must be called' in str(err)

def test_test_interruption_causes_communication_timeout(parallel_suite, config_override):
    config_override("parallel.communication_timeout_secs", 2)
    parallel_suite[0].when_run.interrupt()
    summary = parallel_suite.run(num_workers=1, verify=False)
    [interrupted_result] = summary.get_all_results_for_test(parallel_suite[0])
    assert interrupted_result.is_interrupted()
    for result in summary.session.results:
        if result != interrupted_result:
            assert result.is_success() or result.is_not_run()

def test_test_interruption_causes_no_requests(parallel_suite, config_override):
    config_override("parallel.no_request_timeout", 2)
    parallel_suite[0].when_run.interrupt()
    summary = parallel_suite.run(num_workers=1, verify=False)
    assert summary.get_all_results_for_test(parallel_suite[0]) == []

def test_test_skips(parallel_suite):
    parallel_suite[0].add_decorator('slash.skipped("reason")')
    parallel_suite[0].expect_skip()
    results = parallel_suite.run().session.results
    assert results.is_success(allow_skips=True)
    assert results.get_num_skipped() == 1
    for result in results:
        if result.is_skip():
            assert 'reason' in result.get_skips()

def test_session_warnings(parallel_suite):
    parallel_suite[0].append_line("import warnings")
    parallel_suite[0].append_line("warnings.warn('message')")
    session_results = parallel_suite.run().session
    assert len(session_results.warnings) == 1
    [w] = session_results.warnings
    assert w.message == 'message'

def test_traceback_vars(parallel_suite):
    #code to be inserted:
        #     def test_traceback_frames():
        #     num = 0
        #     a()
        #
        # def a():
        #     x=1
        #     assert False
    parallel_suite[0].append_line("def a():")
    parallel_suite[0].append_line("   num = 0")
    parallel_suite[0].append_line("   b()")
    parallel_suite[0].append_line("def b():")
    parallel_suite[0].append_line("   x=1")
    parallel_suite[0].append_line("   assert False")
    parallel_suite[0].append_line("a()")
    parallel_suite[0].expect_failure()
    summary = parallel_suite.run(num_workers=1)
    results = summary.session.results
    found_failure = 0
    for result in results:
        if result.is_failure():
            found_failure += 1
            assert len(result.get_failures()) == 1
            assert len(result.get_failures()[0].traceback.frames) == 3
            assert 'x' in result.get_failures()[0].traceback.frames[2].locals
            assert 'num' in result.get_failures()[0].traceback.frames[1].locals
    assert found_failure == 1

def test_result_data_not_picklable(parallel_suite):
    parallel_suite[0].append_line("import socket")
    parallel_suite[0].append_line("s = socket.socket()")
    parallel_suite[0].append_line("slash.context.result.data.setdefault('socket', s)")
    summary = parallel_suite.run()
    [result] = summary.get_all_results_for_test(parallel_suite[0])
    assert result.data == {}

def test_result_data_is_picklable(parallel_suite):
    parallel_suite[0].append_line("slash.context.result.data.setdefault('num', 1)")
    summary = parallel_suite.run()
    [result] = summary.get_all_results_for_test(parallel_suite[0])
    assert 'num' in result.data
    assert result.data['num'] == 1

def test_result_details_not_picklable(parallel_suite):
    parallel_suite[0].append_line("import socket")
    parallel_suite[0].append_line("s = socket.socket()")
    parallel_suite[0].append_line("slash.context.result.details.append('socket', s)")
    summary = parallel_suite.run()
    [result] = summary.get_all_results_for_test(parallel_suite[0])
    assert result.details.all() == {}

def test_result_details_is_picklable(parallel_suite):
    parallel_suite[0].append_line("slash.context.result.details.append('num', 1)")
    summary = parallel_suite.run()
    [result] = summary.get_all_results_for_test(parallel_suite[0])
    details = result.details.all()
    assert 'num' in details
    assert details['num'] == [1]

def test_parameters(parallel_suite):
    parallel_suite[0].add_parameter(num_values=1)
    summary = parallel_suite.run()
    assert summary.session.results.is_success()

def test_requirements(parallel_suite):
    parallel_suite[0].add_decorator('slash.requires(False)')
    parallel_suite[0].expect_skip()
    results = parallel_suite.run().session.results
    assert results.get_num_skipped() == 1
    assert results.get_num_successful() == len(parallel_suite) - 1
    assert results.is_success(allow_skips=True)

def test_is_test_code(parallel_suite):
    parallel_suite[0].when_run.error()
    summary = parallel_suite.run()
    [result] = summary.get_all_results_for_test(parallel_suite[0])
    [err] = result.get_errors()
    assert err.traceback.frames[-1].is_in_test_code()
    error_json = err.traceback.to_list()
    assert error_json[-1]['is_in_test_code']

def test_parallel_resume(parallel_suite):
    parallel_suite[0].when_run.fail()
    result = parallel_suite.run()
    resumed = get_tests_from_previous_session(result.session.id)
    assert len(resumed) == 1

def test_parallel_symlinks(parallel_suite, logs_dir):   # pylint: disable=unused-argument
    files_dir = logs_dir.join("files")
    links_dir = logs_dir.join("links")
    session = parallel_suite.run(additional_args=['-l', str(files_dir)]).session
    session_log_file = files_dir.join(session.id, "session.log")

    assert session.results.is_success()
    assert session_log_file.check()
    assert links_dir.join("last-session").readlink() == session_log_file
    assert links_dir.join("last-session-dir").readlink() == session_log_file.dirname

    worker_session_ids = session.parallel_manager.server.worker_session_ids
    file_names = [x.basename for x in links_dir.join("last-session-dir").listdir()]
    assert 'worker_1' in file_names

    for file_name in links_dir.join("last-session-dir").listdir():
        if file_name.islink() and 'worker' in file_name.basename:
            last_token = file_name.readlink().split('/')[-1]
            assert last_token in worker_session_ids
            assert os.path.isdir(file_name.readlink())

def test_parallel_interactive_fails(parallel_suite):
    summary = parallel_suite.run(additional_args=['-i'], verify=False)
    results = list(summary.session.results.iter_all_results())
    assert len(results) == 1
    error = results[0].get_errors()[0]
    assert error.exception_type == InteractiveParallelNotAllowed

def test_children_session_ids(parallel_suite):
    summary = parallel_suite.run()
    assert summary.session.results.is_success()
    session_ids = summary.session.parallel_manager.server.worker_session_ids
    expected_session_ids = ["{}_1".format(summary.session.id.split('_')[0])]
    assert session_ids == expected_session_ids

def test_timeout_no_request_to_server(config_override, runnable_test_dir):
    config_override("parallel.no_request_timeout", 1)
    with Session():
        runnables = Loader().get_runnables(str(runnable_test_dir))
        parallel_manager = ParallelManager([])
        parallel_manager.start_server_in_thread(runnables)
        parallel_manager.server.state = ServerStates.SERVE_TESTS

        with slash.assert_raises(ParallelTimeout) as caught:
            parallel_manager.start()
        assert 'No request sent to server' in caught.exception.args[0]

def test_children_not_connected_timeout(runnable_test_dir, config_override):
    config_override("parallel.worker_connect_timeout", 0)
    config_override("parallel.num_workers", 1)
    with Session():
        runnables = Loader().get_runnables(str(runnable_test_dir))
        parallel_manager = ParallelManager([])
        parallel_manager.start_server_in_thread(runnables)
        time.sleep(0.1)
        with slash.assert_raises(ParallelTimeout) as caught:
            parallel_manager.wait_all_workers_to_connect()
        assert caught.exception.args[0] == 'Not all clients connected'

def test_worker_error_logs(parallel_suite, config_override):
    config_override("parallel.communication_timeout_secs", 2)
    parallel_suite[0].when_run.interrupt()
    summary = parallel_suite.run(num_workers=1, verify=False)
    [interrupted_result] = summary.get_all_results_for_test(parallel_suite[0])
    assert interrupted_result.is_interrupted()
    for result in summary.session.results:
        if result != interrupted_result:
            assert result.is_success() or result.is_not_run()
    file_path = os.path.join(summary.session.parallel_manager.workers_error_dircetory, 'errors-worker-1.log')
    assert os.path.isfile(file_path)
    with open(file_path) as error_file:
        line = error_file.readline()
        assert 'interrupted' in line
