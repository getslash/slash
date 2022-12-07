# pylint: disable=unused-argument,redefined-outer-name
import functools
import os
import sys

import logbook
import brotli
import gzip
import gossip
import pytest
import slash

from .utils import run_tests_assert_success, run_tests_in_session, TestCase, make_runnable_tests
from .utils.suite_writer import Suite

def test_console_format(suite, suite_test, config_override, tmpdir):
    config_override('log.format', 'file: {record.message}')
    config_override('log.console_format', 'console: {record.message}')
    config_override('log.root', str(tmpdir))
    suite_test.append_line('slash.logger.error("message here")')
    summary = suite.run(additional_args=['-vvv'])

    assert 'console: message here' in summary.get_console_output()

    [result] = summary.get_all_results_for_test(suite_test)
    with open(result.get_log_path()) as f:
        assert 'file: message here' in f.read()


@pytest.mark.parametrize('should_consider_error', [True, False])
def test_add_error_for_error_log_level(tmpdir, should_consider_error, config_override, test_handler):
    message = 'Hello'
    non_capture_message = 'Do not capture as error'
    test_handler.level = logbook.ERROR
    config_override('log.root', str(tmpdir))
    config_override('run.capture.error_logs_as_errors', should_consider_error)
    def test_with_log_error():
        logger = logbook.Logger('some-logger')
        logger.error(message)
        logger.error(non_capture_message, extra={'capture': False})
    with slash.Session() as session:
        with session.get_started_context():
            slash.runner.run_tests(make_runnable_tests(test_with_log_error))
    [result] = [res for res in session.results.iter_all_results() if not res.is_global_result()]
    expected_error_messages = [message] if should_consider_error else []
    assert [res.message for res in result.get_errors()] == expected_error_messages
    assert [rec.message for rec in test_handler.records] == [message, non_capture_message]

@pytest.mark.skipif(sys.platform == 'win32', reason="does not run on windows")
def test_last_session_symlinks(files_dir, links_dir, session):

    test_log_file = files_dir.join(
        session.id, list(session.results.iter_test_results())[-1].test_metadata.id, "debug.log")
    assert test_log_file.check()
    session_log_file = files_dir.join(session.id, "session.log")
    assert session_log_file.check()

    assert links_dir.join("last-session").readlink() == session_log_file
    assert links_dir.join("last-session-dir").readlink() == session_log_file.dirname
    assert links_dir.join("last-test").readlink() == test_log_file


def test_global_result_get_log_path(files_dir, suite):
    summary = suite.run()
    assert summary.session.results.global_result.get_log_path() is not None
    assert summary.session.results.global_result.get_log_path().startswith(str(files_dir))

def _decompress(input_file_name, use_gzip=True):
    if use_gzip:
        with gzip.open(input_file_name, 'rb') as in_f:
            return in_f.read().decode()
    else:
        with open(input_file_name, 'rb') as in_f:
            return brotli.decompress(in_f.read()).decode()

@pytest.mark.parametrize('compression_enabled', [True, False])
@pytest.mark.parametrize('compression_method', ['gzip', 'brotli'])
@pytest.mark.parametrize('use_rotating_raw_file', [True, False])
def test_logs_compression(files_dir, suite, config_override, compression_enabled, compression_method, use_rotating_raw_file):
    config_override("log.compression.enabled", compression_enabled)
    config_override("log.compression.algorithm", compression_method)
    config_override("log.compression.use_rotating_raw_file", use_rotating_raw_file)
    summary = suite.run()
    session_log_path = summary.session.results.global_result.get_log_path()

    if compression_enabled:
        #validate file names
        if compression_method == "gzip":
            session_log_path.endswith("gz")
        else:
            assert session_log_path.endswith(".br")

        assert summary.session.results.global_result.get_log_path().startswith(str(files_dir))

        raw_file_name = session_log_path[:session_log_path.rfind(".")]
        if use_rotating_raw_file:
            assert os.path.exists(raw_file_name)
        else:
            assert not os.path.exists(raw_file_name)

        #validate compressing successfully
        if use_rotating_raw_file:
            decompressed_logs = _decompress(session_log_path, compression_method == "gzip")
            with open(raw_file_name, 'r') as raw_file:
                assert decompressed_logs.endswith(raw_file.read())
    else:
        assert session_log_path.endswith(".log")

def test_compressing_to_unified_file(files_dir, suite, config_override):
    config_override("log.compression.enabled", True)
    config_override("log.subpath", slash.config.root.log.session_subpath)
    config_override("log.compression.use_rotating_raw_file", True)
    config_override("log.compression.algorithm", "gzip")
    summary = suite.run()
    session_log_path = summary.session.results.global_result.get_log_path()

    raw_file_name = session_log_path[:session_log_path.rfind(".")]
    assert os.path.exists(raw_file_name)

    #validate compressing successfully
    decompressed_logs = _decompress(session_log_path, use_gzip=True)
    with open(raw_file_name, 'r') as raw_file:
        assert decompressed_logs.endswith(raw_file.read())

