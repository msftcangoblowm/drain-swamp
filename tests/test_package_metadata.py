"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

.. code-block:: shell

   pytest --showlocals --log-level INFO tests/test_package_metadata.py
   pytest --showlocals --cov="drain_swamp" --cov-report=term-missing tests/test_package_metadata.py

Needs a config file to specify exact files to include / omit from report.
Will fail with exit code 1 even with 100% coverage

"""

from pathlib import Path

import pytest

from drain_swamp._package_installed import is_package_installed
from drain_swamp.package_metadata import (
    AUTHOR_NAME_FALLBACK,
    PackageMetadata,
    get_author_and_email,
)


def test_play_with_cache():
    """If package is not installed, then author cache will contain only fallbacks"""
    app_name = "blarneys_blowup_doll"
    assert is_package_installed(app_name) is False
    author_name, author_email = get_author_and_email(app_name)
    assert author_name == AUTHOR_NAME_FALLBACK
    assert author_email is None


testdata_package_metadata_construct = (
    (
        "blarneys_blowup_doll",
        None,
        AUTHOR_NAME_FALLBACK,
        None,
    ),
    (
        "blarneys_blowup_doll",
        1.1234,
        AUTHOR_NAME_FALLBACK,
        None,
    ),
    (
        "blarneys_blowup_doll",
        Path(__file__).parent.joinpath("_good_files", "complete.pyproject_toml"),
        AUTHOR_NAME_FALLBACK,
        None,
    ),
    (
        "blarneys_blowup_doll",
        Path(__file__).parent.joinpath("_bad_files", "backend_only.pyproject_toml"),
        AUTHOR_NAME_FALLBACK,
        None,
    ),
    (
        "blarneys_blowup_doll",
        Path(__file__).parent.joinpath("_good_files", "no_project_name.pyproject_toml"),
        "Dave Faulkmore",
        "faulkmore@protonmail.com",
    ),
)

ids_package_metadata_construct = (
    "Unsupported type. Expected Path got None",
    "Unsupported type. Expected Path got float",
    "pyproject.toml lacks author name and email",
    "invalid pyproject.toml. Cannot parse",
    "pyproject.toml has author name and email",
)


@pytest.mark.parametrize(
    "app_name, path_config, expected_name, expected_email",
    testdata_package_metadata_construct,
    ids=ids_package_metadata_construct,
)
def test_package_metadata_construct(
    app_name,
    path_config,
    expected_name,
    expected_email,
    tmp_path,
    prep_pyproject_toml,
):
    # prepare
    path_pyproject_toml = prep_pyproject_toml(path_config, tmp_path)

    # app name cannot be None
    invalids = (
        None,
        "",
        "   ",
    )
    for invalid in invalids:
        with pytest.raises(ValueError):
            PackageMetadata(invalid, path=path_pyproject_toml)

    # nonexistent package. Just checked, it's available. Put the team on that right away

    pm = PackageMetadata(app_name, path=path_pyproject_toml)
    assert pm.full_name == expected_name
    assert pm.email == expected_email
    if pm.email is not None:
        assert isinstance(pm.d_pyproject_toml, dict)
