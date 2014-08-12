class FixtureScopeManager(object):

    def __init__(self, fixture_store):
        super(FixtureScopeManager, self).__init__()
        self._fixture_store = fixture_store
        self._last_module = self._last_test = None

    def begin_test(self, test):
        test_module = test.__slash__.module_name
        if self._last_module is None:
            self._fixture_store.begin_scope('session')
            self._fixture_store.begin_scope('module')
        elif self._last_module != test_module:
            self._fixture_store.begin_scope('module')
        self._last_module = test_module
        self._fixture_store.begin_scope('test')
        self._last_test = test

    def end_test(self, test, next_test):
        assert test == self._last_test
        self._fixture_store.end_scope('test')
        if next_test is None or next_test.__slash__.module_name != self._last_module:
            self._fixture_store.end_scope('module')
        if next_test is None:
            self._fixture_store.end_scope('session')
