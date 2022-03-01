import datetime
import itertools
import socket
import sys
from ..interface import PluginInterface
from ...ctx import context
from ...conf import config
from ...utils.traceback_utils import get_traceback_string
from ...utils.conf_utils import Cmdline, Doc
from slash import config as slash_config
from slash import context
from xml.etree.ElementTree import (
    tostring as xml_to_string,
    Element as E,
    SubElement as SE
)

class Plugin(PluginInterface):
    """
    For more information see https://slash.readthedocs.org/en/master/builtin_plugins.html#xunit
    """

    _start_time = datetime.datetime.now()

    def get_name(self):
        return "xunit"

    def get_default_config(self):
        return {
            "filename": "testsuite.xml" // Cmdline(arg="--xunit-filename") // Doc('Name of XML xUnit file to create'),
        }

    def session_start(self):
        self._start_time = datetime.datetime.now()

    def _add_error(self, parent, errortype, error):
        exc_type, exc_value, _ = exc_info = sys.exc_info()
        self._add_element(parent, errortype,
                          {'type': exc_type.__name__ if exc_type else errortype, 'message': error.message},
                          text=get_traceback_string(exc_info) if exc_value is not None else None,
        )

    def _add_element(self, parent, tag, attrib, text=None):
        element = E(tag, attrib)
        if text is not None:
            element.text = text
        parent.append(element)

    def _get_test_case_element(self, test):
        return E('testcase', dict(name=str(test), classname="{}.{}".format(test.__class__.__module__, test.__class__.__name__), time="0"))

    def _detail2xml(self, tag, name, value):
        r = E(tag, {'name': name})
        if isinstance(value, (dict, tuple, list)):
            r = self._build_xml(r, value)
        elif isinstance(value, (float, int)):
            r.attrib['value'] = str(value)
        else:
            r.attrib['value'] = value
        return r

    def _build_xml(self, r, d):
        if isinstance(d, dict):
            for k, v in d.items():
                s = SE(r, k)
                self._build_xml(s, v)
        elif isinstance(d, (tuple, list)):
            for v in d:
                s = SE(r, 'i')
                self._build_xml(s, v)
        else:
            r.text = str(d)
        return r

    def session_end(self):

        if config.root.parallel.worker_id is not None:
            return

        suite_time = sum([result.get_duration() for result in context.session.results.iter_test_results()],
                         datetime.timedelta()).total_seconds()

        e = E('testsuite', {
            "name": "slash-suite",
            "hostname": socket.getfqdn(),
            "timestamp": self._start_time.isoformat().rsplit(".", 1)[0],
            "time": str(suite_time),
            "tests": str(context.session.results.get_num_results()),
            "errors": str(context.session.results.get_num_errors()),
            "failures": str(context.session.results.get_num_failures()),
            "skipped": str(
                context.session.results.get_num_skipped(include_not_run=False)
            ),
        })
        self._add_errors(e, context.session.results.global_result)
        run_test_results = filter(
            lambda result: result.is_started(),
            context.session.results.iter_test_results()
        )

        for result in run_test_results:

            test = E("testcase", {
                "name": result.test_metadata.address,
                "classname": result.test_metadata.class_name or '',
                "time": str(result.get_duration().total_seconds())
            })
            self._add_errors(test, result)

            for skip in result.get_skips():
                self._add_element(test, 'skipped', {'type': skip or ''})

            for detail_name, detail_value in result.details.all().items():
                if not isinstance(detail_value, list):
                    detail_value = [detail_value]

                for value in detail_value:
                    value = self._detail2xml('detail', detail_name, value)
                    test.append(value)

            e.append(test)

        with open(slash_config.root.plugin_config.xunit.filename, "wb") as outfile:
            outfile.write(xml_to_string(e))

    def _add_errors(self, parent, result):
        for error in itertools.chain(result.get_errors(), result.get_failures()):
            self._add_error(parent, 'failure' if error.is_failure() else 'error', error)
