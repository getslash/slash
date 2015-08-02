import gc


def test_gc_marker(gc_marker):

    class Obj(object):
        pass

    obj = Obj()
    marker = gc_marker.mark(obj)
    assert not marker.destroyed
    del obj
    gc.collect()
    assert marker.destroyed
