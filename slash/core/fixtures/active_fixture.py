class ActiveFixture(object):

    def __init__(self, fixture):
        super(ActiveFixture, self).__init__()
        self.fixture = fixture
        self.id = fixture.info.id
        self.name = fixture.info.name
        self._cleanups = []

    def add_cleanup(self, cleanup):
        self._cleanups.append(cleanup)

    def do_cleanups(self):
        while self._cleanups:
            cleanup = self._cleanups.pop()
            cleanup()