def test_log_file_colorize(files_dir, config_override, suite, suite_test):
    config_override('log.colorize', True)
    suite_test.append_line('slash.logger.notice("hey")')
    summary = suite.run()
    logfiles = [
        summary.session.results.global_result.get_log_path(),
        summary.get_all_results_for_test(suite_test)[0].get_log_path(),
    ]
    for logfile in logfiles:
        with open(logfile, 'rb') as f:
            log_data = f.read()

        assert b'\x1b[' in log_data


@pytest.mark.parametrize('level', ['info', 'notice', 'warning'])
@pytest.mark.parametrize('log_char', ['a', b'a'])
def test_console_truncation_does_not_truncate_files(files_dir, suite, suite_test, config_override, level, log_char):
    assert slash.config.root.log.truncate_console_lines

    long_string = log_char * 1000
    suite_test.append_line('slash.logger.{level}({msg!r})'.format(msg=long_string, level=level))
    summary = suite.run()
    [result] = summary.get_all_results_for_test(suite_test)
    with open(result.get_log_path()) as logfile:
        logfile_data = logfile.read()
        assert str(long_string) in logfile_data


@pytest.mark.parametrize('symlink_name', ['last_session_symlink', 'last_session_dir_symlink', 'last_failed_symlink'])
def test_log_symlinks_without_root_path(suite, config_override, symlink_name):
    config_override('log.{}'.format(symlink_name), 'some/subdir')
    assert suite.run().ok()

@pytest.mark.skipif(sys.platform == 'win32', reason="does not run on windows")
def test_last_test_not_overriden_by_stop_on_error(links_dir, suite):
    failed_test = suite[4]
    failed_test.when_run.fail()
    # we stop on error...
    for test in suite[5:]:
        test.expect_not_run()
    summary = suite.run(additional_args=['-x'])

    [failed_result] = summary.get_all_results_for_test(failed_test)

    for link_name in ('last-test', 'last-failed'):
        assert links_dir.join(link_name).readlink() == failed_result.get_log_path()


def test_last_test_delete_log_file(links_dir, suite, suite_test):
    os.makedirs(str(links_dir))
    temp_file = os.path.abspath(str(links_dir.join('somepath')))
    with open(temp_file, 'w'):
        pass
    os.symlink(temp_file, str(links_dir.join('last-test')))
    os.unlink(temp_file)

    assert not os.path.exists(str(links_dir.join('last-test')))
    assert os.path.islink(str(links_dir.join('last-test')))

    summary = suite.run()
    with open(summary.session.results.global_result.get_log_path()) as f:
        assert 'OSError: ' not in f.read()
    # assert links_dir.join('last-test').readlink() == list(summary.session.results)[-1].get_log_path()


def test_result_log_links(files_dir, session):

    for result in session.results.iter_test_results():
        assert result.get_log_path() is not None
        assert result.get_log_path().startswith(str(files_dir))

@pytest.mark.skipif(sys.platform == 'win32', reason="does not run on windows")
def test_last_failed(suite, links_dir):
    suite[-5].when_run.fail()
    last_failed = suite[-2]
    last_failed.when_run.fail()
    summary = suite.run()

    [result] = summary.get_all_results_for_test(last_failed)
    fail_log = result.get_log_path()
    assert os.path.isfile(fail_log)
    assert links_dir.join('last-failed').readlink() == fail_log


def test_errors_log_for_test(suite, suite_test, errors_log_path, logs_dir):
    suite_test.when_run.fail()
    res = suite.run()[suite_test]
    with errors_log_path.open() as f:
        lines = [l for l in f.read().splitlines() if 'NOTICE' not in l]
        error_line = lines[0]
    assert 'Error added' in error_line
    with open(res.get_log_path()) as f:
        lines = f.read().splitlines()
        assert error_line in lines

@pytest.mark.skipif(sys.platform == 'win32', reason="does not run on windows")
@pytest.mark.parametrize('should_keep_failed_tests', [True, False])
def test_logs_deletion(suite, suite_test, errors_log_path, logs_dir, config_override, should_keep_failed_tests):
    config_override('log.cleanup.enabled', True)
    config_override('log.cleanup.keep_failed', should_keep_failed_tests)

    suite_test.when_run.fail()
    summary = suite.run()
    remaining_files = []
    logs_files_dir = os.path.join(str(logs_dir), 'files')
    for dirname, _, files in os.walk(str(logs_dir)):
        for filename in files:
            f = os.path.join(dirname, filename)
            if os.path.isfile(f) and not os.path.islink(f):
                remaining_files.append(f)
    if should_keep_failed_tests:
        for file_path in [summary[suite_test].get_log_path(), summary.session.results.global_result.get_log_path()]:
            assert file_path in remaining_files
        assert os.listdir(logs_files_dir)
    else:
        assert len(remaining_files) == 0   # pylint: disable=len-as-condition
        assert not os.listdir(logs_files_dir)

