from .element import Element


class SuiteWriterTestContainer(Element):

    def __init__(self, suite):
        super(SuiteWriterTestContainer, self).__init__(suite)
        self._tests = []

    @property
    def tests(self):
        return list(self._tests)

    def get_num_tests(self):
        return len(self._tests)
