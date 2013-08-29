import operator

## utility operators

def safe_isinstance(a, b):
    try:
        return isinstance(a, b)
    except TypeError:
        return False

def safe_not_isinstance(a, b):
    return not safe_isinstance(a, b)

def is_none(x):
    return x is None

def is_not_none(x):
    return x is not None

def not_contains(x, y):
    """
    Python's operator module does not have a function for the ``not in`` operator. That's a shame.
    """
    return y not in x

def is_empty(x):
    return len(x) == 0

def is_not_empty(x):
    return not is_empty(x)

### Operator information
_OPERATORS = {}

def _op(operator_func, operator_token, inverse_func, inverse_token):
    _OPERATORS[operator_func] = Operator(operator_token, operator_func, inverse_func)
    _OPERATORS[inverse_func] = Operator(inverse_token, inverse_func, operator_func)

class Operator(object):
    def __init__(self, template, func, inverse_func):
        super(Operator, self).__init__()
        self.template = template
        self.func = func
        self.inverse_func = inverse_func

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)

    def to_expression(self, *args, **kwargs):
        return self.template.format(*args, **kwargs)

def get_operator_by_func(operator_func):
    return _OPERATORS[operator_func]

### operator declarations
_op(operator.eq, "{0} == {1}", operator.ne, "{0} != {1}")
_op(safe_isinstance, "{0} is instance of {1}", safe_not_isinstance, "{0} is not instance of {1}")
_op(is_none, "{0} is None", is_not_none, "{0} is not None")
_op(operator.is_, "{0} is {1}", operator.is_not, "{0} is not {1}")
_op(operator.truth, "{0} is not false", operator.not_, "{0} is not true")
_op(operator.contains, "{1} in {0}", not_contains, "{1} not in {0}")
_op(is_empty, "{0} is empty", is_not_empty, "{0} is not empty")