def test_errors_log_for_session(suite, errors_log_path, request, logs_dir):
    @gossip.register('slash.session_start')
    def on_session_start():
        try:
            1/0                     # pylint: disable=pointless-statement
        except ZeroDivisionError:
            slash.add_error()

    request.addfinalizer(on_session_start.gossip.unregister)
    results = suite.run(expect_session_errors=True).session.results
    assert len(results.global_result.get_errors()) == 1
    with errors_log_path.open() as f:
        lines = [l for l in f.read().splitlines() if 'NOTICE' not in l]
        assert 'Error added' in lines[0]

    with open(results.global_result.get_log_path()) as f:
        assert lines[0] in f.read().splitlines()


@pytest.mark.parametrize('level', ['info', 'error'])
@pytest.mark.parametrize('core_log_level', [logbook.WARNING, logbook.TRACE])
def test_filtering_slash_logs(files_dir, config_override, level, core_log_level):
    config_override('log.core_log_level', core_log_level)
    assert slash.config.root.log.truncate_console_lines

    suite = Suite()
    suite_test = suite.add_test(type='function')
    long_string = 'a' * 1000
    suite_test.append_line('slash.logger.{level}({msg!r})'.format(msg=long_string, level=level))
    summary = suite.run()
    result = summary.get_all_results_for_test(suite_test)[0]

    with open(result.get_log_path()) as logfile:
        logfile_data = logfile.read()
        assert long_string in logfile_data

    debug_core_string = 'slash.loader: Checking'
    debug_bypass_string = 'slash.runner: #'
    with open(summary.session.results.global_result.get_log_path()) as logfile:
        logfile_data = logfile.read()
        assert debug_bypass_string in logfile_data
        if core_log_level == logbook.TRACE:
            assert debug_core_string in logfile_data
        else:
            assert debug_core_string not in logfile_data

def test_log_names_with_timestamps(files_dir, config_override, suite):
    config_override('log.core_log_level', logbook.TRACE)
    config_override('log.session_subpath', '{timestamp:%Y-%m-%d-%H%M%S}/session.log')
    config_override('log.subpath', '{timestamp:%Y-%m-%d-%H%M%S}/test.log')
    suite.run()


@pytest.mark.parametrize('raw_values', [True, False])
def test_show_raw_param_values(suite_builder, raw_values, config_override, unified_session_log_path):
    config_override('log.show_raw_param_values', raw_values)


    # pylint: disable=unused-variable
    @suite_builder.first_file.add_code
    def __code__():
        import slash # pylint: disable=redefined-outer-name, reimported


        @slash.parametrize('param', [object()])
        def test_1(param):
            pass

    res = suite_builder.build().run().assert_success(1).slash_app.session.results
    with unified_session_log_path.open() as f:
        log_text = f.read()


    raw_log = 'param=<object object at 0x'

    if raw_values:
        assert raw_log in log_text
    else:
        assert 'test_1(param=param0)' in log_text
        assert raw_log not in log_text


################################################################################
## Fixtures

@pytest.fixture
def unified_session_log_path(logs_dir, config_override):
    config_override('log.root', str(logs_dir))
    config_override('log.session_subpath', 'session.log')
    config_override('log.unified_session_log', True)
    return logs_dir.join('session.log')


@pytest.fixture(autouse=True)
def override_log_level(config_override):
    config_override('log.core_log_level', logbook.TRACE)


@pytest.fixture
def session():
    session = run_tests_assert_success(SampleTest)
    return session


@pytest.fixture
def errors_log_path(request, config_override, tmpdir, logs_dir):
    subpath = 'subdir/errors.log'
    config_override('log.highlights_subpath', subpath)
    return logs_dir.join('files').join(subpath)


@pytest.fixture
def links_dir(logs_dir):
    return logs_dir.join("links")


@pytest.fixture
def files_dir(logs_dir):
    return logs_dir.join("files")


_TOKEN = "logging-test"
_SESSION_START_MARK = "session-start-mark"
_SESSION_END_MARK = "session-end-mark"

_silenced_logger = logbook.Logger("silenced_logger")


################################################################################
## Legacy Tests


