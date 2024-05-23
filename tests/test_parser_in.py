"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

..

Unittest for module, drain_swamp.backend_setupttools

Without coverage

.. code-block:: shell

   pytest --showlocals --log-level INFO tests/test_parser_in.py

With coverage

.. code-block:: shell

   pytest --showlocals --cov="drain_swamp" --cov-report=term-missing tests/test_parser_in.py

"""

import sys
from pathlib import Path

import pytest

from drain_swamp.exceptions import PyProjectTOMLParseError
from drain_swamp.parser_in import get_pyproject_toml

if sys.version_info >= (3, 9):  # pragma: no cover
    from collections.abc import Mapping
else:
    from typing import Mapping

testdata_unsupported_type = [
    (None,),
    ("Hello world!",),
    (1.1234,),
    (1,),
]
ids_unsupported_type = (
    "None",
    "str",
    "float",
    "int",
)


@pytest.mark.parametrize(
    "invalid",
    testdata_unsupported_type,
    ids=ids_unsupported_type,
)
def test_get_pyproject_toml_unsupported_type(invalid):
    # pytest --showlocals --log-level INFO -k "test_get_pyproject_toml_unsupported_type" tests
    with pytest.raises(TypeError):
        get_pyproject_toml(invalid)


def test_get_pyproject_toml_path_bad(tmp_path):
    # pytest --showlocals --log-level INFO -k "test_get_pyproject_toml_path_bad" tests
    # A Path but dodgy --> FileNotFoundError
    invalids = (
        Path("/etc"),  # folder without a pyproject.toml in it
        tmp_path.joinpath("hi_there.txt"),  # absolute but nonexistent
        Path("__init__.py"),  # not absolute
    )
    for invalid in invalids:
        with pytest.raises(FileNotFoundError):
            get_pyproject_toml(invalid)


PYPROJECT_TOML_BAD = list(
    Path(__file__).parent.joinpath("_bad_files").glob("backend_only.pyproject_toml")
)


@pytest.mark.parametrize(
    "path",
    PYPROJECT_TOML_BAD,
    ids=[path.name.rsplit(".", 1)[0] for path in PYPROJECT_TOML_BAD],
)
def test_get_pyproject_toml_bad(path):
    # pytest --showlocals --log-level INFO -k "test_get_pyproject_toml_bad" tests

    # file_as_str = path.read_text()
    # Provide a path, not the file contents
    invalids = (
        path,
        str(path),
        # file_as_str,
    )
    for invalid in invalids:
        with pytest.raises(PyProjectTOMLParseError):
            get_pyproject_toml(invalid)


PYPROJECT_TOML_GOOD = list(
    Path(__file__).parent.joinpath("_good_files").glob("*.pyproject_toml")
)


@pytest.mark.parametrize(
    "path",
    PYPROJECT_TOML_GOOD,
    ids=[path.name.rsplit(".", 1)[0] for path in PYPROJECT_TOML_GOOD],
)
def test_get_pyproject_toml_good(path):
    # pytest --showlocals --log-level INFO -k "test_get_pyproject_toml_good" tests
    valids = (
        path,
        str(path),
    )
    for valid in valids:
        # Provide a path, not the file contents
        actual = get_pyproject_toml(valid)
        assert isinstance(actual, Mapping)


testdata_get_pyproject_toml_dir = (
    Path(__file__).parent.parent,
    Path(__file__).parent,
)
ids_get_pyproject_toml_dir = (
    "package base folder",
    "tests folder",
)


@pytest.mark.parametrize(
    "path_dir",
    testdata_get_pyproject_toml_dir,
    ids=ids_get_pyproject_toml_dir,
)
def test_get_pyproject_toml_dir(path_dir):
    # pytest --showlocals --log-level INFO -k "test_get_pyproject_toml_dir" tests
    actual = get_pyproject_toml(path_dir)
    assert isinstance(actual, Mapping)
