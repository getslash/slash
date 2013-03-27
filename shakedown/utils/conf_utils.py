import itertools
from confetti import Metadata

_dest_generator = ("dest_{0}".format(i) for i in itertools.count())

class _Cmdline(object):
    def __init__(self, arg=None, on=None, off=None):
        super(_Cmdline, self).__init__()
        self.dest = next(_dest_generator)
        self.arg = arg
        self.on = on
        self.off = off

def Cmdline(**kwargs):
    return Metadata(cmdline=_Cmdline(**kwargs))



def Doc(msg):
    return Metadata(doc=msg)


