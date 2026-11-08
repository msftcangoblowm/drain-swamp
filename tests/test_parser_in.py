"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

Unittest for module, drain_swamp.parser_in

With coverage

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

import platform
from collections.abc import Mapping
from contextlib import nullcontext as does_not_raise
from pathlib import (
    Path,
    PurePath,
)
from typing import TYPE_CHECKING

import pytest

from drain_swamp.exceptions import (
    PyProjectTOMLParseError,
    PyProjectTOMLReadError,
)
from drain_swamp.parser_in import TomlParser

if TYPE_CHECKING:
    from collections.abc import Callable

    from .typing_only import DOES_NOT_OR_DOES


@pytest.mark.parametrize(
    "invalid, expectation",
    (
        pytest.param(
            None,
            pytest.raises(PyProjectTOMLReadError),
            id="None",
        ),
        pytest.param(
            "Hello world!",
            pytest.raises(PyProjectTOMLReadError),
            id="str",
        ),
        pytest.param(
            1.1234,
            pytest.raises(PyProjectTOMLReadError),
            id="float",
        ),
        pytest.param(
            1,
            pytest.raises(PyProjectTOMLReadError),
            id="int",
        ),
        pytest.param(
            Path("/etc"),
            pytest.raises(PyProjectTOMLReadError),
            marks=pytest.mark.skipif(
                platform.system().lower() != "linux",
                reason="linux like fs path",
            ),
            id="folder-without-a-pyproject.toml-in-it",
        ),
        pytest.param(
            Path("/etc/dog_shit_throwing_monkey.conf"),
            pytest.raises(PyProjectTOMLReadError),
            marks=pytest.mark.skipif(
                platform.system().lower() != "linux",
                reason="linux like fs path",
            ),
            id="absolute-but-nonexistent",
        ),
        pytest.param(
            Path("__init__.py"),
            does_not_raise(),
            id="relative-path-which-shockingly-resolves",
        ),
    ),
)
def test_get_pyproject_toml_path_and_unsupported_type(
    invalid: "Path | str | float | int | None",
    expectation: "DOES_NOT_OR_DOES",
) -> None:
    """Unsupported types feed to TomlParser"""
    # pytest --showlocals --log-level INFO -k "test_get_pyproject_toml_path_and_unsupported_type" tests
    #    If a Path but dodgy --> FileNotFoundError
    with expectation:
        TomlParser(
            invalid,  # type: ignore[arg-type]
            raise_exceptions=True,
        )


@pytest.mark.parametrize(
    "relpath_toml_src, expectation",
    (
        pytest.param(
            Path("_bad_files").joinpath("backend_only.pyproject_toml"),
            pytest.raises(PyProjectTOMLParseError),
            id="backend-only",
        ),
    ),
)
def test_get_pyproject_toml_bad(
    relpath_toml_src: "Path",
    expectation: "DOES_NOT_OR_DOES",
    tmp_path: "Path",
    request: pytest.FixtureRequest,
    prep_pyproject_toml: "Callable[[Path, Path, Path | None], Path | None]",
) -> None:
    """Parse a bad pyproject.toml."""
    # pytest --showlocals --log-level INFO -k "test_get_pyproject_toml_bad" tests
    abspath_tests_dir = request.path.parent
    abspath_toml_src = abspath_tests_dir.joinpath(relpath_toml_src)

    # file_as_str = path.read_text()
    # Provide a path, not the file contents
    path_f = prep_pyproject_toml(abspath_toml_src, tmp_path)
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
def test_get_pyproject_toml_good(
    path_toml_src: "Path",
    tmp_path: "Path",
    prep_pyproject_toml: "Callable[[Path, Path, Path | None], Path | None]",
) -> None:
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


@pytest.mark.parametrize(
    "path_dir",
    (
        pytest.param(
            Path(__file__).parent.parent,
            id="package-base-folder",
        ),
        pytest.param(
            Path(__file__).parent,
            id="tests-folder",
        ),
    ),
)
def test_search_for_pyproject_toml(path_dir: "Path") -> None:
    """TomlParser Reverse searches for pyproject.toml."""
    # pytest --showlocals --log-level INFO -k "test_get_pyproject_toml_dir" tests
    tp = TomlParser(path_dir, raise_exceptions=True)
    actual = tp.d_pyproject_toml
    assert isinstance(actual, Mapping)

    # classmethod TomlParser.resolve accepts str
    dir_path = str(path_dir)
    actual = TomlParser.resolve(dir_path)
    assert issubclass(type(actual), PurePath)


def test_pyproject_toml_search_fail(tmp_path: "Path") -> None:
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


@pytest.mark.parametrize(
    "relpath_toml_src, expectation",
    (
        pytest.param(
            Path("_bad_files").joinpath("backend_only.pyproject_toml"),
            pytest.raises(PyProjectTOMLParseError),
            id="unparsable-pyproject-toml",
        ),
        pytest.param(
            Path("_good_files").joinpath("nonexistent.pyproject_toml"),
            pytest.raises(PyProjectTOMLReadError),
            id="no-such-pyproject-toml",
        ),
    ),
)
def test_toml_parser_read(
    relpath_toml_src: "Path",
    expectation: "DOES_NOT_OR_DOES",
    tmp_path: "Path",
    request: pytest.FixtureRequest,
    prep_pyproject_toml: "Callable[[Path, Path, Path | None], Path | None]",
) -> None:
    """Parse pyproject.toml file with TomlParser."""
    # pytest --showlocals --log-level INFO -k "test_toml_parser_read" -v tests
    abspath_tests_dir = request.path.parent
    abspath_toml_src = abspath_tests_dir.joinpath(relpath_toml_src)

    if not abspath_toml_src.exists():
        path_f = tmp_path
    else:
        path_f = prep_pyproject_toml(abspath_toml_src, tmp_path)

    # Either could raise PyProjectTOMLParseError or PyProjectTOMLReadError
    with expectation:
        TomlParser.read(path_f)
