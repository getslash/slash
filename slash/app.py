from contextlib import contextmanager
import sys
from . import hooks as trigger_hook
from .loader import Loader
from .core.session import Session
from . import site
from .utils import cli_utils
from .utils.interactive import start_interactive_shell
from .utils.reporter import report_context

class Application(object):
    def __init__(self, parser, args, report_stream):
        super(Application, self).__init__()
        self.parser = parser
        self.args = args
        self.report_stream = report_stream
        self.test_loader = Loader()
        self.session = Session()
    def error(self, *args, **kwargs):
        self.parser.error(*args, **kwargs)

@contextmanager
def get_application_context(parser=None, argv=None, args=(), report_stream=sys.stderr, enable_interactive=False, allow_unknown_args=False):
    site.load()
    args = list(args)
    if enable_interactive:
        args.append(
            cli_utils.Argument("-i", "--interactive", help="Enter an interactive shell",
                               action="store_true", default=False)
        )
    with cli_utils.get_cli_environment_context(argv=argv, extra_args=args, allow_unknown_args=allow_unknown_args) as (parser, parsed_args):
        app = Application(parser=parser, args=parsed_args, report_stream=report_stream)
        with app.session:
            with report_context(app.report_stream):
                if enable_interactive and parsed_args.interactive:
                    start_interactive_shell()
                yield app
            trigger_hook.result_summary()

