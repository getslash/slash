import sys
from contextlib import contextmanager

import logbook

from . import hooks
from . import log
from ._compat import ExitStack
from .conf import config
from .ctx import context
from .exception_handling import handling_exceptions
from .exceptions import NoActiveSession, SkipTest, INTERRUPTION_EXCEPTIONS
from .core.function_test import FunctionTest
from .core.metadata import ensure_test_metadata
from .utils.interactive import notify_if_slow_context
from .utils.iteration import PeekableIterator


_logger = logbook.Logger(__name__)
log.set_log_color(_logger.name, logbook.NOTICE, 'blue')


def run_tests(iterable, stop_on_error=None):
    """
    Runs tests from an iterable using the current session
    """
    # pylint: disable=maybe-no-member
    if context.session is None or not context.session.started:
        raise NoActiveSession("A session is not currently started")

    if stop_on_error is None:
        stop_on_error = config.root.run.stop_on_error

    test_iterator = PeekableIterator(iterable)
    last_filename = None
    complete = False
    try:
        for test in test_iterator:
            _set_test_metadata(test)
            test_filename = test.__slash__.file_path
            if last_filename != test_filename:
                context.session.reporter.report_file_start(test_filename)
                last_filename = test_filename
            context.session.reporter.report_test_start(test)
            _logger.notice("{0}", test.__slash__.address)

            _run_single_test(test, test_iterator)


            result = context.session.results[test]
            context.session.reporter.report_test_end(test, result)
            if not test_iterator.has_next() or ensure_test_metadata(test_iterator.peek()).file_path != last_filename:
                context.session.reporter.report_file_end(last_filename)
            if result.has_fatal_exception():
                _logger.debug("Stopping on fatal exception")
                break
            if not result.is_success(allow_skips=True) and stop_on_error:
                _logger.debug("Stopping (run.stop_on_error==True)")
                break
        else:
            complete = True
    finally:
        context.session.scope_manager.flush_remaining_scopes(
            in_failure=not complete, in_interruption=context.session.results.is_interrupted())

    _mark_unrun_tests(test_iterator)
    if complete:
        context.session.mark_complete()
    elif last_filename is not None:
        context.session.reporter.report_file_end(last_filename)
    _logger.trace('Session finished. is_success={0} has_skips={1}',
                  context.session.results.is_success(allow_skips=True), bool(context.session.results.get_num_skipped()))


def _run_single_test(test, test_iterator):
    run_state = {'exc_info': (None, None, None)}
    with ExitStack() as exit_stack:

        # sets the current result, test id etc.
        result = exit_stack.enter_context(_get_test_context(test))

        with handling_exceptions():

            if not _check_test_requirements(test):
                _logger.debug('Requirements not met for {0}. Not running', test)
                return

            result.mark_started()
            try:
                try:
                    with handling_exceptions(swallow=True):
                        context.session.scope_manager.begin_test(test)
                        try:
                            hooks.test_start() # pylint: disable=no-member
                            with handling_exceptions(swallow=True):
                                try:
                                    test.run()
                                except:
                                    run_state['exc_info'] = sys.exc_info()
                                    raise
                        finally:
                            context.session.scope_manager.end_test(
                                test,
                                next_test=test_iterator.peek_or_none(),
                                exc_info=run_state['exc_info'])
                except SkipTest:
                    pass
                _fire_test_summary_hooks(test, result)
            except SkipTest:
                pass
            except INTERRUPTION_EXCEPTIONS:
                with notify_if_slow_context(message="Cleaning up due to interrupt. Please wait..."):
                    hooks.test_interrupt() # pylint: disable=no-member
                raise
            finally:
                result.mark_finished()



def _fire_test_summary_hooks(test, result): # pylint: disable=unused-argument
    with handling_exceptions():
        try:
            if result.is_just_failure():
                hooks.test_failure()  # pylint: disable=no-member
            elif result.is_skip():
                hooks.test_skip(reason=result.get_skips()[0]) # pylint: disable=no-member
            elif result.is_success():
                hooks.test_success()  # pylint: disable=no-member
            else:
                _logger.debug('Firing test_error hook for {0} (result: {1})', test, result)
                hooks.test_error()  # pylint: disable=no-member

        finally:
            hooks.test_end()  # pylint: disable=no-member


def _set_test_metadata(test):
    ensure_test_metadata(test)
    assert test.__slash__.test_index0 is None
    test.__slash__.test_index0 = next(context.session.test_index_counter)


def _mark_unrun_tests(test_iterator):
    remaining = list(test_iterator)
    for test in remaining:
        with _get_test_context(test, logging=False):
            pass


def _check_test_requirements(test):
    unmet_reqs = test.get_unmet_requirements()
    if unmet_reqs:
        context.result.add_skip('Unmet requirements: {0}'.format(unmet_reqs))
        return False
    return True


@contextmanager
def _get_test_context(test, logging=True):
    ensure_test_metadata(test)

    assert test.__slash__.id is None
    test.__slash__.id = context.session.id_space.allocate()
    with _set_current_test_context(test):
        result = context.session.results.create_result(test)
        prev_result = context.result
        context.result = result
        try:
            with (context.session.logging.get_test_logging_context() if logging else ExitStack()):
                _logger.debug("Started test: {0}", test)
                yield result
        finally:
            context.result = prev_result

@contextmanager
def _set_current_test_context(test):
    prev_test = context.test
    prev_test_id = context.test_id
    context.test = test
    context.test_id = test.__slash__.id
    if isinstance(test, FunctionTest):
        context.test_classname = None
        context.test_methodname = test.__slash__.factory_name
    else:
        context.test_classname = test.__slash__.factory_name
        # this includes a dot (.), so it has to be truncated
        context.test_methodname = test.__slash__.address_in_factory[1:]
    try:
        yield
    finally:
        context.test = prev_test
        context.test_id = prev_test_id
