from __future__ import absolute_import

import os
import sys
from ..interface import PluginInterface
from ...utils.conf_utils import Cmdline, Doc
from slash import config as slash_config
from ..cov_engine import engine, embed
from coverage.misc import CoverageException


class CoverageError(Exception):
    """Indicates that our coverage is too low"""
    pass

class Plugin(PluginInterface):
    """Use coverage package to produce code coverage reports.

    Delegates all work to a particular implementation based on whether
    this test process is centralised, a distributed master or a
    distributed slave.
    """

    def __init__(self):
        """Creates a coverage slash plugin.

        We read the rc file that coverage uses to get the data file
        name.  This is needed since we give coverage through it's API
        the data file name.
        """

        # Our implementation is unknown at this time.
        self.pid = None
        self.cov = None
        self.cov_controller = None
        self.failed = False
        self._started = False

    def activate(self):
        self._start(engine.Central)

    def _start(self, controller_cls=engine.Central, config=None, nodeid=None):
        if config is None:
            # fake config option for engine
            class Config(object):
                option = []

            config = Config()

        self.cov_controller = controller_cls(
            slash_config.root.plugin_config.coverage.cov_source,
            slash_config.root.plugin_config.coverage.cov_report,
            slash_config.root.plugin_config.coverage.cov_config,
            slash_config.root.plugin_config.coverage.cov_append,
            config,
            nodeid
        )
        self.cov_controller.start()
        self._started = True

    def get_name(self):
        return "coverage"

    def get_config(self):
        return {
            'cov_source': [] // Doc('measure coverage for filesystem path (multi-allowed)') // Cmdline(append='--cov', metavar='path'),
            'cov_report': [] // Doc('type of report to generate: term, term-missing, annotate, html, xml (multi-allowed)') // Cmdline(append='--cov-report'),
            'cov_config': '.coveragerc' // Doc('config file for coverage, default: .coveragerc') // Cmdline(arg='--cov-config', metavar='path'),
            'cov_append': False // Doc('do not delete coverage but append to current, default: False') // Cmdline(on='--cov-append')
        }

    def session_start(self):
        """At session start determine our implementation and delegate to it."""
        self.pid = os.getpid()
        if not self._started:
            self.activate()

    def session_end(self):
        """Delegate to our implementation."""
        self.failed = False
        if self.cov_controller is not None:
            self.cov_controller.finish()

    def test_start(self):
        if os.getpid() != self.pid:
            # test is run in another process than session, run
            # coverage manually
            self.cov = embed.init()

    def test_end(self):
        if self.cov is not None:
            embed.multiprocessing_finish(self.cov)
            self.cov = None

    def result_summary(self):
        """Delegate to our implementation."""
        if self.cov_controller is None:
            return
        try:
            total = self.cov_controller.summary(sys.stdout)
        except CoverageException as exc:
            sys.stdout.write('Failed to generate report: %s\n' % exc)  # pragma: no cover
            total = 0                                                  # pragma: no cover
        assert total is not None, 'Test coverage should never be `None`'
