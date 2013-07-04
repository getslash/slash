import traceback

class Error(object):
    def __init__(self, exc_info):
        super(Error, self).__init__()
        self.exception_type, self.exception, tb = exc_info
        self.exception_text = "".join(traceback.format_exception(
            self.exception_type, self.exception, tb
        ))
    def __repr__(self):
        return repr(self.exception)
    def __str__(self):
        return str(self.exception)
