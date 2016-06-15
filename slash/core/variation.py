from numbers import Number
import string

from .._compat import string_types
from .fixtures.parameters import Parametrization

_PRINTABLE_TYPES = (Number,) + string_types
_PRINTABLE_CHARS = set(string.ascii_letters) | set(string.digits) | set("-_")


class Variation(object):

    """Represents a single variation of parameter points. A variation is merely a mapping of fixture ids to their values.
    This mostly applies for parametrization fixtures. The other fixtures follow since they are either constant
    or indirectly depend on parametrization"""

    def __init__(self, store, param_value_indices, name_bindings=None, verbose_id=None):
        """
        :param name_bindings: dictionary mapping parameter name to its id
        """
        super(Variation, self).__init__()
        self._store = store
        self.param_value_indices = param_value_indices
        self.name_bindings = name_bindings or {}
        self.values = {}
        self.id = self._store.get_variation_id(self)
        self.safe_repr = self._get_safe_repr()
        self.verbose_id = verbose_id

    def _get_safe_repr(self):
        returned = {}
        for name, f in self.name_bindings.items():
            if isinstance(f, Parametrization):
                returned[name] = self._format_parameter_safe(name, f)
            else:
                returned[name] = '{}{}'.format(name, self.id[name])
        return ','.join('{}={}'.format(key, returned[key]) for key in sorted(returned))

    def _format_parameter_safe(self, name, p):
        param_index = self.param_value_indices[p.info.id]
        value = str(self._store.get_value(self, p))
        if self._is_printable(value):
            return str(value)
        return '{}{}'.format(name, param_index)

    def _is_printable(self, value):
        if not isinstance(value, _PRINTABLE_TYPES):
            return False
        return _PRINTABLE_CHARS.issuperset(value)

    def has_value_for_parameter(self, param_id):
        return param_id in self.param_value_indices

    def populate_early_known_values(self):
        for name, param in self.name_bindings.items():
            if isinstance(param, Parametrization):
                self.values[name] = self._store.get_value(self, param)

    def populate_values(self):
        for name, param in self.name_bindings.items():
            if name not in self.values:
                self.values[name] = self._store.get_value(self, param)

    def forget_values(self):
        self.values.clear()

    def get_param_value(self, param):
        return self._store.get_value(self, param)

    def __eq__(self, other):
        if isinstance(other, Variation):
            other = other.param_value_indices
        if not isinstance(other, dict):
            return NotImplemented
        return self.param_value_indices == other

    def __ne__(self, other):
        return not (self == other)  # pylint: disable=superfluous-parens,unneeded-not

    def __repr__(self):
        return 'Variation({0})'.format(', '.join('{0}={1}'.format(key, value) for key, value in self.param_value_indices.items()))

    def __nonzero__(self):
        return bool(self.param_value_indices)

    __bool__ = __nonzero__
