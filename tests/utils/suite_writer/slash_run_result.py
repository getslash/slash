import copy
import itertools

import logbook

import slash

from .validation import get_test_id_from_test_address

_timestamps = itertools.count()

_logger = logbook.Logger(__name__)


class SlashRunResult(object):

    _console_output = None

    def __init__(self, report_stream):
        super(SlashRunResult, self).__init__()
        self._report_stream = report_stream
        self.exit_code = 0
        self.error_message = None
        self.session = None
        self.tracker = Tracker()

    @property
    def events(self):
        return self.tracker.events

    def ok(self):
        return self.session.results.is_success()

    def get_console_output(self):
        if self._console_output is None:
            self._console_output = self._report_stream.getvalue()
        return self._console_output

    def get_all_results_for_test(self, test):
        returned = []
        for result in self.session.results:
            if get_test_id_from_test_address(result.test_metadata.address) == test.id:
                returned.append(result)
        return returned

    def __getitem__(self, test):
        matching = self.get_all_results_for_test(test)
        assert len(matching) == 1
        return matching[0]

    def __repr__(self):
        return '<Summary ({})>'.format(self.session.results)


class Tracker(object):

    def __init__(self):
        super(Tracker, self).__init__()
        self.events = Events()
        self.active_fixtures = {}

    def notify_fixture_start(self, f_id, value):
        _logger.debug('started fixture {}', f_id)
        assert f_id not in self.active_fixtures
        self.active_fixtures[f_id] = value

    def notify_fixture_end(self, f_id):
        _logger.debug('ended fixture {}', f_id)
        self.active_fixtures.pop(f_id)

    def notify_parameter_value(self, p_id, value):
        slash.context.result.data.setdefault('param_values', {})[p_id] = value

    def get_fixture_memento(self):
        return copy.deepcopy(self.active_fixtures)


class Event(object):

    def __init__(self, args):
        super(Event, self).__init__()
        self.args = args
        self.timestamp = next(_timestamps)

    def is_before(self, other_event):
        return self.timestamp < other_event.timestamp

    def __repr__(self):
        return '<Event #{}: {}>'.format(self.timestamp, self.args)


class Events(object):

    def __init__(self):
        super(Events, self).__init__()
        self._events = []
        self._events_by_args = {}

    def add(self, *args):
        self._events.append(Event(args))
        self._events_by_args[args] = self._events[-1]

    def assert_consecutive(self, evts):
        seq = [self[x] for x in evts]
        timestamps = [e.timestamp for e in seq]
        begin = seq[0].timestamp
        assert timestamps == [begin + i for i in range(len(seq))]

    def __getitem__(self, args):
        return self._events_by_args[self._normalize_key(args)]

    def __contains__(self, args):
        return self._normalize_key(args) in self._events_by_args
        # return self.has_event(*args)

    def has_event(self, *args):
        return args in self

    def _normalize_key(self, args):
        if not isinstance(args, tuple):
            args = (args,)
        return args

    def __repr__(self):
        return '<Events>'
