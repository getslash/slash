class EventRecorder:
    def __init__(self):
        super().__init__()
        self.events = {}
        self.timestamp = 0

    def record(self, event_name, **kwargs):
        assert event_name not in self.events, f"Event {event_name} already recorded"
        self.timestamp += 1
        self.events[event_name] = Event(self.timestamp, kwargs)

    def __getitem__(self, event_name):
        return self.events[event_name]


class Event:
    happened = True

    def __init__(self, timestamp, info):
        super().__init__()
        self.timestamp = timestamp
        self.info = info
