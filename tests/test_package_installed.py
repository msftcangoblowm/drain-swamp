"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

Checks if a Python package is installed

.. code-block:: shell

   pytest --showlocals --log-level INFO tests/test_is_package_installed.py
   pytest --showlocals --cov="drain_swamp" --cov-report=term-missing tests/test_is_package_installed.py

"""

import pytest

from drain_swamp._package_installed import is_package_installed
from drain_swamp.constants import g_app_name

testdata_is_package_installed = (
    (
        "blarneys_blowup_doll",
        False,
    ),
    (
        g_app_name,
        True,
    ),
)
ids_is_package_installed = (
    "no such package",
    "package exists",
)


@pytest.mark.parametrize(
    "app_name, is_installed",
    testdata_is_package_installed,
    ids=ids_is_package_installed,
)
def test_is_package_installed(app_name, is_installed):
    """Check if package is installed or not"""
    # pytest --showlocals --log-level INFO -k "test_is_package_installed" tests
    assert is_package_installed(app_name) is is_installed
