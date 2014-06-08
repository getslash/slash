from slash._compat import iteritems
from slash.parameters import (
    iterate,
    iter_inherited_method_parameter_combinations,
    )

def test_iter_inherited_method_parameter_sets(cartesian):
    class Base(object):

        @iterate(a=cartesian.a.make_set())
        def method(self):
            pass

    class Derived1(Base):
        pass

    class Derived2(Derived1):
        @iterate(b=cartesian.b.make_set(), c=cartesian.c.make_set())
        def method(self):
            pass

    sets = list(iter_inherited_method_parameter_combinations(Derived2, 'method'))
    assert len(sets) == len(cartesian)
