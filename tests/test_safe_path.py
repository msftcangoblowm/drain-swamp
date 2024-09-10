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

from pathlib import (
    Path,
    PurePath,
)

import pytest

from drain_swamp._safe_path import (
    is_win,
    replace_suffixes,
    resolve_joinpath,
    resolve_path,
)


def test_resolve_joinpath(tmp_path):
    """Platform aware joinpath."""
    # pytest --showlocals --log-level INFO -k "test_resolve_joinpath" tests
    parts = ("src", "empty_file.txt")
    abspath_types_a = (
        PurePath(tmp_path),
        tmp_path,  # Path
    )
    b_repath = "src/empty_file.txt"
    relpaths_types_b = (
        PurePath(b_repath),
        Path(b_repath),
    )
    for abspath in abspath_types_a:
        for relpath in relpaths_types_b:
            abspath_from_joining = resolve_joinpath(abspath, relpath)
            abspath_from_parts = abspath.joinpath(*parts)
            assert abspath_from_joining == abspath_from_parts


testdata_resolve_path = (
    pytest.param(
        "true",
        "\\true",
        marks=pytest.mark.skipif(not is_win(), reason="Windows platform issue"),
    ),
    pytest.param(
        "true",
        "/true",
        marks=pytest.mark.skipif(is_win(), reason="MacOS and linux platform issue"),
    ),
)
ids_resolve_path = (
    "Windows",
    "Linux and MacOS",
)


@pytest.mark.parametrize(
    "f_path, expected",
    testdata_resolve_path,
    ids=ids_resolve_path,
)
def test_resolve_path(f_path, expected):
    """Test resolve_path.

    Do not know the exact absolute path. So just check contains the
    expected components of the path
    """
    # pytest --showlocals --log-level INFO -k "test_resolve_path" tests
    actual = resolve_path(f_path)
    assert expected in actual


testdata_replace_suffixes = (
    (
        "ted.txt",
        [".tar", ".gz"],
    ),
)
ids_replace_suffixes = ("txt to tarball",)


@pytest.mark.parametrize(
    "relpath, suffixes",
    testdata_replace_suffixes,
    ids=ids_replace_suffixes,
)
def test_replace_suffixes(tmp_path, relpath, suffixes):
    """Confirm can replace suffixes on an absolute path."""
    # pytest --showlocals --log-level INFO -k "test_replace_suffixes" tests
    str_suffixes = "".join(suffixes)
    abspath_0 = tmp_path / relpath
    abspath_1 = replace_suffixes(abspath_0, str_suffixes)
    assert abspath_1.suffixes == suffixes
