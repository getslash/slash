import colorama
import functools

class ColorStringBase(object):

    def get_colored(self):
        raise NotImplementedError() # pragma: no cover

    def __repr__(self):
        return repr(str(self))

    def __add__(self, other):
        return ColorCompoundString(self, other)

    def __radd__(self, other):
        return ColorCompoundString(other, self)

class ColorString(ColorStringBase):
    def __init__(self, string, color):
        super(ColorString, self).__init__()
        self._string = string
        self._color = color

    def __len__(self):
        return len(self._string)

    def ljust(self, *args):
        return ColorString(self._string.ljust(*args), self._color)

    @classmethod
    def get_formatter(cls, color):
        return functools.partial(cls, color=color)

    def __mod__(self, values):
        return ColorString(self._string % values, self._color)

    def __str__(self):
        return str(self._string)

    def get_colored(self):
        return "{}{}{}".format(getattr(colorama.Fore, self._color.upper()), self._string, colorama.Fore.RESET) # pylint: disable=no-member

class ColorCompoundString(ColorStringBase):

    def __init__(self, *strings):
        super(ColorCompoundString, self).__init__()
        self._strings = strings

    def __str__(self):
        return ''.join(str(x) for x in  self._strings)

    def __len__(self):
        return sum(len(s) for s in self._strings)

    def ljust(self):
        raise NotImplementedError() # pragma: no cover

    def get_colored(self):
        return ''.join(s.get_colored() if isinstance(s, ColorStringBase) else s for s in self._strings)
