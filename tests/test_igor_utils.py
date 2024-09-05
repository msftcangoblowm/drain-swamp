"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

Unit test -- Module

.. code-block:: shell

   python -m coverage run --source='drain_swamp.igor_utils' -m pytest \
   --showlocals tests/test_igor_utils.py && coverage report \
   --data-file=.coverage --include="**/igor_utils.py"

Integration test

.. code-block:: shell

   make coverage
   pytest --showlocals --cov="drain_swamp" --cov-report=term-missing \
   --cov-config=pyproject.toml tests

"""

import contextlib
import io
import logging
import logging.config
import re
import subprocess
from contextlib import nullcontext as does_not_raise
from pathlib import (
    Path,
    PurePath,
)
from unittest.mock import (
    MagicMock,
    Mock,
    patch,
)

import pytest

from drain_swamp._package_installed import is_package_installed
from drain_swamp.constants import (
    LOGGING,
    g_app_name,
)
from drain_swamp.igor_utils import (
    SCRIV_START,
    UNRELEASED,
    AlterEnv,
    build_package,
    edit_for_release,
    get_current_version,
    get_tag_version,
    get_version_file_path,
    pretag,
    print_cheats,
    seed_changelog,
    update_file,
    write_version_file,
)
from drain_swamp.version_file.dump_version import write_version_files
from drain_swamp.version_semantic import _scm_key

testdata_update_file = (
    (
        None,
        None,
        False,
    ),
    (
        "",
        None,
        False,
    ),
    (
        "    ",
        None,
        False,
    ),
    (
        1.2345,
        None,
        False,
    ),
    (
        PurePath("hi/there"),
        None,
        False,
    ),
    (
        Path(__file__).parent.joinpath(
            "_changelog_files",
            "CHANGES-empty.rst",
        ),
        "Nothing yet.",
        True,
    ),
)
ids_update_file = (
    "None",
    "empty string len 0",
    "whitespace string len not 0",
    "unsupported type float",
    "relative path",
    "skeleton changelog",
)


@pytest.mark.parametrize(
    "rel_path, expected, is_normal",
    testdata_update_file,
    ids=ids_update_file,
)
def test_update_file(rel_path, expected, is_normal, tmp_path, prep_pyproject_toml):
    """Test update_file."""
    # pytest --showlocals --log-level INFO -k "test_update_file" tests
    pattern = re.escape(SCRIV_START)
    replacement = f"{UNRELEASED}\n\nNothing yet.\n\n\n" + SCRIV_START

    # act
    if not is_normal:
        out = update_file(rel_path, pattern, replacement)
        # verify
        assert out is None
    else:
        # prepare
        #    CHANGES.rst
        path_empty = prep_pyproject_toml(rel_path, tmp_path, rename="CHANGES.rst")
        existing_text = path_empty.read_text()

        # act
        update_file(
            path_empty,
            pattern,
            replacement,
        )
        # verify
        actual_text = path_empty.read_text()
        assert existing_text != actual_text
        assert expected in actual_text


testdata_seed_changelog = (
    (
        Path(__file__).parent.joinpath(
            "_changelog_files",
            "CHANGES-empty.rst",
        ),
        0,
    ),
    (
        Path(__file__).parent.joinpath(
            "_changelog_files",
            "CHANGES-missing-start-token.rst",
        ),
        1,
    ),
)
ids_seed_changelog = (
    "normal skeleton",
    "start token missing",
)


@pytest.mark.parametrize(
    "path_change_rst, exit_code_expected",
    testdata_seed_changelog,
    ids=ids_seed_changelog,
)
def test_seed_changelog(
    path_change_rst,
    exit_code_expected,
    tmp_path,
    prep_pyproject_toml,
):
    """Look for start token below add a seed token."""
    # pytest --showlocals --log-level INFO -k "test_seed_changelog" tests
    expected_token = "Nothing yet."

    # no prepare
    exit_code_actual = seed_changelog(tmp_path)
    assert exit_code_actual == 2

    # prepare
    path_empty = prep_pyproject_toml(path_change_rst, tmp_path, rename="CHANGES.rst")
    contents_before = path_empty.read_text()

    # act
    exit_code_actual = seed_changelog(tmp_path)

    # Verify
    #    expected exit code
    assert exit_code_actual == exit_code_expected

    #    check file state
    contents_after = path_empty.read_text()
    if exit_code_actual == 0:
        assert contents_before != contents_after
        assert expected_token in contents_after
    else:
        assert contents_before == contents_after
        assert expected_token not in contents_after


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
    """Test edit_for_release."""
    # pytest --showlocals --log-level INFO -k "test_edit_for_release" tests
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
    assert opt_int == 3

    #    create docs/ folder
    path_docs = tmp_path.joinpath("docs")
    path_docs.mkdir()

    opt_int = edit_for_release(tmp_path, kind, snippet_co=snippet_co)
    assert opt_int is not None
    assert opt_int == 4

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


def test_build_package(prep_pyproject_toml, tmp_path):
    """Fake world fake building package."""
    # pytest --showlocals --log-level INFO -k "test_build_package" tests
    # Not a folder
    path_passwd = tmp_path.joinpath("password-secret.txt")
    path_passwd.touch()
    kind = "five element spirit or nature?"
    with pytest.raises(NotADirectoryError):
        build_package(path_passwd, kind)

    # semantic version str is bad --> ValueError
    with pytest.raises(ValueError):
        build_package(tmp_path, kind)

    # package_name is a non-empty str -->
    # build_package --> version_clean --> _tag_version  -> AssertionError
    kind = "tag"
    with (
        patch(
            f"{g_app_name}.version_semantic._tag_version", side_effect=AssertionError
        ),
        pytest.raises(AssertionError),
    ):
        build_package(tmp_path, kind)

    # simulate no initial git tag --> kind either current or now
    sane_fallback = "0.0.1"
    kinds = (
        "now",
        "current",
    )
    for kind in kinds:
        with (
            patch(
                f"{g_app_name}.version_semantic._current_version",
                return_value=sane_fallback,
            ),
            pytest.raises(AssertionError),
        ):
            build_package(tmp_path, kind)

    # simulate no initial git tag --> kind == tag --> sane fallback
    kind = "tag"
    with (
        patch(f"{g_app_name}.version_semantic._tag_version", return_value=None),
        patch(
            f"{g_app_name}.version_semantic._current_version",
            return_value=sane_fallback,
        ),
        pytest.raises(AssertionError),
    ):
        build_package(tmp_path, kind)

    # No preparation of pyproject.toml
    cmd = []
    kind = "0.0.1"
    with (
        patch(
            "subprocess.run",
            side_effect=subprocess.CalledProcessError(128, cmd),
        ),
        pytest.raises(AssertionError),
    ):
        build_package(tmp_path, kind)

    # prepare pyproject.toml
    p_toml_file = Path(__file__).parent.joinpath(
        "_good_files", "complete-manage-pip-prod-unlock.pyproject_toml"
    )
    prep_pyproject_toml(p_toml_file, tmp_path)

    cmd = []
    kind = "0.0.1"
    with (
        patch(
            "subprocess.run",
            side_effect=subprocess.CalledProcessError(128, cmd),
        ),
    ):
        bool_out = build_package(tmp_path, kind)
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
        bool_out = build_package(tmp_path, kind)
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
        bool_out = build_package(tmp_path, kind)
        assert bool_out is True


testdata_pretag = (
    (
        "1!v1.0.1+g4b33a80.d20240129",
        "1.0.1",
        does_not_raise(),
    ),
    (
        "0.1.1.candidate1dev1+g4b33a80.d20240129",
        "0.1.1rc1.dev1",
        does_not_raise(),
    ),
    (
        "five element spirit or nature?",
        "Version contains invalid token. Invalid version:",
        does_not_raise(),
    ),
)
ids_pretag = (
    "with epoch locals and prepended v",
    "malformed semantic ver str raise ValueError",
    "complete garbage str that is not a semantic version str",
)


@pytest.mark.parametrize(
    "ver, expected, expectation",
    testdata_pretag,
    ids=ids_pretag,
)
def test_pretag(ver, expected, expectation):
    """Sanitize ver str.

    From just this unittest non-obvious how to sanitize a ver str containing an epoch.
    Shell escape doesn't work. Instead surround by single quotes"""
    # pytest --showlocals --log-level INFO -k "test_pretag" tests
    with expectation:
        is_success, actual = pretag(ver)
    if isinstance(expectation, does_not_raise):
        if is_success:
            assert actual == expected
        else:
            # prints the error message
            assert len(actual) != 0
            # not the fixed semantic version str
            assert expected in actual


