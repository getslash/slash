from contextlib import contextmanager
import slash
import py.code  # pylint: disable=no-name-in-module, import-error


def get_code_lines(function):
    source_lines = str(py.code.Code(function).source()).splitlines()  # pylint: disable=no-member
    assert source_lines[0].startswith('@')
    assert source_lines[1].startswith('def ')
    assert source_lines[2][0].isspace()
    lines = str(py.code.Source('\n'.join(source_lines[2:])).deindent()).splitlines() # pylint: disable=no-member
    return lines


@contextmanager
def get_temporary_slashrc_context(new_path=None):
    prev = slash.config.root.run.user_customization_file_path
    slash.config.root.run.user_customization_file_path = new_path
    try:
        yield
    finally:
        slash.config.root.run.user_customization_file_path = prev
