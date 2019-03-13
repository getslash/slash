from ..conf import config
from .. import hooks
import os
import logbook
from ..utils.tmux_utils import create_new_window, create_new_pane
from slash import ctx
import subprocess
import time
import signal
import errno
import sys

_logger = logbook.Logger(__name__)

def is_process_running(pid):
    try:
        os.kill(pid, 0)
    except OSError as err:
        if err.errno == errno.ESRCH:
            return False
        else:
            raise
    return True

class WorkerConfiguration(object):
    def __init__(self, args, worker_id):
        self._worker_id = worker_id
        self.argv = [sys.executable, '-m', 'slash.frontend.main', 'run', '--parallel-parent-session-id', ctx.session.id] + \
                     args + ["--parallel-worker-id", str(worker_id)]
        self._excluded_tests = set()
        self._forced_tests = set()
        self._pid = None

    def get_forced_tests(self):
        return self._forced_tests

    def get_excluded_tests(self):
        return self._excluded_tests

    def get_worker_id(self):
        return self._worker_id

    def _start(self):
        raise NotImplementedError()

    def start(self):
        hooks.before_worker_start(worker_config=self) # pylint: disable=no-member
        _logger.notice("Starting worker number {}", self._worker_id)
        self.argv += ['--parallel-port', str(ctx.session.parallel_manager.server.port),\
                      '--keepalive-port', str(ctx.session.parallel_manager.keepalive_server.port), \
                      '--workers-error-dir', ctx.session.parallel_manager.workers_error_dircetory]
        self._start()

    def kill(self):
        raise NotImplementedError()

    def handle_timeout(self):
        raise NotImplementedError()

    def _test_or_index_to_index(self, test_or_test_index):
        test_index = test_or_test_index.__slash__.parallel_index if hasattr(test_or_test_index, '__slash__') else test_or_test_index
        assert isinstance(test_index, int)
        return test_index

    def exclude_test(self, test_or_test_index):
        """Prevents from the test/test_index to be executed on the specific worker
        """
        test_index = self._test_or_index_to_index(test_or_test_index)
        if test_index in self._forced_tests:
            raise RuntimeError('Cannot exclude test_index {} for client {} since it has been forced before'.format(test_index,
                                                                                                       self._worker_id))
        if test_index in self._excluded_tests:
            _logger.warning('test_index {} already in exclude list for worker {}, not adding it', test_index, self._worker_id)
        else:
            self._excluded_tests.add(test_index)

    def force_test(self, test_or_test_index):
        """Forces the test/test_index to be executed on the specific worker
        """
        test_index = self._test_or_index_to_index(test_or_test_index)
        if test_index in self._excluded_tests:
            raise RuntimeError('Cannot force test_index {} for client {} since it has been excluded before'.format(test_index,
                                                                                                       self._worker_id))
        if test_index in self._forced_tests:
            _logger.warning('test_index {} already in forced list for worker {}, not adding it', test_index, self._worker_id)
        else:
            self._forced_tests.add(test_index)

    def get_pid(self):
        return self._pid

    def is_active(self):
        raise NotImplementedError()

    def wait_to_finish(self):
        raise NotImplementedError()

class ProcessWorkerConfiguration(WorkerConfiguration):
    def _start(self):
        with open(os.devnull, 'w') as devnull:
            self._pid = subprocess.Popen(self.argv, stdin=devnull, stdout=devnull, stderr=devnull)

    def kill(self):
        if self._pid is not None:
            self._pid.send_signal(signal.SIGTERM)

    def handle_timeout(self):
        if self.is_active():
            self._pid.kill()

    def is_active(self):
        return self._pid.poll() is None

    def wait_to_finish(self):
        self._pid.wait()

class TmuxWorkerConfiguration(WorkerConfiguration):
    def __init__(self, basic_args, worker_id):
        super(TmuxWorkerConfiguration, self).__init__(basic_args, worker_id)
        self._window_handle = None

    def _start(self):
        self.argv += [';$SHELL']
        command = ' '.join(self.argv)
        if config.root.tmux.use_panes:
            self._window_handle = create_new_pane(command)
        else:
            self._window_handle = create_new_window("worker {}".format(self._worker_id), command)

    def get_pid(self):
        if self._pid is None:
            self._pid = ctx.session.parallel_manager.server.worker_to_pid.get(self._worker_id)
        return self._pid

    def handle_timeout(self):
        if not config.root.tmux.use_panes:
            self._window_handle.rename_window('stopped_client_{}'.format(self._worker_id))

    def is_active(self):
        return is_process_running(self.get_pid())

    def kill(self):
        try:
            os.kill(self.get_pid(), signal.SIGTERM)
        except OSError as err:
            if err.errno != errno.ESRCH:
                raise

    def wait_to_finish(self):
        for _ in range(10):
            if not self.is_active():
                break
            else:
                time.sleep(0.5)
