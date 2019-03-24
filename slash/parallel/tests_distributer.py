from slash import ctx
from logbook import Logger


_logger = Logger(__name__)

class TestsDistributer(object):
    def __init__(self, num_tests):
        self._unstarted_tests_indices = [i for i in range(num_tests)]
        self._current_tests_index = 0
        workers_config = ctx.session.parallel_manager.workers.values()
        self._workers_excluded_tests = {config.get_worker_id(): config.get_excluded_tests() \
                                        for config in workers_config}
        self._forced_tests_dict = {}
        for config in workers_config:
            for test_index in config.get_forced_tests():
                self._forced_tests_dict[test_index] = config.get_worker_id()
        _logger.debug("forced_tests_dict: {}", self._forced_tests_dict)

    def _can_execute_test(self, test_index, client_id):
        _logger.debug("_can_execute_test - client_id: {}, test_index: {}", client_id, test_index)
        forced_worker = self._forced_tests_dict.get(test_index)
        if forced_worker is not None:
            return forced_worker == client_id
        return test_index not in self._workers_excluded_tests[client_id]

    def get_next_test_for_client(self, client_id):
        ret = None
        for test_index in self._unstarted_tests_indices:
            if self._can_execute_test(test_index, client_id):
                ret = test_index
                break
            else:
                _logger.debug('worker id {} cannot execute test number {}, searching another', client_id, test_index)
        if ret is not None:
            self._unstarted_tests_indices.remove(ret)
        return ret

    def clear_unstarted_tests(self):
        self._unstarted_tests_indices = []

    def get_unstarted_tests(self):
        return list(self._unstarted_tests_indices)

    def has_unstarted_tests(self):
        return len(self._unstarted_tests_indices) > 0
