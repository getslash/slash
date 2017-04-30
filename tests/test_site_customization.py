# pylint: disable=global-statement,global-variable-not-assigned
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


class SlashRunSiteCustomizationTest(TestCase):
    "Make sure ``slash run`` calls site.load()"

    def setUp(self):
        super(SlashRunSiteCustomizationTest, self).setUp()
        self.forge.replace(slash.site, "load")
        self.forge.replace_with(sys, "stderr", cStringIO())

    def test_slash_run_calls_site_load(self):
        slash.site.load(working_directory=None)
        self.forge.replay()
        app = slash_run.slash_run([])
        assert app.exit_code != 0

_customization_index = 0
_loaded_customizations = []


def _apply_customization(index=0):
    _loaded_customizations.append(index)


class CustomizationTest(TestCase):

    def setUp(self):
        super(CustomizationTest, self).setUp()
        global _loaded_customizations
        global _customization_index
        _customization_index = 0
        _loaded_customizations = []

    def get_customization_source(self):
        global _customization_index
        returned = "import {0}; {0}._apply_customization({1})".format(__name__, _customization_index)
        _customization_index += 1
        return returned

    def test_customize_via_local_and_global_slashrc(self):
        self._test_customize_via_local_slashrc(also_use_global=True)

    def test_customize_via_local_slashrc(self):
        self._test_customize_via_local_slashrc(also_use_global=False)

    def _test_customize_via_local_slashrc(self, also_use_global):
        if also_use_global:
            global_slashrc_path = os.path.join(self.get_new_path(), "slashrc")
            self.override_config("run.user_customization_file_path", global_slashrc_path)
            with open(global_slashrc_path, "w") as f:
                f.write(self.get_customization_source())

        self.addCleanup(os.chdir, os.path.abspath("."))
        os.chdir(self.get_new_path())
        with open(".slashrc", "w") as f:
            f.write(self.get_customization_source())
        self.assert_customization_loaded()

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
        unused = self.get_customization_source()  # expect a single customization  # pylint: disable=unused-variable
        entry_point.load().and_return(_apply_customization)
        self.forge.replay()
        self.assert_customization_loaded()

    def assert_customization_loaded(self):
        global _loaded_customizations
        global _customization_index
        slash.site.load()
        self.assertEqual(_loaded_customizations, list(range(_customization_index)))
