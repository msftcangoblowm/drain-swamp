"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

Build environment for taking current or tag version.

With coverage

.. code-block:: shell

   python -m coverage run --data-file=".coverage.ver.integrate" \
   --source='drain_swamp.version_semantic' -m pytest \
   --showlocals tests/test_versioning_integration.py

   python -m coverage run --data-file=".coverage.ver.unittest" \
   --source='drain_swamp.version_semantic' -m pytest \
   --showlocals tests/test_versioning_unittest.py

   python -m coverage combine --data-file=.coverage \
   .coverage.ver.integrate .coverage.ver.unittest

   coverage report \
   --data-file=.coverage --include="**/version_semantic.py"

Integration test

.. code-block:: shell

   make coverage
   pytest --showlocals --cov="drain_swamp" --cov-report=term-missing \
   --cov-config=pyproject.toml tests

"""

from contextlib import nullcontext as does_not_raise
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from wreck._safe_path import fix_relpath

from drain_swamp.constants import g_app_name
from drain_swamp.version_file.dump_version import write_version_files
from drain_swamp.version_semantic import _tag_version

if TYPE_CHECKING:
    import logging
    from collections.abc import (
        Callable,
        MutableSet,
        Sequence,
    )

    from .typing_only import DOES_NOT_OR_DOES


@pytest.mark.logging_package_name(g_app_name)
@pytest.mark.parametrize(
    "relpath_config_src, version_file_relpath, expectation, kind_expected",
    (
        pytest.param(
            Path("_good_files").joinpath(
                "complete-manage-pip-prod-unlock.pyproject_toml",
            ),
            fix_relpath("src/complete_awesome_perfect/_version.py"),
            does_not_raise(),
            "0.0.5",
            id="tool.setuptools.dynamic.version-attr-key",
        ),
        pytest.param(
            Path("_good_files").joinpath("complete-version-txt.pyproject_toml"),
            "VERSION.txt",
            does_not_raise(),
            "0.0.5",
            id="tool.setuptools.dynamic.version-file-key",
        ),
        pytest.param(
            Path("_bad_files").joinpath("complete-version-other.pyproject_toml"),
            "VERSION.rst",
            pytest.raises(ValueError),
            None,
            id="unsupported-version-file-type.-rst",
        ),
    ),
)
def test_version_file_read_normal(
    relpath_config_src: "Path",
    version_file_relpath: str,
    expectation: "DOES_NOT_OR_DOES",
    kind_expected: str | None,
    tmp_path: "Path",
    prep_pyproject_toml: "Callable[[Path, Path, Path | None], Path | None]",
    prepare_folders_files: "Callable[[Sequence[str | Path] | MutableSet[str | Path]], set[Path]]",
    logging_strict: "Callable[[], tuple[logging.Logger, Sequence[logging.Logger]]]",
    request: pytest.FixtureRequest,
    # has_logging_occurred,
) -> None:
    """Version file contains the tag version, retrieve it. Does not depend on git."""
    # pytest --showlocals --log-level INFO -k "test_version_file_read_normal" tests
    abspath_tests_dir = request.path.parent
    abspath_config_src = abspath_tests_dir.joinpath(relpath_config_src)

    t_two = logging_strict()
    logger, loggers = t_two

    kind = "0.0.5"

    relpath_version_file = Path(version_file_relpath)
    write_to = relpath_version_file

    # prepare
    #    base package folder
    path_cwd = tmp_path / "complete_awesome_perfect"
    path_cwd.mkdir()

    #    package code folder
    path_dir_dest = path_cwd.joinpath("src", "complete_awesome_perfect")
    path_dir_dest.mkdir(parents=True)

    path_f = path_cwd / relpath_version_file

    #    pyproject.toml
    prep_pyproject_toml(abspath_config_src, path_cwd)

    # get tag version, but no existing file
    next_versions = (
        None,
        "",
        "   ",  # whitespace only
        0.1234,  # unsupported version
    )
    for next_version in next_versions:
        with pytest.warns(UserWarning) as w:
            # static dependency would be read from pyproject.toml
            # so actual is not always None
            actual = _tag_version(
                next_version=next_version,
                path=path_cwd,
            )
            assert len(w) == 1
            assert str(w[0].message) != 0
            assert actual is None

    #    _version.py|VERSION.txt -- empty file
    seq_empties = (version_file_relpath,)
    prepare_folders_files(seq_empties, path_cwd)

    # act
    with expectation:
        write_version_files(kind, path_cwd, write_to, None)
    if isinstance(expectation, does_not_raise):
        # verify
        contents_actual = path_f.read_text()
        if kind_expected is None:
            assert contents_actual is None
        else:
            assert kind in contents_actual

        # next_version empty str | just whitespace | None --> no write to version_file
        for next_version in next_versions:
            actual = _tag_version(
                next_version=next_version,
                path=path_cwd,
            )
            assert isinstance(actual, str)

        # assert has_logging_occurred(caplog)
        pass


@pytest.mark.parametrize(
    "relpath_config_src, version_file_relpath, kind_expected",
    (
        pytest.param(
            Path("_bad_files").joinpath("static-version.pyproject_toml"),
            fix_relpath("src/complete_awesome_perfect/_version.py"),
            "0.0.5",
            id="project.version-not-dynamic",
        ),
    ),
)
def test_version_file_read_special(
    relpath_config_src: "Path",
    version_file_relpath: str,
    kind_expected: str,
    tmp_path: "Path",
    caplog: pytest.LogCaptureFixture,
    prep_pyproject_toml: "Callable[[Path, Path, Path | None], Path | None]",
    prepare_folders_files: "Callable[[Sequence[str | Path] | MutableSet[str | Path]], set[Path]]",
    has_logging_occurred: "Callable[[], bool]",
    request: pytest.FixtureRequest,
) -> None:
    """Test write_version_files."""
    # pytest --showlocals --log-level INFO -k "test_version_file_read_special" tests
    abspath_tests_dir = request.path.parent
    abspath_config_src = abspath_tests_dir.joinpath(relpath_config_src)

    kind = "0.0.5"
    relpath_version_file = Path(version_file_relpath)
    write_to = relpath_version_file

    # prepare
    #    base package folder
    path_cwd = tmp_path / "complete_awesome_perfect"
    path_cwd.mkdir()

    #    package code folder
    path_dir_dest = path_cwd.joinpath("src", "complete_awesome_perfect")
    path_dir_dest.mkdir(parents=True)

    path_f = path_cwd / relpath_version_file

    #    pyproject.toml
    prep_pyproject_toml(abspath_config_src, path_cwd)

    #    _version.py|VERSION.txt -- empty file
    seq_empties = (version_file_relpath,)
    prepare_folders_files(seq_empties, path_cwd)

    # act
    write_version_files(kind, path_cwd, write_to, None)

    # confirm
    contents_actual = path_f.read_text()
    if kind_expected is None:
        assert contents_actual is None
    else:
        assert kind in contents_actual

    next_versions = (
        None,
        "",
        "   ",  # whitespace only
        0.1234,  # unsupported version
    )
    for next_version in next_versions:
        actual = _tag_version(
            next_version=next_version,
            path=path_cwd,
        )
        assert isinstance(actual, str)


@pytest.mark.parametrize(
    "relpath_config_src, base_folder_path, next_version",
    (
        pytest.param(
            Path("_good_files").joinpath("backend-only.pyproject_toml"),
            "complete_awesome_perfect",
            None,
            id="invalid-version-file-None",
        ),
        pytest.param(
            Path("_good_files").joinpath("backend-only.pyproject_toml"),
            "complete_awesome_perfect",
            "",
            id="invalid-version-file-empty-str",
        ),
        pytest.param(
            Path("_good_files").joinpath("backend-only.pyproject_toml"),
            "complete_awesome_perfect",
            "   ",
            id="invalid-version-file-whitespace-only",
        ),
        pytest.param(
            Path("_good_files").joinpath("backend-only.pyproject_toml"),
            "complete_awesome_perfect",
            0.1234,
            id="invalid-version-file-unsupported-type-float",
        ),
    ),
)
def test_version_file_read_invalid(
    relpath_config_src: "Path",
    base_folder_path: str,
    next_version: str | float | None,
    tmp_path: "Path",
    request: pytest.FixtureRequest,
    prep_pyproject_toml: "Callable[[Path, Path, Path | None], Path | None]",
    prepare_folders_files: "Callable[[Sequence[str | Path] | MutableSet[str | Path]], set[Path]]",
) -> None:
    """Test version file read issues."""
    # pytest --showlocals --log-level INFO -k "test_version_file_read_invalid" tests
    abspath_tests_dir = request.path.parent
    abspath_config_src = abspath_tests_dir.joinpath(relpath_config_src)

    # prepare -- base package folder
    path_cwd = tmp_path / base_folder_path
    path_cwd.mkdir()

    # prepare -- pyproject.toml
    prep_pyproject_toml(abspath_config_src, path_cwd)

    with pytest.warns(UserWarning) as w:
        actual = _tag_version(
            next_version=next_version,  # type: ignore[arg-type]
            path=path_cwd,
        )
        assert len(w) == 1
        assert str(w[0].message) != 0
        assert actual is None
