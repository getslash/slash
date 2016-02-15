class ReporterInterface(object):

    def notify_before_console_output(self):
        pass

    def notify_after_console_output(self):
        pass

    def report_before_debugger(self, exc_info):
        pass

    def report_session_start(self, session):
        pass

    def report_session_end(self, session):
        pass

    def report_file_start(self, filename):
        pass

    def report_file_end(self, filename):
        pass

    def report_collection_start(self):
        pass

    def report_test_collected(self, all_tests, test):
        pass

    def report_collection_end(self, collected):
        pass

    def report_test_start(self, test):
        pass

    def report_test_end(self, test, result):
        if result.is_success():
            self.report_test_success(test, result)
        elif result.is_skip():
            self.report_test_skip(test, result)
        elif result.is_error():
            self.report_test_error(test, result)
        elif result.is_interrupted():
            self.report_test_interrupted(test, result)
        else:
            assert result.is_failure()
            self.report_test_failure(test, result)

    def report_test_success(self, test, result):
        pass

    def report_test_skip(self, test, result):
        pass

    def report_test_error(self, test, result):
        pass

    def report_test_failure(self, test, result):
        pass

    def report_test_interrupted(self, test, result):
        pass

    def report_test_error_added(self, test, error):
        pass

    def report_test_failure_added(self, test, error):
        pass

    def report_test_skip_added(self, test, reason):
        pass

    def report_fancy_message(self, headline, message):
        pass

    def report_message(self, message):
        pass

    def report_error_message(self, message):
        pass

