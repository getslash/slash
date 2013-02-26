class Metadata(object):
    pass

def ensure_shakedown_metadata(thing):
    returned = getattr(thing, "__shakedown__", None)
    if returned is None:
        returned = thing.__shakedown__ = Metadata()
    return returned
