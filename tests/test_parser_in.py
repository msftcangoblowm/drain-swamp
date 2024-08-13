"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

..

Unittest for module, drain_swamp.backend_setupttools

.. code-block:: shell

   pytest --showlocals --log-level INFO tests/test_parser_in.py
   pytest --showlocals --cov="drain_swamp" --cov-report=term-missing tests/test_parser_in.py

"""

import sys
from pathlib import (
    Path,
    PurePath,
)

import pytest

from drain_swamp.exceptions import (
    PyProjectTOMLParseError,
    PyProjectTOMLReadError,
)
from drain_swamp.parser_in import TomlParser

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
    with pytest.raises(PyProjectTOMLReadError):
        TomlParser(invalid, raise_exceptions=True)


testdata_random_folders_and_files = (
    pytest.param(
        Path("/etc"),
        marks=pytest.mark.xfail(raises=PyProjectTOMLReadError),
    ),
    pytest.param(
        Path("/etc/dog_shit_throwing_monkey.conf"),
        marks=pytest.mark.xfail(raises=PyProjectTOMLReadError),
    ),
    (Path("__init__.py")),
)
ids_random_folders_and_files = (
    "folder without a pyproject.toml in it",
    "absolute but nonexistent",
    "realitive path which shockingly resolves",
)


@pytest.mark.parametrize(
    "path_f",
    testdata_random_folders_and_files,
    ids=ids_random_folders_and_files,
)
def test_random_folders_and_files(path_f):
    # pytest --showlocals --log-level INFO -k "test_random_folders_and_files" tests
    # A Path but dodgy --> FileNotFoundError
    TomlParser(path_f, raise_exceptions=True)


testdata_unparsable = list(
    Path(__file__).parent.joinpath("_bad_files").glob("backend_only.pyproject_toml")
)


@pytest.mark.parametrize(
    "path_toml_src",
    testdata_unparsable,
    ids=[path.name.rsplit(".", 1)[0] for path in testdata_unparsable],
)
def test_get_pyproject_toml_bad(path_toml_src, tmp_path, prep_pyproject_toml):
    # pytest --showlocals --log-level INFO -k "test_get_pyproject_toml_bad" tests

    # file_as_str = path.read_text()
    # Provide a path, not the file contents
    path_f = prep_pyproject_toml(path_toml_src, tmp_path)
    invalids = (path_f,)
    for invalid in invalids:
        with pytest.raises(PyProjectTOMLParseError):
            TomlParser(invalid, raise_exceptions=True)
        tp = TomlParser(invalid, raise_exceptions=False)
        actual = tp.d_pyproject_toml
        assert actual is None


testdata_valid_pyproject_toml = list(
    Path(__file__).parent.joinpath("_good_files").glob("*.pyproject_toml")
)


@pytest.mark.parametrize(
    "path_toml_src",
    testdata_valid_pyproject_toml,
    ids=[path.name.rsplit(".", 1)[0] for path in testdata_valid_pyproject_toml],
)
def test_get_pyproject_toml_good(path_toml_src, tmp_path, prep_pyproject_toml):
    # pytest --showlocals --log-level INFO -k "test_get_pyproject_toml_good" tests
    path_f = prep_pyproject_toml(path_toml_src, tmp_path)
    valids = (path_f,)
    for valid in valids:
        # Provide a path, not the file contents
        tp = TomlParser(valid)
        actual_dict = tp.d_pyproject_toml
        assert isinstance(actual_dict, Mapping)
        path_actual = tp.path_file
        assert issubclass(type(path_actual), PurePath)


testdata_search_for_pyproject_toml = (
    Path(__file__).parent.parent,
    Path(__file__).parent,
)
ids_search_for_pyproject_toml = (
    "package base folder",
    "tests folder",
)


@pytest.mark.parametrize(
    "path_dir",
    testdata_search_for_pyproject_toml,
    ids=ids_search_for_pyproject_toml,
)
def test_search_for_pyproject_toml(path_dir):
    # pytest --showlocals --log-level INFO -k "test_get_pyproject_toml_dir" tests
    tp = TomlParser(path_dir, raise_exceptions=True)
    actual = tp.d_pyproject_toml
    assert isinstance(actual, Mapping)

    # classmethod TomlParser.resolve accepts str
    dir_path = str(path_dir)
    actual = TomlParser.resolve(dir_path)
    assert issubclass(type(actual), PurePath)


def test_pyproject_toml_search_fail(tmp_path):
    # pytest --showlocals --log-level INFO -k "test_pyproject_toml_search_fail" tests
    # there should be no pyproject.toml in the reverse path
    path_f = tmp_path.joinpath("some_file.txt")
    with pytest.raises(PyProjectTOMLReadError):
        TomlParser(path_f, raise_exceptions=True)

    invalids = (
        "Go team!",
        0.1234,
    )
    for invalid in invalids:
        tp = TomlParser(path_f, raise_exceptions=invalid)
        assert tp.d_pyproject_toml is None


testdata_toml_parser_read = (
    pytest.param(
        Path(__file__).parent.joinpath("_bad_files", "backend_only.pyproject_toml"),
        marks=pytest.mark.xfail(raises=PyProjectTOMLParseError),
    ),
    pytest.param(
        Path(__file__).parent.joinpath("_good_files", "nonexistent.pyproject_toml"),
        marks=pytest.mark.xfail(raises=PyProjectTOMLReadError),
    ),
)
ids_toml_parser_read = (
    "unparsable pyproject-toml",
    "no such pyproject-toml",
)


@pytest.mark.parametrize(
    "path_toml_src",
    testdata_toml_parser_read,
    ids=ids_toml_parser_read,
)
def test_toml_parser_read(path_toml_src, tmp_path, prep_pyproject_toml):
    # pytest --showlocals --log-level INFO -k "test_toml_parser_read" -v tests
    if not path_toml_src.exists():
        path_f = tmp_path
    else:
        path_f = prep_pyproject_toml(path_toml_src, tmp_path)

    # Either could raise PyProjectTOMLParseError or PyProjectTOMLReadError
    d_pyproject_toml, path_resolved = TomlParser.read(path_f)
