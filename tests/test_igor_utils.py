"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

Without coverage

.. code-block:: shell

   pytest --showlocals --log-level INFO tests/test_igor_utils.py

With coverage

Needs a config file to specify exact files to include / omit from report.
Will fail with exit code 1 even with 100% coverage

.. code-block:: shell

   pytest --showlocals --cov="drain_swamp" --cov-report=term-missing tests/test_igor_utils.py

"""

import logging
import logging.config
import re
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from drain_swamp.constants import (
    LOGGING,
    g_app_name,
)
from drain_swamp.igor_utils import (
    SCRIV_START,
    UNRELEASED,
    build_package,
    edit_for_release,
    seed_changelog,
    update_file,
)
from drain_swamp.version_semantic import SetuptoolsSCMNoTaggedVersionError


def test_update_file(tmp_path, prep_pyproject_toml):
    invalids = (
        None,
        "",
        "   ",
        1.2345,
    )
    pattern = re.escape(SCRIV_START)
    replacement = f"{UNRELEASED}\n\nNothing yet.\n\n\n" + SCRIV_START
    for invalid in invalids:
        out = update_file(invalid, pattern, replacement)
        assert out is None

    # not absolute Path
    rel_path = Path("hi/there")
    out = update_file(rel_path, pattern, replacement)
    assert out is None

    # Need a successful replacement, with differencing file content afterwards
    path_change_rst = Path(__file__).parent.joinpath(
        "_changelog_files",
        "CHANGES-empty.rst",
    )
    path_empty = prep_pyproject_toml(path_change_rst, tmp_path, rename="CHANGES.rst")
    existing_text = path_empty.read_text()
    update_file(
        path_empty,
        pattern,
        replacement,
    )
    actual_text = path_empty.read_text()
    assert existing_text != actual_text
    assert "Nothing yet." in actual_text


def test_seed_changelog(tmp_path, prep_pyproject_toml):
    path_change_rst = Path(__file__).parent.joinpath(
        "_changelog_files",
        "CHANGES-empty.rst",
    )
    path_empty = prep_pyproject_toml(path_change_rst, tmp_path, rename="CHANGES.rst")
    existing_text = path_empty.read_text()
    seed_changelog(tmp_path)
    actual_text = path_empty.read_text()
    assert existing_text != actual_text
    assert "Nothing yet." in actual_text


testdata_edit_for_release = (
    (
        Path(__file__).parent.joinpath("_changelog_files", "CHANGES-empty.rst"),
        Path(__file__).parent.joinpath("_changelog_files", "NOTICE-empty.txt"),
        Path(__file__).parent.joinpath(
            "test_snip", "test_snip_harden_one_snip__with_id_.txt"
        ),
        Path(__file__).parent.joinpath("_good_files", "no_project_name.pyproject_toml"),
        "asdf",
        "0.0.1",
        2,
    ),
    (
        Path(__file__).parent.joinpath("_changelog_files", "CHANGES-empty.rst"),
        Path(__file__).parent.joinpath("_changelog_files", "NOTICE-empty.txt"),
        Path(__file__).parent.joinpath(
            "test_snip", "test_snip_harden_one_snip__with_id_.txt"
        ),
        Path(__file__).parent.joinpath("_good_files", "no_copyright.pyproject_toml"),
        "asdf",
        "0.0.1",
        None,
    ),
    (
        Path(__file__).parent.joinpath("_changelog_files", "CHANGES-empty.rst"),
        Path(__file__).parent.joinpath("_changelog_files", "NOTICE-empty.txt"),
        Path(__file__).parent.joinpath(
            "test_snip", "test_snip_harden_one_snip__with_id_.txt"
        ),
        Path(__file__).parent.joinpath("_good_files", "no_copyright.pyproject_toml"),
        "asdf",
        "0.0.1.dev0",
        None,
    ),
    (
        Path(__file__).parent.joinpath("_changelog_files", "CHANGES-empty.rst"),
        Path(__file__).parent.joinpath("_changelog_files", "NOTICE-empty.txt"),
        Path(__file__).parent.joinpath(
            "test_snip", "test_snip_harden_one_snip__with_id_.txt"
        ),
        Path(__file__).parent.joinpath("_good_files", "weird_copyright.pyproject_toml"),
        "asdf",
        "0.0.1",
        None,
    ),
    (
        Path(__file__).parent.joinpath("_changelog_files", "CHANGES-empty.rst"),
        Path(__file__).parent.joinpath("_changelog_files", "NOTICE-empty.txt"),
        Path(__file__).parent.joinpath(
            "test_snip", "test_snip_harden_one_snip__with_id_.txt"
        ),
        Path(__file__).parent.joinpath(
            "_good_files", "weird_copyright-2.pyproject_toml"
        ),
        "asdf",
        "0.0.1",
        None,
    ),
)
ids_edit_for_release = (
    "has copyright start year",
    "no copyright start year",
    "no copyright start year. dev release",
    "float copyright start year",
    "str not an int copyright start year",
)


@pytest.mark.parametrize(
    "path_changes, path_notice, path_snip, path_pyproject_toml, snippet_co, sem_version_str, expected_exit_co",
    testdata_edit_for_release,
    ids=ids_edit_for_release,
)
def test_edit_for_release(
    path_changes,
    path_notice,
    path_snip,
    path_pyproject_toml,
    snippet_co,
    sem_version_str,
    expected_exit_co,
    tmp_path,
    prep_pyproject_toml,
    caplog,
    has_logging_occurred,
):
    LOGGING["loggers"][g_app_name]["propagate"] = True
    logging.config.dictConfig(LOGGING)
    logger = logging.getLogger(name=g_app_name)
    logger.addHandler(hdlr=caplog.handler)
    caplog.handler.level = logger.level

    cmd = []
    kind = sem_version_str

    # prepare
    prep_pyproject_toml(path_changes, tmp_path, rename="CHANGES.rst")
    prep_pyproject_toml(path_notice, tmp_path, rename="NOTICE.txt")

    # before prepare of docs/conf.py
    opt_int = edit_for_release(tmp_path, kind, snippet_co=snippet_co)
    assert opt_int is not None
    assert opt_int == 1

    #    create docs/ folder
    path_docs = tmp_path.joinpath("docs")
    path_docs.mkdir()

    #    docs/conf.py
    prep_pyproject_toml(path_snip, path_docs, rename="conf.py")

    #    pyproject.toml
    prep_pyproject_toml(
        path_pyproject_toml,
        tmp_path,
        rename="pyproject.toml",
    )

    # unittest.mock.patch to prevent changes to _version.py
    # properties; defang so doesn't change src/[proj name]/_version.py
    with (
        patch(
            "subprocess.run",
            return_value=subprocess.CompletedProcess(
                cmd,
                returncode=0,
                stdout=sem_version_str,
            ),
        ),
    ):
        opt_int = edit_for_release(tmp_path, kind, snippet_co=snippet_co)
    if expected_exit_co is None:
        assert opt_int is expected_exit_co
    else:
        assert opt_int == expected_exit_co

    # assert has_logging_occurred(caplog)
    pass


def test_build_package(tmp_path):
    """Fake world fake building package"""
    # Not a folder
    path_passwd = tmp_path.joinpath("password-secret.txt")
    path_passwd.touch()
    kind = "five element spirit or nature?"
    with pytest.raises(NotADirectoryError):
        build_package(path_passwd, kind, package_name=None)

    # semantic version str is bad --> ValueError
    with pytest.raises(ValueError):
        build_package(tmp_path, kind, package_name=g_app_name)

    # package_name is a non-empty str -->
    # build_package --> clean_version --> _tag_version  -> AssertionError
    kind = "tag"
    invalids = (
        None,
        "",
        "   ",
        1.2345,
    )
    for invalid in invalids:
        with (
            patch(f"{g_app_name}.version_semantic._get_app_name", return_value=None),
            pytest.raises(AssertionError),
        ):
            build_package(tmp_path, kind, package_name=invalid)

    # simulate no initial git tag --> kind either current or now
    kinds = (
        "now",
        "current",
    )
    for kind in kinds:
        with (
            patch(
                f"{g_app_name}.version_semantic._current_version",
                return_value=None,
            ),
            pytest.raises(SetuptoolsSCMNoTaggedVersionError),
        ):
            build_package(tmp_path, kind, package_name=g_app_name)

    # simulate no initial git tag --> kind == tag
    kind = "tag"
    with (
        patch(f"{g_app_name}.version_semantic._tag_version", return_value=None),
        patch(
            f"{g_app_name}.version_semantic._current_version",
            return_value=None,
        ),
        pytest.raises(SetuptoolsSCMNoTaggedVersionError),
    ):
        build_package(tmp_path, kind, package_name=g_app_name)

    # build fail
    cmd = []
    kind = "0.0.1"
    with (
        patch(
            "subprocess.run",
            side_effect=subprocess.CalledProcessError(128, cmd),
        ),
    ):
        bool_out = build_package(tmp_path, kind, package_name=g_app_name)
        assert bool_out is False

    with (
        patch(
            "subprocess.run",
            return_value=subprocess.CompletedProcess(
                cmd,
                returncode=128,
                stdout="fatal: No names found, cannot describe anything.",
            ),
        ),
    ):
        bool_out = build_package(tmp_path, kind, package_name=g_app_name)
        assert bool_out is False

    # build success
    with (
        patch(
            "subprocess.run",
            return_value=subprocess.CompletedProcess(
                cmd,
                returncode=0,
                stdout="You just installed the best package and dependencies ... ever",
            ),
        ),
    ):
        bool_out = build_package(tmp_path, kind, package_name=g_app_name)
        assert bool_out is True
