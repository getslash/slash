"""Coverage controllers for use by pytest-cov and nose-cov."""

import os
import sys
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

import coverage


class CovController(object):
    """Base class for different plugin implementations."""

    def __init__(self, cov_source, cov_report, cov_config, cov_append, config=None, nodeid=None):
        """Get some common config used by multiple derived classes."""
        self.cov_source = cov_source
        self.cov_report = cov_report
        self.cov_config = cov_config
        self.cov_append = cov_append
        self.config = config
        self.nodeid = nodeid

        self.cov = None
        self.node_descs = set()
        self.failed_slaves = []
        self.topdir = os.getcwd()

    def set_env(self):
        """Put info about coverage into the env so that subprocesses can activate coverage."""
        if self.cov_source is None:
            os.environ['COV_CORE_SOURCE'] = ''
        else:
            os.environ['COV_CORE_SOURCE'] = os.pathsep.join(
                os.path.abspath(p) for p in self.cov_source)
        config_file = os.path.abspath(self.cov_config)
        if os.path.exists(config_file):
            os.environ['COV_CORE_CONFIG'] = config_file
        else:
            os.environ['COV_CORE_CONFIG'] = ''
        os.environ['COV_CORE_DATAFILE'] = os.path.abspath('.coverage')

    @staticmethod
    def unset_env():
        """Remove coverage info from env."""
        os.environ.pop('COV_CORE_SOURCE', None)
        os.environ.pop('COV_CORE_CONFIG', None)
        os.environ.pop('COV_CORE_DATAFILE', None)

    @staticmethod
    def get_node_desc(platform, version_info):
        """Return a description of this node."""

        return 'platform %s, python %s' % (platform, '%s.%s.%s-%s-%s' % version_info[:5])

    @staticmethod
    def sep(stream, s, txt):
        if hasattr(stream, 'sep'):
            stream.sep(s, txt)
        else:
            sep_total = max((70 - 2 - len(txt)), 2)
            sep_len = sep_total // 2
            sep_extra = sep_total % 2
            out = '%s %s %s\n' % (s * sep_len, txt, s * (sep_len + sep_extra))
            stream.write(out)

    def summary(self, stream):
        """Produce coverage reports."""
        total = 0

        if not self.cov_report:
            with open(os.devnull, 'w') as null:
                total = self.cov.report(show_missing=True, ignore_errors=True, file=null)
                return total

        # Output coverage section header.
        if len(self.node_descs) == 1:
            self.sep(stream, '-', 'coverage: %s' % ''.join(self.node_descs))
        else:
            self.sep(stream, '-', 'coverage')
            for node_desc in sorted(self.node_descs):
                self.sep(stream, ' ', '%s' % node_desc)

        # Produce terminal report if wanted.
        if 'term' in self.cov_report or 'term-missing' in self.cov_report:
            show_missing = ('term-missing' in self.cov_report) or None
            total = self.cov.report(show_missing=show_missing, ignore_errors=True, file=stream)

        # Produce annotated source code report if wanted.
        if 'annotate' in self.cov_report:
            self.cov.annotate(ignore_errors=True)
            # We need to call Coverage.report here, just to get the total
            # Coverage.annotate don't return any total and we need it for --cov-fail-under.
            total = self.cov.report(ignore_errors=True, file=StringIO())
            stream.write('Coverage annotated source written next to source\n')

        # Produce html report if wanted.
        if 'html' in self.cov_report:
            total = self.cov.html_report(ignore_errors=True)
            stream.write('Coverage HTML written to dir %s\n' % self.cov.config.html_dir)

        # Produce xml report if wanted.
        if 'xml' in self.cov_report:
            total = self.cov.xml_report(ignore_errors=True)
            stream.write('Coverage XML written to file %s\n' % self.cov.config.xml_output)

        # Report on any failed slaves.
        if self.failed_slaves:
            self.sep(stream, '-', 'coverage: failed slaves')
            stream.write('The following slaves failed to return coverage data, '
                         'ensure that pytest-cov is installed on these slaves.\n')
            for node in self.failed_slaves:
                stream.write('%s\n' % node.gateway.id)

        return total


class Central(CovController):
    """Implementation for centralised operation."""

    def start(self):
        """Erase any previous coverage data and start coverage."""

        self.cov = coverage.coverage(source=self.cov_source,
                                     config_file=self.cov_config)
        if self.cov_append:
            self.cov.load()
        else:
            self.cov.erase()
        self.cov.start()
        self.set_env()

    def finish(self):
        """Stop coverage, save data to file and set the list of coverage objects to report on."""

        self.unset_env()
        self.cov.stop()
        self.cov.combine()
        self.cov.save()
        node_desc = self.get_node_desc(sys.platform, sys.version_info)
        self.node_descs.add(node_desc)
