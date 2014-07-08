from slash.utils.formatter import Formatter

class CodeFormatter(Formatter):

    def __init__(self, stream):
        super(CodeFormatter, self).__init__(stream, ' ' * 4)
