class Result(object):
    def __init__(self):
        super(Result, self).__init__()
        self._errors = []
        self._failures = []
        self._skips = []
        self._finished = False
    def is_error(self):
        return bool(self._errors)
    def is_failure(self):
        return bool(self._failures)
    def is_success(self):
        return self._finished and not self._errors and not self._failures and not self._skips
    def is_finished(self):
        return self._finished
    def mark_finished(self):
        self._finished = True
    def add_error(self, e):
        self._errors.append(e)
    def add_failure(self, f):
        self._failures.append(f)
