import os

from . import pattern_matching

def iter_suite_file_paths(suite_files):
    for filename in suite_files:

        dirname = os.path.abspath(os.path.dirname(filename))
        with open(filename) as suite_file:
            for path in suite_file:
                path = path.strip()
                if not path or path.startswith("#"):
                    continue

                path, matcher, repeat = _parse_path_filter_and_repeat(path)

                if not os.path.isabs(path):
                    path = os.path.abspath(os.path.join(dirname, path))

                if not path.endswith('.py') and '.py:' not in path and not os.path.isdir(path):
                    for p, other_filter in iter_suite_file_paths([path]):
                        yield p, _and_matchers(matcher, other_filter)
                    continue

                for _ in range(repeat):
                    yield path, matcher


def _and_matchers(a, b):
    if a is None:
        return b
    if b is None:
        return a
    return pattern_matching.AndMatching([a, b])


def _parse_path_filter_and_repeat(line):
    if '#' not in line:
        return line, None, 1

    line, remainders = line.split('#', 1)
    line = line.strip()
    remainders = remainders.split(',')

    matcher = None
    repeat = 1
    for remainder in remainders:
        remainder = remainder.strip()
        if remainder.startswith('filter:'):
            matcher = pattern_matching.Matcher(remainder.split(':', 1)[1])
        if remainder.startswith('repeat:'):
            repeat = int(remainder.split(':', 1)[1])
    return line, matcher, repeat
