from .tagging import NO_TAGS

class RunnableTest(object):

    """
    This class is meant to serve as a base class to any test that can
    actually be executed by the Slash runner.
    """
    __slash__ = None

    def run(self):
        """
        This method is meant to be overriden by derived classes to actually
        perform the test logic
        """
        raise NotImplementedError()  # pragma: no cover

    def get_tags(self):
        return NO_TAGS

    def get_unmet_requirements(self):
        return [r for r in self.get_requirements() if not r.is_met()]

    def get_requirements(self):
        raise NotImplementedError() # pragma: no cover

    def get_required_fixture_objects(self):
        raise NotImplementedError() # pragma: no cover

    def __repr__(self):
        return '<Runnable test {0!r}>'.format(self.__slash__)
