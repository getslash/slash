from importlib.metadata import distribution, PackageNotFoundError


__version__ = distribution("slash").version


def get_backslash_client_version():
    try:
        return distribution("backslash").version
    except PackageNotFoundError:
        return None


__backslash_version__ = get_backslash_client_version()
