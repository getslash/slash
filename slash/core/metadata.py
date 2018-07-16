import itertools
import sys

from ..ctx import context
from ..exceptions import SlashInternalError

_sort_key_generator = itertools.count(1)

class Metadata(object):

    """Class representing the metadata associated with a test object. Generally available
    as test.__slash__
    """

    #: The index of the test in the current execution, 0-based
    test_index0 = None

    def __init__(self, factory, test):
        super(Metadata, self).__init__()
        #: The test's unique id
        self.id = None
        self.tags = test.get_tags()
        self._sort_key = next(_sort_key_generator)
        self.repeat_all_index = 0
        if factory is not None:
            #: The path to the file from which this test was loaded
            self.module_name = factory.get_module_name()
            if not self.module_name:
                raise SlashInternalError('Could not find module for {}'.format(test))

            self._file_path = factory.get_filename()
            self.factory_name = factory.get_factory_name()
        else:
            self.module_name = type(test).__module__
            self._file_path = sys.modules[self.module_name].__file__
            self.factory_name = '?'
        self.variation = test.get_variation()
        if self.variation is None:
            raise SlashInternalError('{} has no variations'.format(test))

        self._address_override = None
        #: Address string to identify the test inside the file from which it was loaded
        self.address_in_file = self.factory_name
        self.address_in_factory = test.get_address_in_factory()
        if self.address_in_factory is not None:
            self.address_in_file += self.address_in_factory
        if factory is not None:
            self._class_name = factory.get_class_name()
        else:
            testfunc = test.get_test_function()
            if hasattr(testfunc, '__self__'):
                self._class_name = testfunc.__self__.__class__.__name__
            else:
                self._class_name = None

        self._interactive = False

    def set_file_path(self, file_path):
        self._file_path = file_path

    @property
    def file_path(self):
        return self._file_path

    def get_address(self, raw_params=False):
        """
        String identifying the test, to be used when logging or displaying
        results in the console generally it is composed of the file path and
        the address inside the file

        :param raw_params: If ``True``, emit the full parametrization values are interpolated into the returned
           string
        """
        if self._address_override is not None:
            return self._address_override

        returned = '{}:{}'.format(self.file_path, self.address_in_file)
        if self.variation:
            returned += '({})'.format(
                ', '.join('{}={!r}'.format(key, value) for key, value in self.variation.values.items())
                if raw_params
                else self.variation.safe_repr
            )
        return returned

    address = property(get_address)

    def allocate_id(self):
        if self.id is not None:
            raise SlashInternalError('id field of metadata object should be None, is {}'.format(self.id))
        self.id = context.session.id_space.allocate()

    def set_sort_key(self, key):
        self._sort_key = key

    def get_sort_key(self):
        return self._sort_key

    def set_test_full_name(self, name):
        assert hasattr(self, '_address_override')
        self._address_override = name

    def is_interactive(self):
        return self._interactive

    def mark_interactive(self):
        self._interactive = True
        self.set_sort_key(0)

    @property
    def class_name(self):
        return self._class_name

    @property
    def function_name(self):
        returned = self.address_in_file
        if self._class_name:
            prefix = self._class_name + '.'
            assert returned.startswith(prefix)
            returned = returned[len(prefix):]

        return returned.split('(')[0]

    @property
    def test_index1(self):
        """Same as ``test_index0``, only 1-based
        """
        if self.test_index0 is None:
            return None
        return self.test_index0 + 1

    def __repr__(self):
        return '<{}>'.format(self.address)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.address == other.address
        return False

    def __ne__(self, other):
        return not (self == other)  # pylint: disable=superfluous-parens,unneeded-not

    def __hash__(self):
        return self.address.__hash__()

def ensure_test_metadata(test):
    returned = getattr(test, "__slash__", None)
    if returned is None:
        returned = test.__slash__ = Metadata(None, test)
    return returned
