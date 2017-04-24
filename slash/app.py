import logbook
import signal
import sys
from contextlib import contextmanager

from . import hooks as trigger_hook
from . import log
from . import site
from . import plugins
from ._compat import ExitStack
from .conf import config
from .core.session import Session
from .reporting.console_reporter import ConsoleReporter
from .exceptions import TerminatedException, SlashException
from .exception_handling import handling_exceptions
from .loader import Loader
from .log import ConsoleHandler
from .utils import cli_utils
from .utils.debug import debug_if_needed

_logger = logbook.Logger(__name__)


class Application(object):

    def __init__(self):
        super(Application, self).__init__()
        self._test_loader = Loader()
        self.set_report_stream(sys.stderr)
        self._argv = None
        self._reset_parser()
        self._positional_args = None
        self._parsed_args = None
        self._reporter = None
        self.test_loader = Loader()
        self.session = None
        self._working_directory = None
        self._interrupted = False
        self._exit_code = 0

    def set_working_directory(self, path):
        self._working_directory = path

    @property
    def exit_code(self):
        return self._exit_code

    def set_exit_code(self, exit_code):
        self._exit_code = exit_code

    @property
    def interrupted(self):
        return self._interrupted

    @property
    def positional_args(self):
        return self._positional_args

    @property
    def parsed_args(self):
        return self._parsed_args

    def enable_interactive(self):
        self.arg_parser.add_argument(
            '-i', '--interactive', help='Enter an interactive shell',
            action="store_true", default=False)

    def _reset_parser(self):
        self.arg_parser = cli_utils.SlashArgumentParser()

    def set_argv(self, argv):
        self._argv = list(argv)

    def _get_argv(self):
        if self._argv is None:
            return sys.argv[1:]
        return self._argv[:]

    def set_report_stream(self, stream):
        if stream is not None:
            self._report_stream = stream
            self._default_reporter = ConsoleReporter(level=logbook.ERROR, stream=stream)
            self._console_handler = ConsoleHandler(stream=stream, level=logbook.ERROR)

    def set_reporter(self, reporter):
        self._reporter = reporter

    def get_reporter(self):
        returned = self._reporter
        if returned is None:
            returned = ConsoleReporter(
                level=config.root.log.console_level,
                stream=self._report_stream)

        return returned

    def __enter__(self):
        self._exit_stack = ExitStack()
        self._exit_stack.__enter__()
        try:
            self._exit_stack.enter_context(self._prelude_logging_context())
            self._exit_stack.enter_context(self._sigterm_context())
            site.load(working_directory=self._working_directory)

            cli_utils.configure_arg_parser_by_plugins(self.arg_parser)
            cli_utils.configure_arg_parser_by_config(self.arg_parser)
            argv = cli_utils.add_pending_plugins_from_commandline(self._get_argv())

            self._parsed_args, self._positional_args = self.arg_parser.parse_known_args(argv)

            self._exit_stack.enter_context(
                cli_utils.get_modified_configuration_from_args_context(self.arg_parser, self._parsed_args)
                )

            self.session = Session(reporter=self.get_reporter(), console_stream=self._report_stream)

            trigger_hook.configure() # pylint: disable=no-member
            plugins.manager.activate_pending_plugins()
            cli_utils.configure_plugins_from_args(self._parsed_args)


            self._exit_stack.enter_context(self.session)
            self._emit_prelude_logs()
            return self

        except:
            self._emit_prelude_logs()
            self.__exit__(*sys.exc_info())
            raise

    def __exit__(self, exc_type, exc_value, exc_tb):
        exc_info = (exc_type, exc_value, exc_tb)
        debug_if_needed(exc_info)
        if exc_value is not None:
            self._exit_code = exc_value.code if isinstance(exc_value, SystemExit) else -1

        if isinstance(exc_value, SlashException):
            self.get_reporter().report_error_message(str(exc_value))

        elif isinstance(exc_value, Exception):
            _logger.error('Unexpected error occurred', exc_info=exc_info)
            self.get_reporter().report_error_message('Unexpected error: {}'.format(exc_value))

        if isinstance(exc_value, (KeyboardInterrupt, SystemExit, TerminatedException)):
            self._interrupted = True

        if exc_type is not None:
            trigger_hook.result_summary() # pylint: disable=no-member
        self._exit_stack.__exit__(exc_type, exc_value, exc_tb)
        self._exit_stack = None
        self._reset_parser()
        return True

    def _prelude_logging_context(self):
        self._prelude_log_handler = log.RetainedLogHandler(bubble=True, level=logbook.TRACE)
        return self._prelude_log_handler.applicationbound()

    def _emit_prelude_logs(self):
        self._prelude_log_handler.disable()
        handler = None
        if self.session is not None:
            handler = self.session.logging.session_log_handler
        if handler is None:
            handler = self._console_handler
        self._prelude_log_handler.flush_to_handler(handler)

    @contextmanager
    def _sigterm_context(self):
        def handle_sigterm(*_):
            with handling_exceptions():
                raise TerminatedException('Terminated by signal')

        prev = signal.signal(signal.SIGTERM, handle_sigterm)
        try:
            yield
        finally:
            try:
                signal.signal(signal.SIGTERM, prev)
            except TypeError as e:
                #workaround for a strange issue on app cleanup. See https://bugs.python.org/issue23548
                if 'signal handler must be signal.SIG_IGN' not in str(e):
                    raise
