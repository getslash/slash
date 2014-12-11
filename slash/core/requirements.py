_SLASH_REQUIRES_KEY_NAME = '__slash_requirements__'


def requires(req, message=None):
    """A decorator specifying that the decorated tests requires a certain precondition in order to run

    :param req: Either a function receiving no arguments and returning a boolean, or a boolean specifying whether or not
       the requirement is met
    """
    def decorator(func):
        reqs = getattr(func, _SLASH_REQUIRES_KEY_NAME, None)
        if reqs is None:
            reqs = []
            setattr(func, _SLASH_REQUIRES_KEY_NAME, reqs)
        reqs.append(Requirement(req, message))
        return func
    return decorator


def get_requirements(test):
    return list(getattr(test, _SLASH_REQUIRES_KEY_NAME, []))


class Requirement(object):

    def __init__(self, req, message=None):
        super(Requirement, self).__init__()
        self._req = req
        self._message = message

    def __repr__(self):
        if self._message is not None:
            return self._message
        return repr(self._req)

    def is_met(self):
        if isinstance(self._req, bool):
            return self._req
        return self._req()
