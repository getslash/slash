from .utils import TestCase
import os
import sys
from tempfile import mktemp
import slash
import slash.site
from slash._compat import cStringIO
from slash.frontend import slash_run
import requests
import pkg_resources

site_customized = False

class SlashRunSiteCustomizationTest(TestCase):
    "Make sure ``slash run`` calls site.load()"
    def setUp(self):
        super(SlashRunSiteCustomizationTest, self).setUp()
        self.forge.replace(slash.site, "load")
        self.forge.replace_with(sys, "stderr", cStringIO())
    def test_slash_run_calls_site_load(self):
        slash.site.load()
        self.forge.replay()
        with self.assertRaises(SystemExit):
            slash_run.slash_run([])

class CustomizationTest(TestCase):
    def get_customization_source(self):
        return "import {0}; {0}.site_customized=True".format(__name__)
    def get_customization_function(self):
        def _customize():
            global site_customized
            site_customized = True
        return _customize
    def test_customize_via_slashrc(self):
        slashrc_path = os.path.join(self.get_new_path(), "slashrc")
        self.override_config("run.user_customization_file_path", slashrc_path)
        with open(slashrc_path, "w") as f:
            f.write(self.get_customization_source())
    def test_customize_via_env_var(self):
        os.environ["SLASH_SETTINGS"] = custom_filename = mktemp()
        self.addCleanup(os.environ.pop, "SLASH_SETTINGS")
        with open(custom_filename, "w") as f:
            f.write(self.get_customization_source())
        self.assert_customization_loaded()
    def test_customize_via_url(self):
        url = "http://nonexistent.com/some/path/to/custom/file.py"
        self.forge.replace(requests, "get")
        fake_response = self.forge.create_mock(requests.Response)
        fake_response.raise_for_status().whenever()
        fake_response.content = self.get_customization_source()
        requests.get(url).and_return(fake_response)
        os.environ["SLASH_SETTINGS"] = url
        self.addCleanup(os.environ.pop, "SLASH_SETTINGS")
        self.forge.replay()
        self.assert_customization_loaded()
    def test_customize_via_pkgutil_entry_point(self):
        self.forge.replace(pkg_resources, "iter_entry_points")
        entry_point = self.forge.create_wildcard_mock()
        pkg_resources.iter_entry_points("slash.site.customize").and_return(iter([entry_point]))
        entry_point.load().and_return(self.get_customization_function())
        self.forge.replay()
        self.assert_customization_loaded()
    def assert_customization_loaded(self):
        global site_customized
        site_customized = False
        slash.site.load()
        self.assertTrue(site_customized, "Customization not loaded!")
