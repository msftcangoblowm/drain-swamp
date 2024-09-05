"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

Unit test -- Module

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
from unittest.mock import patch

import pytest

from drain_swamp._package_installed import is_package_installed
from drain_swamp.constants import g_app_name
from drain_swamp.package_metadata import (
    AUTHOR_NAME_FALLBACK,
    PackageMetadata,
    get_author_and_email,
)

testdata_play_with_cache = (
    (
        "blarneys_blowup_doll",
        False,
        AUTHOR_NAME_FALLBACK,
        None,
    ),
    (
        "drain_swamp",
        True,
        "Dave Faulkmore",
        "faulkmore@protonmail.com",
    ),
)
ids_play_with_cache = (
    "nonexistant package. Not installed",
    "existant package. Installed",
)


@pytest.mark.parametrize(
    "app_name, is_installed, author_name_expected, author_email_expected",
    testdata_play_with_cache,
    ids=ids_play_with_cache,
)
def test_play_with_cache(
    app_name,
    is_installed,
    author_name_expected,
    author_email_expected,
):
    """If package is not installed, then author cache will contain only fallbacks."""
    # pytest --showlocals --log-level INFO -k "test_play_with_cache" tests
    assert is_package_installed(app_name) is is_installed
    author_name, author_email = get_author_and_email(app_name)
    assert author_name == author_name_expected
    assert author_email == author_email_expected


testdata_package_metadata_construct = (
    (
        "blarneys_blowup_doll",
        None,
        AUTHOR_NAME_FALLBACK,
        None,
        does_not_raise(),
    ),
    (
        "blarneys_blowup_doll",
        1.1234,
        AUTHOR_NAME_FALLBACK,
        None,
        does_not_raise(),
    ),
    (
        "blarneys_blowup_doll",
        Path(__file__).parent.joinpath("_good_files", "complete.pyproject_toml"),
        AUTHOR_NAME_FALLBACK,
        None,
        does_not_raise(),
    ),
    (
        "blarneys_blowup_doll",
        Path(__file__).parent.joinpath("_bad_files", "backend_only.pyproject_toml"),
        AUTHOR_NAME_FALLBACK,
        None,
        does_not_raise(),
    ),
    (
        "blarneys_blowup_doll",
        Path(__file__).parent.joinpath("_good_files", "no_project_name.pyproject_toml"),
        "Dave Faulkmore",
        "faulkmore@protonmail.com",
        does_not_raise(),
    ),
    (
        None,
        Path(__file__).parent.joinpath("_good_files", "complete.pyproject_toml"),
        None,
        None,
        pytest.raises(ValueError),
    ),
    (
        "",
        Path(__file__).parent.joinpath("_good_files", "complete.pyproject_toml"),
        None,
        None,
        pytest.raises(ValueError),
    ),
    (
        "   ",
        Path(__file__).parent.joinpath("_good_files", "complete.pyproject_toml"),
        None,
        None,
        pytest.raises(ValueError),
    ),
    (
        "complete-awesome-perfect",
        Path(__file__).parent.joinpath("_good_files", "complete.pyproject_toml"),
        "Anonymous",
        None,
        does_not_raise(),
    ),
)

ids_package_metadata_construct = (
    "Unsupported type. Expected Path got None",
    "Unsupported type. Expected Path got float",
    "pyproject.toml lacks author name and email",
    "invalid pyproject.toml. Cannot parse",
    "pyproject.toml has author name and email",
    "app name is None",
    "app name is empty",
    "app name is non-empty whitespace",
    "matching package name. No author name nor email address",
)


@pytest.mark.parametrize(
    "app_name, path_config, expected_name, expected_email, expectation",
    testdata_package_metadata_construct,
    ids=ids_package_metadata_construct,
)
def test_package_metadata_construct(
    app_name,
    path_config,
    expected_name,
    expected_email,
    expectation,
    tmp_path,
    prep_pyproject_toml,
):
    """Retrieve author first name and email from package metadata."""
    # pytest --showlocals --log-level INFO -k "test_package_metadata_construct" tests
    # prepare
    path_pyproject_toml = prep_pyproject_toml(path_config, tmp_path)

    # nonexistent package. Just checked, it's available.
    with expectation:
        pm = PackageMetadata(app_name, path=path_pyproject_toml)
    if isinstance(expectation, does_not_raise):
        assert pm.full_name == expected_name
        assert pm.email == expected_email
        assert pm.left_name in expected_name
        if pm.email is not None:
            assert isinstance(pm.d_pyproject_toml, dict)


testdata_package_construct_with_patch = (
    (
        "complete-awesome-perfect",
        Path(__file__).parent.joinpath("_good_files", "complete.pyproject_toml"),
        "Anonymous",
        None,
        does_not_raise(),
    ),
)
ids_package_construct_with_patch = ("",)


@pytest.mark.parametrize(
    "app_name, path_config, expected_name, expected_email, expectation",
    testdata_package_construct_with_patch,
    ids=ids_package_construct_with_patch,
)
def test_package_construct_with_patch(
    app_name,
    path_config,
    expected_name,
    expected_email,
    expectation,
    tmp_path,
    prep_pyproject_toml,
):
    """Patch it til you make it."""
    # pytest --showlocals --log-level INFO -k "test_package_metadata_construct" tests
    # prepare
    #    pyproject.toml
    path_pyproject_toml = prep_pyproject_toml(path_config, tmp_path)

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