def test_get_current_version(path_project_base):
    """Get the current version of this package. Requires package setuptools-scm."""
    ver = get_current_version(path_project_base())
    if is_package_installed("setuptools_scm"):
        assert isinstance(ver, str)
    else:
        assert ver is None


def test_print_cheats(path_project_base, prep_pyproject_toml, tmp_path):
    """Prints non-vital info. Useful urls and commands."""
    # pytest --showlocals --log-level INFO -k "test_print_cheats" tests
    path_cwd = path_project_base()
    kinds = ("tag", "current")

    # NotADirectoryError
    kind = "current"
    path_f = tmp_path.joinpath("fish.txt")
    path_f.touch()
    with pytest.raises(NotADirectoryError):
        print_cheats(path_f, kind)

    # ValueError
    with pytest.raises(ValueError):
        kind_food_bad = "'dog food tastes better than this'"
        print_cheats(path_cwd, kind_food_bad)

    # kind="tag". Missing ``pyproject.toml``. Need to prepare that
    # Only for missing or unparsable results in AssertionError.
    # For all other issues, issues warning and fallsback to current version
    kind = "tag"
    with pytest.raises(AssertionError):
        print_cheats(tmp_path, kind)

    # prepare
    p_toml_file = Path(__file__).parent.joinpath(
        "_good_files", "complete-manage-pip-prod-unlock.pyproject_toml"
    )
    prep_pyproject_toml(p_toml_file, tmp_path)

    for kind in kinds:
        with contextlib.redirect_stdout(io.StringIO()) as f:
            print_cheats(path_cwd, kind)
        out = f.getvalue()
        assert out is not None
        assert isinstance(out, str)
        assert len(out.strip()) != 0

        branches = (
            "important_branch",
            "master",
            "main",
        )
        for branch in branches:
            with (
                patch(
                    f"{g_app_name}.igor_utils._get_branch",
                    return_value=branch,
                ),
                contextlib.redirect_stdout(io.StringIO()) as f,
            ):
                print_cheats(path_cwd, kind)
            out = f.getvalue()
            assert out is not None
            assert isinstance(out, str)
            assert len(out.strip()) != 0


