import signal
import sys
from contextlib import contextmanager

from . import hooks as trigger_hook
from . import site
from .core.session import Session
from .conf import config
from .exceptions import TerminatedException
from .loader import Loader
from .reporting.console_reporter import ConsoleReporter
from .utils import cli_utils


class Application(object):
    def __init__(self, parser, args, report_stream):
        super(Application, self).__init__()
        self.parser = parser
        self.args = args
        self.report_stream = report_stream
        self.test_loader = Loader()
        self.session = Session(reporter=ConsoleReporter(level=config.root.log.console_level, stream=report_stream), console_stream=report_stream)

    def error(self, message, usage=True):
        if usage:
            self.parser.error(message)
        else:
            sys.exit('Error: {0}'.format(message))

@contextmanager
def get_application_context(parser=None, argv=None, args=(), report_stream=sys.stderr, enable_interactive=False, positionals_metavar=None):
    with _handling_sigterm_context():
        site.load()
        args = list(args)
        if enable_interactive:
            args.append(
                cli_utils.Argument("-i", "--interactive", help="Enter an interactive shell",
                                   action="store_true", default=False)
            )
        with cli_utils.get_cli_environment_context(argv=argv, extra_args=args, positionals_metavar=positionals_metavar) as (parser, parsed_args):
            app = Application(parser=parser, args=parsed_args, report_stream=report_stream)
            _check_unknown_switches(app)
            with app.session:
                yield app
                trigger_hook.result_summary()  # pylint: disable=no-member

def _check_unknown_switches(app):
    unknown = [arg for arg in app.args.positionals if arg.startswith("-")]
    if unknown:
        app.error("Unknown flags: {0}".format(", ".join(unknown)))

@contextmanager
def _handling_sigterm_context():

    def handle_sigterm(*_):
        raise TerminatedException('Terminated by signal')

    prev = signal.signal(signal.SIGTERM, handle_sigterm)
    try:
        yield
    finally:
        signal.signal(signal.SIGTERM, prev)
