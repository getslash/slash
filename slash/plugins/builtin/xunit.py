import datetime
import socket
import sys
from ..interface import PluginInterface
from ...ctx import context
from ...utils.traceback_utils import get_traceback_string
from ...utils.conf_utils import Cmdline
from slash import config as slash_config
from slash import context
from xml.etree.ElementTree import (
    tostring as xml_to_string,
    Element as E,
    )

class Plugin(PluginInterface):
    """
    For more information see https://slash.readthedocs.org/en/master/builtin_plugins.html#xunit
    """

    _xunit_elements = None
    _start_time = datetime.datetime.now()

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
            "name": context.test.__slash__.address,
            "classname": context.test.__slash__.class_name or '',
            "time": "0"
        }))

    def test_success(self):
        pass

    def test_end(self):
        for detail_name, detail_value in context.result.details.all().items():
            self._add_element('detail', {'name': detail_name, 'value': detail_value})

    def error_added(self, result, error): # pylint: disable=unused-argument
        if error.is_failure():
            self._add_error("failure", error)
        else:
            self._add_error("error", error)

    def _add_error(self, errortype, error):
        exc_type, exc_value, _ = exc_info = sys.exc_info()
        self._add_element(errortype, {'type': exc_type.__name__ if exc_type else errortype, 'message': error.message}, text=get_traceback_string(exc_info) if exc_value is not None else None)

    def _add_element(self, tag, attrib, text=None):
        if not context.test:
            return
        test_element = self._get_xunit_elements_list()[-1]
        element = E(tag, attrib)
        if text is not None:
            element.text = text
        test_element.append(element)

    def _get_test_case_element(self, test):
        return E('testcase', dict(name=str(test), classname="{}.{}".format(test.__class__.__module__, test.__class__.__name__), time="0"))

    def test_skip(self, reason):
        test_element = self._get_xunit_elements_list()[-1]
        test_element.append(E('skipped', type=reason or ''))

    def session_end(self):
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
