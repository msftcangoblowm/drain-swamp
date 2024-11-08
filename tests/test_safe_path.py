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

from collections.abc import Sequence
from contextlib import nullcontext as does_not_raise
from pathlib import (
    Path,
    PurePath,
)

import pytest

from drain_swamp._safe_path import (
    get_venv_python_abspath,
    is_linux,
    is_macos,
    is_win,
    replace_suffixes,
    resolve_joinpath,
    resolve_path,
)
from drain_swamp.pep518_venvs import VenvMapLoader


def test_platform_checks():
    """Not caring about the result, run is_[platform] checks."""
    # pytest --showlocals --log-level INFO -k "test_platform_checks" tests
    fcns = (
        is_linux,
        is_macos,
        is_win,
    )
    for fcn in fcns:
        bool_result = fcn()
        assert isinstance(bool_result, bool)


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
    pytest.param(
        "adsfdsafdsafdsafasfsadfafsadfasdfsadfasdf",
        None,
        marks=pytest.mark.skipif(is_win(), reason="MacOS and linux platform issue"),
    ),
)
ids_resolve_path = (
    "Windows",
    "Linux and MacOS",
    "nonexistent executable",
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
    if expected is None:
        assert expected == actual
    else:
        assert expected in actual


testdata_replace_suffixes = (
    ("ted.txt", [".tar", ".gz"], "ted.tar.gz"),
    (
        "ted.txt",
        None,
        "ted",
    ),
    (
        "ted.txt",
        "",
        "ted",
    ),
)
ids_replace_suffixes = (
    "txt to tarball",
    "suffixes None",
    "suffixes empty str",
)


@pytest.mark.parametrize(
    "relpath, suffixes, expected_name",
    testdata_replace_suffixes,
    ids=ids_replace_suffixes,
)
def test_replace_suffixes(suffixes, expected_name, tmp_path, relpath):
    """Confirm can replace suffixes on an absolute path."""
    # pytest --showlocals --log-level INFO -k "test_replace_suffixes" tests
    is_nonstr_sequence = (
        suffixes is not None
        and isinstance(suffixes, Sequence)
        and not isinstance(suffixes, str)
    )
    if is_nonstr_sequence:
        str_suffixes = "".join(suffixes)
    else:
        str_suffixes = suffixes

    abspath_0 = tmp_path / relpath
    abspath_1 = replace_suffixes(abspath_0, str_suffixes)
    if is_nonstr_sequence:
        assert abspath_1.suffixes == suffixes
    assert abspath_1.name == expected_name


def test_get_venv_python_abspath(
    tmp_path,
    path_project_base,
):
    """Confirm drain-swamp venv relpaths are real venv, not just folders."""
    # pytest --showlocals --log-level INFO -k "test_get_venv_python_abspath" tests
    path_cwd = path_project_base()

    # FileNotFoundError (pyproject.toml) or LookupError (section tool.venvs)
    expectation = does_not_raise()
    with expectation:
        loader = VenvMapLoader(str(path_cwd))
    if isinstance(expectation, does_not_raise):
        venv_relpaths = loader.venv_relpaths
        for venv_relpath in venv_relpaths:
            """Get the python executable path from the cwd base path
            and venv relative path.
            """
            fcn = get_venv_python_abspath
            args = (path_cwd, venv_relpath)
            kwargs = {}
            try:
                abspath_venv_python_executable = fcn(*args, **kwargs)
            except NotADirectoryError:
                # pytest-venv can be given a path to a pyenv python shim
                # pip-compile --pip-args='--python=[pyenv_python_shim_abspath]' ...
                reason = (
                    f"No venv at relative path {venv_relpath}. "
                    "Run context may preclude creating a venv with the "
                    "correct interpreter version."
                )
                pytest.skip(reason)
            else:
                venv_python_executable_abspath = Path(abspath_venv_python_executable)
                # TODO: test has executable permission
                is_file = (
                    venv_python_executable_abspath.exists()
                    and venv_python_executable_abspath.is_file()
                )
                assert is_file is True

        # Force a NotADirectoryError
        venv_relpath = resolve_joinpath(
            path_cwd, "a-crack-addiction-would-be-healthier"
        )
        with pytest.raises(NotADirectoryError):
            get_venv_python_abspath(path_cwd, venv_relpath)

        with pytest.raises(TypeError):
            get_venv_python_abspath(None, venv_relpath)
