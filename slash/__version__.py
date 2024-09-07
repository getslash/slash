import importlib.metadata

get_distribution = importlib.metadata.distribution

__version__ = get_distribution("slash").version


def get_backslash_client_version():
    try:
        return get_distribution("backslash").version
    except importlib.metadata.PackageNotFoundError:
        return None


__backslash_version__ = get_backslash_client_version()
