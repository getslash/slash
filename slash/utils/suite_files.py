import os

def iter_suite_file_paths(suite_files):
    for filename in suite_files:

        dirname = os.path.abspath(os.path.dirname(filename))
        for path in open(filename):
            path = path.strip()
            if not path or path.startswith("#"):
                continue

            if not os.path.isabs(path):
                path = os.path.abspath(os.path.join(dirname, path))

            if not path.endswith('.py') and '.py:' not in path and not os.path.isdir(path):
                for p in iter_suite_file_paths([path]):
                    yield p
                continue

            yield path
