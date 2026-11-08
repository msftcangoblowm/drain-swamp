"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

With coverage

.. code-block:: shell

   python -m coverage run --source='drain_swamp.package_metadata' -m pytest \
   --showlocals tests/test_package_metadata.py && coverage report \
   --data-file=.coverage --include="**/package_metadata.py"

Integration test

.. code-block:: shell

   make coverage
   pytest --showlocals --cov="drain_swamp" --cov-report=term-missing \
   --cov-config=pyproject.toml tests

"""

from contextlib import nullcontext as does_not_raise
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
from wreck._package_installed import is_package_installed

from drain_swamp.constants import g_app_name
from drain_swamp.package_metadata import (
    AUTHOR_NAME_FALLBACK,
    PackageMetadata,
    get_author_and_email,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from .typing_only import DOES_NOT_OR_DOES


@pytest.mark.parametrize(
    "app_name, is_installed, author_name_expected, author_email_expected",
    (
        pytest.param(
            "blarneys_blowup_doll",
            False,
            AUTHOR_NAME_FALLBACK,
            None,
            id="nonexistent-package.-Not-installed",
        ),
        pytest.param(
            "drain_swamp",
            True,
            "Dave Faulkmore",
            "faulkmore@protonmail.com",
            id="existent-package.-Installed",
        ),
    ),
)
def test_play_with_cache(
    app_name: str,
    is_installed: bool,
    author_name_expected: str,
    author_email_expected: str,
) -> None:
    """If package is not installed, then author cache will contain only fallbacks."""
    # pytest --showlocals --log-level INFO -k "test_play_with_cache" tests
    assert is_package_installed(app_name) is is_installed
    author_name, author_email = get_author_and_email(app_name)
    assert author_name == author_name_expected
    assert author_email == author_email_expected


@pytest.mark.parametrize(
    "app_name, relpath_config, expected_name, expected_email, expectation",
    (
        pytest.param(
            "blarneys_blowup_doll",
            None,
            AUTHOR_NAME_FALLBACK,
            None,
            does_not_raise(),
            id="Unsupported-type.-Expected-Path-got-None",
        ),
        pytest.param(
            "blarneys_blowup_doll",
            1.1234,
            AUTHOR_NAME_FALLBACK,
            None,
            does_not_raise(),
            id="Unsupported=type.-Expected-Path-got-float",
        ),
        pytest.param(
            "blarneys_blowup_doll",
            Path("_good_files").joinpath("complete.pyproject_toml"),
            AUTHOR_NAME_FALLBACK,
            None,
            does_not_raise(),
            id="pyproject.toml=lacks-author-name-and-email",
        ),
        pytest.param(
            "blarneys_blowup_doll",
            Path("_bad_files").joinpath("backend_only.pyproject_toml"),
            AUTHOR_NAME_FALLBACK,
            None,
            does_not_raise(),
            id="invalid-pyproject.toml.-Cannot-parse",
        ),
        pytest.param(
            "blarneys_blowup_doll",
            Path("_good_files").joinpath("no_project_name.pyproject_toml"),
            "Dave Faulkmore",
            "faulkmore@protonmail.com",
            does_not_raise(),
            id="pyproject.toml-has-author-name-and-email",
        ),
        pytest.param(
            None,
            Path("_good_files").joinpath("complete.pyproject_toml"),
            None,
            None,
            pytest.raises(ValueError),
            id="app-name-is-None",
        ),
        pytest.param(
            "",
            Path("_good_files").joinpath("complete.pyproject_toml"),
            None,
            None,
            pytest.raises(ValueError),
            id="app-name-is-empty",
        ),
        pytest.param(
            "   ",
            Path("_good_files").joinpath("complete.pyproject_toml"),
            None,
            None,
            pytest.raises(ValueError),
            id="app-name-is-non-empty=whitespace",
        ),
        pytest.param(
            "complete-awesome-perfect",
            Path("_good_files").joinpath("complete.pyproject_toml"),
            "Anonymous",
            None,
            does_not_raise(),
            id="matching-package-name.-No-author-name-nor-email-address",
        ),
    ),
)
def test_package_metadata_construct(
    app_name: str | None,
    relpath_config: "Path | float | None",
    expected_name: str | None,
    expected_email: str | None,
    expectation: "DOES_NOT_OR_DOES",
    tmp_path: "Path",
    request: pytest.FixtureRequest,
    prep_pyproject_toml: "Callable[[Path, Path, Path | str | None], Path]",
) -> None:
    """Retrieve author first name and email from package metadata."""
    # pytest --showlocals --log-level INFO -k "test_package_metadata_construct" tests
    if TYPE_CHECKING:
        abspath_config: Path | float | None

    abspath_tests_dir = request.path.parent
    if relpath_config is None or isinstance(relpath_config, float):
        abspath_config = relpath_config
    else:
        abspath_config = abspath_tests_dir.joinpath(relpath_config)

    # prepare
    path_pyproject_toml = prep_pyproject_toml(
        abspath_config,  # type: ignore[arg-type]
        tmp_path,
    )

    # nonexistent package. Just checked, it's available.
    with expectation:
        pm = PackageMetadata(app_name, path=path_pyproject_toml)
    if isinstance(expectation, does_not_raise):
        assert pm.full_name == expected_name
        assert pm.email == expected_email
        assert pm.left_name in expected_name
        if pm.email is not None:
            assert isinstance(pm.d_pyproject_toml, dict)


@pytest.mark.parametrize(
    "app_name, relpath_config, expected_name, expected_email, expectation",
    (
        pytest.param(
            "complete-awesome-perfect",
            Path("_good_files").joinpath("complete.pyproject_toml"),
            "Anonymous",
            None,
            does_not_raise(),
            id="no-author-email-anonymous",
        ),
    ),
)
def test_package_construct_with_patch(
    app_name: str,
    relpath_config: "Path",
    expected_name: str,
    expected_email: str | None,
    expectation: "DOES_NOT_OR_DOES",
    tmp_path: "Path",
    request: pytest.FixtureRequest,
    prep_pyproject_toml: "Callable[[Path, Path, Path | None], Path | None]",
) -> None:
    """Patch it til you make it."""
    # pytest --showlocals --log-level INFO -k "test_package_metadata_construct" tests
    abspath_tests_dir = request.path.parent
    abspath_config = abspath_tests_dir.joinpath(relpath_config)

    # prepare
    #    pyproject.toml
    path_pyproject_toml = prep_pyproject_toml(abspath_config, tmp_path)

    with expectation:
        with patch(
            f"{g_app_name}.package_metadata.is_package_installed",
            return_value=True,
        ):
            with patch(
                f"{g_app_name}.package_metadata.get_author_and_email",
                return_value=(expected_name, expected_email),
            ):
                pm = PackageMetadata(app_name, path=path_pyproject_toml)
                assert pm.full_name == expected_name
                assert pm.email == expected_email
