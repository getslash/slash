class EventRecorder(object):
    def __init__(self):
        super(EventRecorder, self).__init__()
        self.events = {}
        self.timestamp = 0
    def record(self, event_name, **kwargs):
        assert event_name not in self.events, "Event {0} already recorded".format(event_name)
        self.timestamp += 1
        self.events[event_name] = Event(self.timestamp, kwargs)
    def __getitem__(self, event_name):
        return self.events[event_name]

class Event(object):
    happened = True
    def __init__(self, timestamp, info):
        super(Event, self).__init__()
        self.timestamp = timestamp
        self.info = info
