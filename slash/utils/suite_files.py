import os

from . import pattern_matching

def iter_suite_file_paths(suite_files):
    for filename in suite_files:

        dirname = os.path.abspath(os.path.dirname(filename))
        for path in open(filename):
            path = path.strip()
            if not path or path.startswith("#"):
                continue

            path, filter = _parse_path_and_filter(path)

            if not os.path.isabs(path):
                path = os.path.abspath(os.path.join(dirname, path))

            if not path.endswith('.py') and '.py:' not in path and not os.path.isdir(path):
                for p, other_filter in iter_suite_file_paths([path]):
                    yield p, _and_matchers(filter, other_filter)
                continue

            yield path, filter


def _and_matchers(a, b):
    if a is None:
        return b
    if b is None:
        return a
    return pattern_matching.AndMatching([a, b])


def _parse_path_and_filter(line):
    if '#' not in line:
        return line, None

    line, remainder = line.split('#', 1)
    line = line.strip()
    remainder = remainder.strip()
    if not remainder.startswith('filter:'):
        return line, None
    return line, pattern_matching.Matcher(remainder.split(':', 1)[1])