testdata_get_version_file_path = (
    (
        Path(__file__).parent.joinpath(
            "_good_files",
            "no_project_name.pyproject_toml",
        ),
        None,
    ),
)
ids_get_version_file_path = (
    "In pyproject.toml, missing tool.pipenv-unlock.version_file",
)


@pytest.mark.parametrize(
    "p_toml_file, expected_version_file",
    testdata_get_version_file_path,
    ids=ids_get_version_file_path,
)
def test_get_version_file_path(
    p_toml_file,
    expected_version_file,
    tmp_path,
    prep_pyproject_toml,
):
    """Test get_version_file_path."""
    # pytest --showlocals --log-level INFO -k "test_get_version_file_path" tests

    path_f = tmp_path / "pyproject.toml"
    actual_version_file = get_version_file_path(path_f)
    assert actual_version_file is None

    # prepare
    path_f = prep_pyproject_toml(p_toml_file, tmp_path)

    actual_version_file = get_version_file_path(path_f)
    assert actual_version_file == expected_version_file


testdata_alter_env = (
    (
        Path(__file__).parent.joinpath(
            "_good_files",
            "complete-manage-pip-prod-unlock.pyproject_toml",
        ),
        "complete-awesome-perfect",
    ),
)
ids_alter_env = ("Buildable package pyproject.toml",)


@pytest.mark.parametrize(
    "p_toml_file, pkg_name_expected",
    testdata_alter_env,
    ids=ids_alter_env,
)
def test_alter_env(
    p_toml_file,
    pkg_name_expected,
    path_project_base,
    prep_pyproject_toml,
    prepare_folders_files,
    tmp_path,
):
    """Test AlterEnv."""
    # pytest --showlocals --log-level INFO -k "test_alter_env" tests
    path_cwd = path_project_base()
    # NotADirectoryError
    kind = "tag"
    path_f = tmp_path.joinpath("fish.txt")
    path_f.touch()
    with pytest.raises(NotADirectoryError):
        AlterEnv(path_f, kind)

    # ValueError
    kind_food_bad = "'dog food tastes better than this'"
    with pytest.raises(ValueError):
        AlterEnv(path_cwd, kind_food_bad)

    # AssertionError -- no pyproject.toml or no project.name field
    kind = "tag"
    with pytest.raises(AssertionError):
        AlterEnv(tmp_path, kind)

    # prepare
    prep_pyproject_toml(p_toml_file, tmp_path)

    """in the tmp folder, there is no git. kind: current returns a fallback"""
    kinds = ("0.0.1",)
    for kind in kinds:
        with (
            patch(
                f"{g_app_name}.igor_utils.SemVersion.version_clean",
                return_value=kind,
            ),
        ):
            ae = AlterEnv(tmp_path, kind)
            assert ae.path_cwd == tmp_path
            assert ae.pkg_name == pkg_name_expected
            assert ae.scm_key == _scm_key(pkg_name_expected)
            assert ae.scm_val is not None
            assert ae.version_file.endswith("_version.py")

            # property setter -- AlterEnv.version_file
            invalids = (0.1, None)
            for invalid in invalids:
                with pytest.raises(TypeError):
                    ae.version_file = invalid

            # prepare -- version file (empty w/ parent folders)
            ver_file = ae.version_file
            p_ver = tmp_path.joinpath(ver_file)
            prepare_folders_files((p_ver,), tmp_path)

            write_version_file(tmp_path, kind, is_test=True)
            # confirm file size is not 0
            assert p_ver.stat().st_size != 0

            # No version file template for file type
            # write_version_file with is_test=True does not validate has template
            ver_file = "src/complete_awesome_perfect/_version.rst"
            ae.version_file = ver_file
            p_ver = ae.path_cwd.joinpath(ver_file)
            prepare_folders_files((p_ver,), tmp_path)

            write_version_file(tmp_path, kind, is_test=True)
            assert p_ver.stat().st_size == 0

            # Simulate missing tool.pipenv-unlock.version_file or non-str
            with (
                patch(
                    f"{g_app_name}.igor_utils.get_version_file_path",
                    return_value=None,
                ),
                pytest.raises(AssertionError),
            ):
                ae = AlterEnv(tmp_path, kind)