class LogFormattingTest(TestCase):

    def setUp(self):
        super(LogFormattingTest, self).setUp()
        self.log_path = self.get_new_path()
        self.override_config(
            "log.root", self.log_path
        )
        self.override_config(
            "log.format", "-- {record.message} --"
        )
        self.override_config("log.subpath", "debug.log")

    def test(self):
        self.session = run_tests_assert_success(SampleTest)
        with open(os.path.join(self.log_path, "debug.log")) as logfile:
            for line in logfile:
                self.assertTrue(line.startswith("-- "))
                self.assertTrue(line.endswith(" --\n"))


class LoggingTest(TestCase):

    def test(self):
        self.log_path = self.get_new_path()
        self.override_config(
            "log.root",
            self.log_path,
        )
        self.override_config(
            "log.subpath",
            os.path.join("{context.session.id}",
                         "{context.test.__slash__.test_index0:03}-{context.test_id}", "debug.log")
        )
        self.override_config(
            "log.session_subpath",
            os.path.join("{context.session.id}", "debug.log")
        )
        self.override_config(
            "log.silence_loggers",
            [_silenced_logger.name]
        )

        self.addCleanup(gossip.unregister_token, _TOKEN)
        slash.hooks.session_start.register(  # pylint: disable=no-member
            functools.partial(_mark, _SESSION_START_MARK), token=_TOKEN)

        slash.hooks.session_end.register(  # pylint: disable=no-member
            functools.partial(_mark, _SESSION_END_MARK), token=_TOKEN)
        self.addCleanup(gossip.unregister_token, _TOKEN)

        self.session = run_tests_assert_success(SampleTest)
        self.tests_metadata = [
            result.test_metadata for result in self.session.results.iter_test_results()]
        self._test_all_run()
        self._test_test_logs_written()
        self._test_session_logs()
        self._test_no_silenced_logger_records()

    def _test_all_run(self):
        methods = [
            method_name for method_name in dir(SampleTest)
            if method_name.startswith("test")
        ]
        self.assertTrue(methods)
        self.assertEqual(len(self.tests_metadata), len(methods))

    def _test_test_logs_written(self):
        for test_metadata in self.tests_metadata:
            test_dir = "{:03}-{}".format(test_metadata.test_index0, test_metadata.id)
            log_path = os.path.join(
                self.log_path, self.session.id, test_dir, "debug.log")
            with open(log_path) as f:
                data = f.read()
            for other_test in self.tests_metadata:
                if other_test.id != test_metadata.id:
                    self.assertNotIn(other_test.id, data)
            self.assertNotIn(_SESSION_START_MARK, data)
            self.assertNotIn(_SESSION_END_MARK, data)

    def _test_session_logs(self):
        with open(os.path.join(self.log_path, self.session.id, "debug.log")) as f:
            data = f.read()
        self.assertIn(_SESSION_START_MARK, data)
        self.assertIn(_SESSION_END_MARK, data)
        for test_id in (t.id for t in self.tests_metadata):
            self.assertNotIn(test_id, data)

    def _test_no_silenced_logger_records(self):
        for path, _, filenames in os.walk(self.log_path):
            for filename in filenames:
                assert filename.endswith(".log")
                filename = os.path.join(path, filename)
                with open(filename) as f:
                    assert _silenced_logger.name not in f.read(
                    ), "Silenced logs appear in log file {}".format(filename)


class ExtraLoggersTest(TestCase):

    def setUp(self):
        super(ExtraLoggersTest, self).setUp()
        self.session = slash.Session()
        self.handler = logbook.TestHandler()
        self.addCleanup(slash.log.remove_all_extra_handlers)
        slash.log.add_log_handler(self.handler)

    def test(self):
        with self.session:
            run_tests_in_session(SampleTest, session=self.session)
        for test_result in self.session.results.iter_test_results():
            for record in self.handler.records:
                if test_result.test_id in record.message:
                    break
            else:
                self.fail(
                    "Test id {} does not appear in logger".format(test_result.test_id))


class SampleTest(slash.Test):

    def test_1(self):
        _mark()

    def test_2(self):
        _silenced_logger.error("error")
        _silenced_logger.info("info")
        _silenced_logger.debug("debug")
        _mark()


def _mark(text=None):
    if text is None:
        text = slash.context.test_id
    slash.logger.debug(text)


class TestLocaltimeLogging(TestCase):

    def setUp(self):
        super(TestLocaltimeLogging, self).setUp()
        self.assertFalse(slash.config.root.log.localtime)
        self.path = self.get_new_path()
        self.override_config(
            "log.localtime", True)
        self.override_config(
            "log.root", self.path)

    def test_local_time(self):
        with slash.Session() as session:  # pylint: disable=unused-variable
            slash.logger.info("Hello")
        self.assertNotEqual(os.listdir(self.path), [])
