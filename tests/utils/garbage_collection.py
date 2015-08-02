import weakref

class GarbageCollectionMarker(object):

    def mark(self, obj):
        marker = _Marker(obj)
        obj.__marker__ = _MarkerAnchor(marker)
        return marker


class _Marker(object):

    destroyed = False

    def __init__(self, obj):
        super(_Marker, self).__init__()
        self._weakref = weakref.proxy(obj)


class _MarkerAnchor(object):

    def __init__(self, marker):
        super(_MarkerAnchor, self).__init__()
        self._marker = marker

    def __del__(self):
        self._marker.destroyed = True
