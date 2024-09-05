"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

Unittest for module, drain_swamp.parser_in

Unit test -- Module

.. code-block:: shell

   python -m coverage run --source='drain_swamp.parser_in' -m pytest \
   --showlocals tests/test_parser_in.py && coverage report \
   --data-file=.coverage --include="**/parser_in.py"

Integration test

.. code-block:: shell

   make coverage
   pytest --showlocals --cov="drain_swamp" --cov-report=term-missing \
   --cov-config=pyproject.toml tests

"""

import sys
from contextlib import nullcontext as does_not_raise
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
    """Unsupported types feed to TomlParser"""
    # pytest --showlocals --log-level INFO -k "test_get_pyproject_toml_unsupported_type" tests
    with pytest.raises(PyProjectTOMLReadError):
        TomlParser(invalid, raise_exceptions=True)


testdata_random_folders_and_files = (
    (
        Path("/etc"),
        pytest.raises(PyProjectTOMLReadError),
    ),
    (
        Path("/etc/dog_shit_throwing_monkey.conf"),
        pytest.raises(PyProjectTOMLReadError),
    ),
    (
        Path("__init__.py"),
        does_not_raise(),
    ),
)
ids_random_folders_and_files = (
    "folder without a pyproject.toml in it",
    "absolute but nonexistent",
    "realitive path which shockingly resolves",
)


@pytest.mark.parametrize(
    "path_f, expectation",
    testdata_random_folders_and_files,
    ids=ids_random_folders_and_files,
)
def test_random_folders_and_files(path_f, expectation):
    """Chaos monkey various paths."""
    # pytest --showlocals --log-level INFO -k "test_random_folders_and_files" tests
    # A Path but dodgy --> FileNotFoundError
    with expectation:
        TomlParser(path_f, raise_exceptions=True)


testdata_unparsable = (
    (
        Path(__file__).parent.joinpath("_bad_files", "backend_only.pyproject_toml"),
        pytest.raises(PyProjectTOMLParseError),
    ),
)
ids_unparsable = ("backend only",)


@pytest.mark.parametrize(
    "path_toml_src, expectation",
    testdata_unparsable,
    ids=ids_unparsable,
)
def test_get_pyproject_toml_bad(
    path_toml_src,
    expectation,
    tmp_path,
    prep_pyproject_toml,
):
    """Parse a bad pyproject.toml."""
    # pytest --showlocals --log-level INFO -k "test_get_pyproject_toml_bad" tests

    # file_as_str = path.read_text()
    # Provide a path, not the file contents
    path_f = prep_pyproject_toml(path_toml_src, tmp_path)
    invalids = (path_f,)
    for invalid in invalids:
        with expectation:
            TomlParser(invalid, raise_exceptions=True)
        tp = TomlParser(invalid, raise_exceptions=False)
        actual = tp.d_pyproject_toml
        assert actual is None

        with expectation:
            TomlParser.read(path_f)

    # not a file
    invalids = (
        None,
        1.234,
    )
    for invalid in invalids:
        with pytest.raises(PyProjectTOMLReadError):
            TomlParser.read(invalid)


testdata_valid_pyproject_toml = list(
    Path(__file__).parent.joinpath("_good_files").glob("*.pyproject_toml")
)


@pytest.mark.parametrize(
    "path_toml_src",
    testdata_valid_pyproject_toml,
    ids=[path.name.rsplit(".", 1)[0] for path in testdata_valid_pyproject_toml],
)
def test_get_pyproject_toml_good(path_toml_src, tmp_path, prep_pyproject_toml):
    """Parse a valid pyproject.toml."""
    # pytest --showlocals --log-level INFO -k "test_get_pyproject_toml_good" tests
    # prepare
    path_f = prep_pyproject_toml(path_toml_src, tmp_path)

    # act
    valids = (path_f,)
    for valid in valids:
        # Provide a path, not the file contents
        tp = TomlParser(valid)
        actual_dict_0 = tp.d_pyproject_toml
        # verify
        assert isinstance(actual_dict_0, Mapping)
        path_f_0 = tp.path_file
        assert issubclass(type(path_f_0), PurePath)

        actual_dict_1, path_f_1 = TomlParser.read(valid)
        assert path_f_0 == path_f_1
        assert actual_dict_0 == actual_dict_1


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
    """TomlParser Reverse searches for pyproject.toml."""
    # pytest --showlocals --log-level INFO -k "test_get_pyproject_toml_dir" tests
    tp = TomlParser(path_dir, raise_exceptions=True)
    actual = tp.d_pyproject_toml
    assert isinstance(actual, Mapping)

    # classmethod TomlParser.resolve accepts str
    dir_path = str(path_dir)
    actual = TomlParser.resolve(dir_path)
    assert issubclass(type(actual), PurePath)


def test_pyproject_toml_search_fail(tmp_path):
    """Chaos monkey test TomlParser."""
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
    (
        Path(__file__).parent.joinpath("_bad_files", "backend_only.pyproject_toml"),
        pytest.raises(PyProjectTOMLParseError),
    ),
    (
        Path(__file__).parent.joinpath("_good_files", "nonexistent.pyproject_toml"),
        pytest.raises(PyProjectTOMLReadError),
    ),
)
ids_toml_parser_read = (
    "unparsable pyproject-toml",
    "no such pyproject-toml",
)


@pytest.mark.parametrize(
    "path_toml_src, expectation",
    testdata_toml_parser_read,
    ids=ids_toml_parser_read,
)
def test_toml_parser_read(path_toml_src, expectation, tmp_path, prep_pyproject_toml):
    """Parse pyproject.toml file with TomlParser."""
    # pytest --showlocals --log-level INFO -k "test_toml_parser_read" -v tests
    if not path_toml_src.exists():
        path_f = tmp_path
    else:
        path_f = prep_pyproject_toml(path_toml_src, tmp_path)

    # Either could raise PyProjectTOMLParseError or PyProjectTOMLReadError
    with expectation:
        TomlParser.read(path_f)
