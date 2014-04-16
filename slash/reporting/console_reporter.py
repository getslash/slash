import sys

import logbook


class ConsoleReporter(object):

    def __init__(self, level=logbook.DEBUG, stream=sys.stderr):
        super(ConsoleReporter, self).__init__()
        self._level = level
