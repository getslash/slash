import datetime
import socket
import sys
from ..interface import PluginInterface
from ...ctx import context
from ...utils.marks import mark
from ...utils.conf_utils import Cmdline
from ...utils.traceback_utils import get_traceback_string
from slash import config as slash_config

from xml.etree.ElementTree import (
    tostring as xml_to_string,
    Element as E,
    )

class Plugin(PluginInterface):

    _xunit_elements = None

    def _get_xunit_elements_list(self):
        returned = self._xunit_elements
        if returned is None:
            returned = self._xunit_elements = []
        return returned

    def get_name(self):
        return "xunit"

    def get_config(self):
        return {"filename": "testsuite.xml" // Cmdline(arg="--xunit-filename")}

    def session_start(self):
        self._start_time = datetime.datetime.now()

    def test_start(self):
        self._get_xunit_elements_list().append(E("testcase", {
            "name": str(context.test),
            "classname": type(context.test).__name__,
            "time": "0"
        }))

    def test_success(self):
        pass

    def error_added(self, result, error):
        if error.is_failure():
            self._add_error("failure")
        else:
            self._add_error("error")

    def _add_error(self, errortype):
        exc_type, exc_value, exc_tb = exc_info = sys.exc_info()
        self.add_test_metadata(errortype,
                                {'type': exc_type.__name__, 'message': str(exc_value)},
                                get_traceback_string(exc_info))

    @mark("register_on", None)  # same as slash.plugins.registers_on, which cause circular ImportError
    def add_test_metadata(self, title, attributes=None, content=None):
        if not attributes:
            attributes = {}
        test_element = self._get_xunit_elements_list()[-1]
        data_element = E(title, attributes)
        data_element.text = content
        test_element.append(data_element)

    def _get_test_case_element(self, test):
        return E('testcase', dict(name=str(test), classname="{}.{}".format(test.__class__.__module__, test.__class__.__name__), time="0"))

    def test_skip(self, reason):
        test_element = self._get_xunit_elements_list()[-1]
        test_element.append(E('skipped', type=reason or ''))

    def result_summary(self):
        e = E('testsuite', {
            "name": "slash-suite",
            "hostname": socket.getfqdn(),
            "timestamp": self._start_time.isoformat().rsplit(".", 1)[0],
            "time": "0",
            "tests": str(context.session.results.get_num_results()),
            "errors": str(context.session.results.get_num_errors()),
            "failures": str(context.session.results.get_num_failures()),
            "skipped": str(context.session.results.get_num_skipped()),
        })
        for element in self._get_xunit_elements_list():
            e.append(element)
        with open(slash_config.root.plugin_config.xunit.filename, "wb") as outfile:
            outfile.write(xml_to_string(e))
