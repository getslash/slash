# pylint: disable=redefined-outer-name
import shutil
import os
import sys

import pytest
import slash

_PYPY = hasattr(sys, "pypy_version_info")

def test_coverage(suite, coverage_plugin, capsys):
    # pylint: disable=unused-argument

    suite_path = suite.commit()
    suite.run(commit=False)

    out, err = capsys.readouterr()
    assert '---------- coverage:' in out
    for test_file in suite.files:
        test_path = os.path.join(suite_path, test_file.get_relative_path())
        assert_string_in_file('.coverage', test_path)
        assert os.path.isfile('htmlcov/index.html')
        assert_string_in_file('htmlcov/index.html', test_path)
        test_report_name = test_path.replace('.', '_').replace(os.path.sep, '_')
        assert os.path.isfile(os.path.join('htmlcov', '{}.html'.format(test_report_name)))
        assert_string_in_file(os.path.join('htmlcov', '{}.html'.format(test_report_name)), test_path)


def assert_string_in_file(filename, string):
    with open(filename) as fh:
        data = fh.read()
        assert string in data

@pytest.fixture
def coverage_plugin(request):
    if os.path.isfile('.coverage'):
        os.remove('.coverage')
    if os.path.isdir('htmlcov'):
        shutil.rmtree('htmlcov')
    slash.config.root.plugin_config.coverage.cov_report = ['html', 'term', 'xml']
    if not _PYPY:
        slash.config.root.plugin_config.coverage.cov_report.append('annotate')

    slash.plugins.manager.activate('coverage')

    @request.addfinalizer
    def deactivate():
        slash.plugins.manager.deactivate('coverage')


