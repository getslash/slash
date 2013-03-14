class RunnableTest(object):
    """
    This class is meant to serve as a base class to any test that can
    actually be executed by the Shakedown runner.
    """
    __shakedown__ = None
    def run(self):
        """
        This method is meant to be overriden by derived classes to actually
        perform the test logic
        """
        raise NotImplementedError() # pragma: no cover

    def get_canonical_name(self):
        return "{0}.{1}".format(type(self).__module__, type(self).__name__)
    def __repr__(self):
        return repr(self.__shakedown__)
