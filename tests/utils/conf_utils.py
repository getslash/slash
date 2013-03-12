from confetti import Metadata

def Doc(msg):
    return Metadata(doc=msg)

class Cmdline(Metadata):
    pass