def test_write_version_file(tmp_path, prep_pyproject_toml):
    """Test write_version_file."""
    # pytest --showlocals --log-level INFO -k "test_write_version_file" tests
    # prepare
    p_toml_file = Path(__file__).parent.joinpath(
        "_good_files",
        "complete-manage-pip-prod-unlock.pyproject_toml",
    )
    prep_pyproject_toml(p_toml_file, tmp_path)

    kinds = (
        (
            "0.0.1",
            tmp_path / "_version.rst",  # no .rst template
        ),
        (
            "golf balls",  # kind bad
            tmp_path.joinpath("src", "complete_awesome_perfect", "_version.py"),
        ),
    )
    for kind, path_f in kinds:
        mock_cls = MagicMock(wraps=AlterEnv, spec=AlterEnv)
        mock_cls.path_cwd.return_value = tmp_path
        mock_cls.scm_val = Mock(spec=kind, return_value=kind)
        mock_cls.version_file.return_value = str(path_f)

        with (
            patch(
                "drain_swamp.igor_utils.AlterEnv",
                return_value=mock_cls,
            ),
            pytest.raises(ValueError),
        ):
            write_version_file(tmp_path, kind, is_test=True)

    # defang

    with patch("drain_swamp.igor_utils.write_version_files", return_value=None):
        # is_test default --> False
        kind = ("0.0.1",)
        invalids = (
            "Hi there",
            0.1234,
        )
        for invalid in invalids:
            write_version_file(tmp_path, kind, is_test=invalid)

        kind = ("golf balls",)
        with pytest.raises(ValueError):
            write_version_file(tmp_path, kind, is_test=True)


def test_get_tag_version(tmp_path, prep_pyproject_toml, prepare_folders_files):
    """Test get_tag_version."""
    # pytest --showlocals --log-level INFO -k "test_get_tag_version" tests
    path_cwd = tmp_path / "complete_awesome_perfect"
    path_cwd.mkdir()
    path_dir_dest = path_cwd.joinpath("src", "complete_awesome_perfect")
    path_version_file = path_dir_dest.joinpath("_version.py")
    version_file_relpath = Path("src").joinpath(
        "complete_awesome_perfect",
        "_version.py",
    )

    # prepare
    srcs = (path_version_file,)
    prepare_folders_files(srcs, path_cwd)

    sem_ver = "0.0.2"
    write_version_files(sem_ver, path_cwd, version_file_relpath, None)

    #    no pyproject.toml
    with (pytest.raises(AssertionError),):
        get_tag_version(path_cwd)

    p_toml_src = Path(__file__).parent.joinpath(
        "_good_files",
        "complete-manage-pip-prod-unlock.pyproject_toml",
    )
    prep_pyproject_toml(p_toml_src, path_cwd)

    #    success
    actual = get_tag_version(path_cwd)
    assert actual == sem_ver

    #    NotADirectory
    path_f = path_cwd.joinpath("fish.txt")
    path_f.touch()
    with pytest.raises(NotADirectoryError):
        get_tag_version(path_f)

    str_version_file = (
        """__version__ = version = 'golf balls'\n"""
        """__version_tuple__ = version_tuple = (0, 0, 3, 'golf balls', '+golfballs.d20241212')\n\n"""
    )
    path_version_file.write_text(str_version_file)

    sane_fallback = "0.0.1"
    sem_ver = get_tag_version(path_cwd)
    assert sem_ver == sane_fallback
