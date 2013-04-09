try:
    from IPython import embed # pylint: disable=F0401
except ImportError:
    import code
    def _interact(ns):
        code.interact(local=ns)
else:
    def _interact(ns):
        embed(user_ns=ns)

def start_interactive_shell(**namespace):
    """
    Starts an interactive shell. Uses IPython if available, else fall back
    to the native Python interpreter.

    Any keyword argument specified will be available in the shell ``globals``.
    """
    _interact(namespace)
