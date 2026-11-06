import weakref


class GarbageCollectionMarker:
    def mark(self, obj):
        marker = _Marker(obj)
        obj.__marker__ = _MarkerAnchor(marker)
        return marker


class _Marker:
    destroyed = False

    def __init__(self, obj):
        super().__init__()
        self._weakref = weakref.proxy(obj)


class _MarkerAnchor:
    def __init__(self, marker):
        super().__init__()
        self._marker = marker

    def __del__(self):
        self._marker.destroyed = True
