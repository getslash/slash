import os
import doctest

def test_readme_doctests():
    readme_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "README.md"))
    assert os.path.exists(readme_path)
    result = doctest.testfile(readme_path, module_relative=False)
    assert result.failed == 0, ('%s tests failed!' % result.failed)
