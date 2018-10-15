import pkg_resources

__version__ = pkg_resources.get_distribution('slash').version

def get_backslash_client_version():
    try:
        return pkg_resources.get_distribution('backslash').version
    except pkg_resources.DistributionNotFound:
        return None

__backslash_version__ = get_backslash_client_version()
