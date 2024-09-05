"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

Module _safe_path deals with platform related path issues

Unit test -- Module

.. code-block:: shell

   python -m coverage run --source='drain_swamp._safe_path' -m pytest \
   --showlocals tests/test_safe_path.py && coverage report \
   --data-file=.coverage --include="**/_safe_path.py"

Integration test

.. code-block:: shell

   make coverage
   pytest --showlocals --cov="drain_swamp" --cov-report=term-missing \
   --cov-config=pyproject.toml tests

"""

from pathlib import PurePath
from unittest.mock import patch

import pytest

from drain_swamp._safe_path import (
    resolve_joinpath,
    resolve_path,
)
from drain_swamp.constants import g_app_name


def test_resolve_joinpath(tmp_path):
    """Platform aware joinpath."""
    # pytest --showlocals --log-level INFO -k "test_resolve_joinpath" tests
    parts = ("src", "empty_file.txt")
    relpath_b = PurePath("src/empty_file.txt")
    abspath_from_joining = resolve_joinpath(tmp_path, relpath_b)
    abspath_from_parts = tmp_path.joinpath(*parts)
    assert abspath_from_joining == abspath_from_parts


testdata_resolve_path = (
    (
        True,
        "true",
        "\\true",
    ),
    (
        False,
        "true",
        "/true",
    ),
)
ids_resolve_path = (
    "Windows",
    "Linux",
)


@pytest.mark.parametrize(
    "is_set_platform_win, f_path, expected",
    testdata_resolve_path,
    ids=ids_resolve_path,
)
def test_resolve_path(is_set_platform_win, f_path, expected):
    """Test resolve_path.

    Do not know the exact absolute path. So just check contains the
    expected components of the path
    """
    # pytest --showlocals --log-level INFO -k "test_resolve_path" tests

    with patch(f"{g_app_name}._safe_path.is_win", return_value=is_set_platform_win):
        actual = resolve_path(f_path)
        assert expected in actual
