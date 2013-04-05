from .utils import TestCase
import os
import sys
from tempfile import mktemp
import shakedown
import shakedown.site
from shakedown.frontend import shake_run
import requests
from six.moves import cStringIO as StringIO

site_customized = False

class ShakeRunSiteCustomizationTest(TestCase):
    "Make sure ``shake run`` calls site.load()"
    def setUp(self):
        super(ShakeRunSiteCustomizationTest, self).setUp()
        self.forge.replace(shakedown.site, "load")
        self.forge.replace_with(sys, "stderr", StringIO())
    def test_shake_run_calls_site_load(self):
        shakedown.site.load()
        self.forge.replay()
        with self.assertRaises(SystemExit):
            shake_run.shake_run([])

class CustomizationTest(TestCase):
    def setUp(self):
        super(CustomizationTest, self).setUp()
    def get_customization_source(self):
        return "import {0}; {0}.site_customized=True".format(__name__)
    def test_customize_via_shakerc(self):
        shakedownrc_path = mktemp()
        self.forge.replace(os.path, "expanduser")
        os.path.expanduser("~/.shakedown/shakerc").whenever().and_return(shakedownrc_path)
        with open(shakedownrc_path, "w") as f:
            f.write(self.get_customization_source())
        self.forge.replay()
        self.assert_customization_loaded()
    def test_customize_via_env_var(self):
        os.environ["SHAKEDOWN_SETTINGS"] = custom_filename = mktemp()
        self.addCleanup(os.environ.pop, "SHAKEDOWN_SETTINGS")
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
        os.environ["SHAKEDOWN_SETTINGS"] = url
        self.addCleanup(os.environ.pop, "SHAKEDOWN_SETTINGS")
        self.forge.replay()
        self.assert_customization_loaded()
    def assert_customization_loaded(self):
        global site_customized
        site_customized = False
        shakedown.site.load()
        self.assertTrue(site_customized, "Customization not loaded!")
