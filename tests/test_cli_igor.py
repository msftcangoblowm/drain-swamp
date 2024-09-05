"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

Unittest for entrypoint, drain-swamp

Unit test -- Module

.. code-block:: shell

   python -m coverage run --source='drain_swamp.cli_igor' -m pytest \
   --showlocals tests/test_cli_igor.py && coverage report \
   --data-file=.coverage --include="**/cli_igor.py"

Integration test

.. code-block:: shell

   make coverage
   pytest --showlocals --cov="drain_swamp" --cov-report=term-missing \
   --cov-config=pyproject.toml tests

"""

import copy
import logging
import logging.config
import shlex
import subprocess
import traceback
from pathlib import Path
from unittest.mock import patch

import pytest  # noqa: F401
from click.testing import CliRunner

from drain_swamp.cli_igor import (
    current_version,
    do_cheats,
    entrypoint_name,
    main,
    seed,
    semantic_version_aware_build,
    setuptools_scm_key_value_pair,
    snippets_list,
    tag_version,
    validate_tag,
)
from drain_swamp.constants import (
    LOGGING,
    g_app_name,
)


def test_cli_main():
    """Minimally test package version is printed."""
    runner = CliRunner()
    # --version
    """
    cmd = ["--version"]
    result = runner.invoke(main, cmd)
    assert result.exit_code == 0
    assert "version" in result.stdout
    """

    # --help
    cmd = ["--help"]
    result = runner.invoke(main, cmd)
    assert result.exit_code == 0
    assert f"Command-line for {entrypoint_name}. Prints usage" in result.stdout


testdata_seed = (
    (
        Path(__file__).parent.joinpath(
            "_changelog_files",
            "CHANGES-empty.rst",
        ),
        0,
        "Updating ",
    ),
    (
        Path(__file__).parent.joinpath(
            "_changelog_files",
            "CHANGES-missing-start-token.rst",
        ),
        1,
        "Start token not found. In CHANGES.rst, add token, ",
    ),
)
ids_seed = (
    "normal skeleton",
    "start token missing",
)


@pytest.mark.parametrize(
    "path_change_rst, exit_code_excepted, stderr_msg",
    testdata_seed,
    ids=ids_seed,
)
def test_seed_cli(
    path_change_rst,
    exit_code_excepted,
    stderr_msg,
    tmp_path,
    prep_pyproject_toml,
):
    """To CHANGES.rst, add seed, later replaced by a changelog versioned entry."""
    # pytest --showlocals --log-level INFO -k "test_seed_cli" tests
    runner = CliRunner(mix_stderr=False)
    with runner.isolated_filesystem(temp_dir=tmp_path) as tmp_dir_path:
        path_tmp_dir = Path(tmp_dir_path)
        start_token = "Nothing yet."
        cmd = ["--path", path_tmp_dir]

        # without prepare. No CHANGES.rst file
        expected = "Provide an absolute path to a file. Got, "
        result = runner.invoke(seed, cmd)
        exit_code_actual = result.exit_code
        actual = result.stderr

        assert exit_code_actual == 2
        assert expected in actual

        # prepare
        path_changelog = prep_pyproject_toml(
            path_change_rst, path_tmp_dir, rename="CHANGES.rst"
        )
        contents_before = path_changelog.read_text()

        # act
        result = runner.invoke(seed, cmd)
        exit_code_actual = result.exit_code
        actual_out = result.stderr

        # verify
        #    exit code
        assert exit_code_actual == exit_code_excepted

        #    received expected error msg
        assert stderr_msg in actual_out

        #    check if changes occurred
        contents_after = path_changelog.read_text()
        if exit_code_actual == 0:
            assert contents_before != contents_after
            assert start_token in contents_after
        else:
            assert contents_before == contents_after
            assert start_token not in contents_after


def test_build_cli(prep_pyproject_toml, tmp_path):
    """Build package -- drain-swamp only. No refresh locking.

    See cmd within build backend instead.
    """
    # pytest --showlocals --log-level INFO -k "test_build_cli" tests
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path) as tmp_dir_path:
        path_tmp_dir = Path(tmp_dir_path)

        # Passing folder is caught by click rather than NotADirectoryError
        path_passwd = path_tmp_dir.joinpath("password-secret.txt")
        path_passwd.touch()
        kind = "five element spirit or nature"
        cmd = [
            "--path",
            str(path_passwd),
            "--kind",
            shlex.split(kind),
        ]
        result = runner.invoke(semantic_version_aware_build, cmd)
        assert result.exit_code == 2
        del cmd

        # AssertionError
        # shlex.split("   ") --> [] which is interpreted as "[]" --> exit code 6, not 4
        # 1.2345 --> "1.2345" --> exit code 6, not 4
        cmd = [
            "--path",
            str(path_tmp_dir),
            "--kind",
            "tag",
        ]
        invalids = (
            "",
            # shlex.split("   "),
            # 1.2345,
        )
        for invalid in invalids:
            cmd_folder_invalid = copy.deepcopy(cmd)
            with (
                patch(
                    f"{g_app_name}.version_semantic.get_package_name", return_value=None
                ),
            ):
                result = runner.invoke(semantic_version_aware_build, cmd_folder_invalid)
                print(
                    f"test_cli_igor.py test_build AssertionError result.stdout {result.stdout}"
                )
                assert result.exit_code == 4
            del cmd_folder_invalid

        # ValueError
        kind = "five element spirit or nature?"
        cmd = [
            "--path",
            path_tmp_dir,
            "--kind",
            kind,
        ]
        result = runner.invoke(semantic_version_aware_build, cmd)
        assert result.exit_code == 5

        # Requires preparation of a pyproject.toml
        cmd = []
        cmd_folder_no_commits = [
            "--path",
            path_tmp_dir,
            "--kind",
            "0.0.1",
        ]
        with (
            patch(
                "subprocess.run",
                side_effect=subprocess.CalledProcessError(128, cmd),
            ),
        ):
            result = runner.invoke(semantic_version_aware_build, cmd_folder_no_commits)
            assert result.exit_code == 4
            assert len(result.output) != 0

        # prepare
        p_toml_file = Path(__file__).parent.joinpath(
            "_good_files", "complete-manage-pip-prod-unlock.pyproject_toml"
        )
        prep_pyproject_toml(p_toml_file, path_tmp_dir)

        # build fail
        cmd = []
        cmd_folder_no_commits = [
            "--path",
            path_tmp_dir,
            "--kind",
            "0.0.1",
        ]
        with (
            patch(
                "subprocess.run",
                side_effect=subprocess.CalledProcessError(128, cmd),
            ),
        ):
            result = runner.invoke(semantic_version_aware_build, cmd_folder_no_commits)
            assert result.exit_code == 1
            assert len(result.output) != 0

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
            result = runner.invoke(semantic_version_aware_build, cmd_folder_no_commits)
            assert result.exit_code == 0


testdata_validate_tag = (
    ("1!v1.0.1+g4b33a80.d20240129", "1.0.1", 0),
    ("0.1.dev0.d20240213", "0.1.dev0.d20240213", 1),
)
ids_validate_tag = (
    "with epoch locals and prepended v",
    "malformed semantic ver str raise ValueError",
)


@pytest.mark.parametrize(
    "ver, expected_msg, expected_exit_code",
    testdata_validate_tag,
    ids=ids_validate_tag,
)
def test_validate_tag(ver, expected_msg, expected_exit_code):
    """Check validate a str. Is it a valid semantic version str?"""
    # pytest --showlocals --log-level INFO -k "test_validate_tag" tests
    runner = CliRunner()
    cmd = [ver]
    result = runner.invoke(validate_tag, cmd)
    if expected_exit_code == 0:
        actual = result.output
        assert actual.rstrip() == expected_msg
        assert result.exit_code == 0
    else:
        assert result.exit_code == 1
        # why semantic version str is malformed
        assert len(result.output) != 0


testdata_current_version = (
    (
        None,
        1,
    ),
    (
        "abcdefg",
        0,
    ),
)
ids_current_version = (
    "call failure",
    "call succeeds gets the current version str",
)


@pytest.mark.parametrize(
    "ret, expected_exit_code",
    testdata_current_version,
    ids=ids_current_version,
)
def test_current_version(ret, expected_exit_code, path_project_base):
    """Test current_version."""
    # demonstrate exit codes, but not that a ver str is returned on a successful call
    runner = CliRunner()

    cmd = ["--path", path_project_base()]
    with (patch(f"{g_app_name}.cli_igor.get_current_version", return_value=ret),):
        result = runner.invoke(current_version, cmd)

    assert result.exit_code == expected_exit_code


testdata_snippets_list = (
    (
        "docs",
        Path(__file__).parent.joinpath(
            "test_snip",
            "test_snip_harden_one_snip__with_id_.txt",
        ),
        0,
        ("little_shop_of_horrors_shrine_candles",),
    ),
    (
        "docs",
        Path(__file__).parent.joinpath(
            "test_snip",
            "test_snip_harden_No_snippet__Nothing_to_do_.txt",
        ),
        6,
        (),
    ),
    (
        "docs",
        Path(__file__).parent.joinpath(
            "_bad_snips",
            "nested-snips.txt",
        ),
        5,
        (),
    ),
)
ids_snippets_list = (
    "Has a snippet",
    "No snippets",
    "Nested snips --> ReplaceResult.VALIDATE_FAIL",
)


@pytest.mark.parametrize(
    "doc_relpath, path_confpy_src, expected_exit_code, keys_expected",
    testdata_snippets_list,
    ids=ids_snippets_list,
)
def test_snippets_list(
    doc_relpath,
    path_confpy_src,
    expected_exit_code,
    keys_expected,
    tmp_path,
    caplog,
):
    """lists snippets in doc?/conf.py --> :code:`drain-swamp list`."""
    # pytest --showlocals --log-level INFO -k "test_snippets_list" tests
    LOGGING["loggers"][g_app_name]["propagate"] = True
    logging.config.dictConfig(LOGGING)
    logger = logging.getLogger(name=g_app_name)
    logger.addHandler(hdlr=caplog.handler)
    caplog.handler.level = logger.level

    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path) as tmp_dir_path:
        path_tmp_dir = Path(tmp_dir_path)

        # a folder --> ReplaceResult.VALIDATE_FAIL
        cmd = [
            "--path",
            path_tmp_dir,
        ]
        result = runner.invoke(snippets_list, cmd)
        assert result.exit_code == 3
        assert result.output.rstrip() == "Expected a doc/ or docs/ folder"

        # prepare
        #    docs/ folder
        path_dir = path_tmp_dir.joinpath(doc_relpath)
        path_dir.mkdir()

        result = runner.invoke(snippets_list, cmd)
        assert result.exit_code == 4
        assert (
            result.output.rstrip()
            == "Expected to find file, doc/conf.py or docs/conf.py"
        )

        # prepare
        #    [docs folder]/conf.py
        contents = path_confpy_src.read_text()
        path_confpy = path_dir.joinpath("conf.py")
        path_confpy.write_text(contents)
        assert path_confpy.exists() and path_confpy.is_file()

        result = runner.invoke(snippets_list, cmd)
        assert result.exit_code == expected_exit_code


testdata_cheats_exceptions = (
    (
        True,
        "current",
        3,
    ),
    (
        False,
        "dog food tastes better than this",
        4,
    ),
    (
        False,
        "current",
        0,
    ),
)
ids_cheats_exceptions = (
    "Expecting a folder",
    "--kind nonsense. Explicit version str invalid",
    "package_name ignored",
)


@pytest.mark.parametrize(
    "is_tmp, kind, exit_code_expected",
    testdata_cheats_exceptions,
    ids=ids_cheats_exceptions,
)
def test_cheats_exceptions(
    is_tmp, kind, exit_code_expected, path_project_base, tmp_path
):
    """Print cheats. Exceptions."""
    # pytest --showlocals --log-level INFO -k "test_cheats_exceptions" tests

    # prepare
    if is_tmp:
        path_f = tmp_path.joinpath("fish.txt")
        path_f.touch()
    else:
        path_cwd = path_project_base()
        path_f = path_cwd

    # act
    cmd = [
        "--path",
        path_f,
        "--kind",
        kind,
    ]
    runner = CliRunner()
    result = runner.invoke(do_cheats, cmd)

    # out = result.output

    tb = result.exc_info[2]
    traceback.print_tb(tb)
    # str_tb = traceback.format_tb(tb)
    # result_exc = result.exception
    pass

    exit_code_actual = result.exit_code
    assert exit_code_actual == exit_code_expected


def test_cheats_unusual(path_project_base, tmp_path):
    """Test cheats unusual issues."""
    # pytest --showlocals --log-level INFO -k "test_cheats_unusual" tests
    path_cwd = path_project_base()
    runner = CliRunner()

    # current
    cmd = [
        "--path",
        str(path_cwd),
        "--kind",
        "current",
    ]
    result = runner.invoke(do_cheats, cmd)
    str_cheats = result.output

    tb = result.exc_info[2]
    traceback.print_tb(tb)
    # str_tb = traceback.format_tb(tb)
    assert result.exit_code == 0
    assert str_cheats is not None and isinstance(str_cheats, str)
    assert len(str_cheats) != 0

    # tag
    exit_code_expected = 0
    kind = "tag"
    cmd = ["--path", str(path_cwd), "--kind", kind]
    result = runner.invoke(do_cheats, cmd)
    exit_code_actual = result.exit_code
    assert exit_code_actual == exit_code_expected

    # no pyproject.toml --> AssertionError(6)
    with runner.isolated_filesystem(temp_dir=tmp_path) as tmp_dir_path:
        kind = "tag"
        cmd = ["--path", tmp_dir_path, "--kind", kind]
        result = runner.invoke(do_cheats, cmd)
        exit_code_actual = result.exit_code
        assert exit_code_actual == 6


testdata_write_version_normal = (
    (
        Path(__file__).parent.joinpath(
            "_good_files", "complete-manage-pip-prod-unlock.pyproject_toml"
        ),
        "tag",
        "0.0.3",
    ),
    (
        Path(__file__).parent.joinpath(
            "_good_files", "complete-manage-pip-prod-unlock.pyproject_toml"
        ),
        "0.0.2",
        "0.0.2",
    ),
)
ids_write_version_normal = (
    "version from version file",
    "explicit valid semantic version str",
)


@pytest.mark.parametrize(
    "path_toml_src, kind, expected",
    testdata_write_version_normal,
    ids=ids_write_version_normal,
)
def test_write_version_normal(
    path_toml_src,
    kind,
    expected,
    tmp_path,
    prep_pyproject_toml,
    prepare_folders_files,
    caplog,
    has_logging_occurred,
):
    """Write version file typical situation."""
    # pytest --showlocals --log-level INFO -k "test_write_version_normal" tests
    LOGGING["loggers"][g_app_name]["propagate"] = True
    logging.config.dictConfig(LOGGING)
    logger = logging.getLogger(name=g_app_name)
    logger.addHandler(hdlr=caplog.handler)
    caplog.handler.level = logger.level

    runner = CliRunner(mix_stderr=False)
    with runner.isolated_filesystem(temp_dir=tmp_path) as tmp_dir_path:
        path_tmp_dir = Path(tmp_dir_path)
        path_cwd = path_tmp_dir.joinpath("complete_awesome_perfect")
        path_cwd.mkdir()
        version_file_relpath = "src/complete_awesome_perfect/_version.py"
        path_version_file = path_cwd.joinpath(version_file_relpath)
        # prepare
        #    pyproject.toml
        prep_pyproject_toml(path_toml_src, path_cwd)
        #    folders and empty _version.py
        srcs = (version_file_relpath,)
        prepare_folders_files(srcs, path_cwd)

        #    version file -- Avoid fallback sane sem version "0.0.1"
        str_version_file = (
            """__version__ = version = '0.0.3'\n"""
            """__version_tuple__ = version_tuple = (0, 0, 3)\n\n"""
        )
        path_version_file.write_text(str_version_file)

        args = [
            "--path",
            str(path_cwd),
        ]

        args2 = copy.deepcopy(args)
        args2.extend(["--kind", kind])
        result = runner.invoke(setuptools_scm_key_value_pair, args2)
        logger.info(f"result.stderr: {result.stderr}")
        exit_code_actual = result.exit_code
        assert exit_code_actual == 0
        actual_contents = path_version_file.read_text()
        assert expected in actual_contents

        # confirm -- get tag version, not current version
        args_get = ("--path", str(path_cwd))
        result_ver = runner.invoke(tag_version, args_get)
        logger.info(f"exc: {result_ver.exception}")
        logger.info(f"err: {result_ver.stderr}")
        logger.info(f"out: {result_ver.stdout}")
        assert has_logging_occurred(caplog)

        assert result_ver.exit_code == 0
        # str_ver_stderr = result_ver.stderr.strip()
        str_ver_stdout = result_ver.stdout.strip()
        assert str_ver_stdout == expected


testdata_write_version_exceptions = (
    (
        Path(__file__).parent.joinpath(
            "_good_files",
            "complete-manage-pip-prod-unlock.pyproject_toml",
        ),
        "golf balls",
        5,
    ),
    (
        Path(__file__).parent.joinpath(
            "_good_files",
            "no_project_name.pyproject_toml",
        ),
        "0.0.4",
        4,
    ),
)
ids_write_version_exceptions = (
    "kind invalid --> ValueError --> 5",
    "pyproject.toml no project.name missing --> AssertionError --> 4",
)


@pytest.mark.parametrize(
    "path_config_src, kind, exit_code_expected",
    testdata_write_version_exceptions,
    ids=ids_write_version_exceptions,
)
def test_write_version_exceptions(
    path_config_src,
    kind,
    exit_code_expected,
    tmp_path,
    prep_pyproject_toml,
    prepare_folders_files,
    caplog,
    has_logging_occurred,
):
    """Write version file exceptions."""
    # pytest --showlocals --log-level INFO -k "test_write_version_exceptions" tests
    runner = CliRunner(mix_stderr=False)
    with runner.isolated_filesystem(temp_dir=tmp_path) as tmp_dir_path:
        path_tmp_dir = Path(tmp_dir_path)
        path_cwd = path_tmp_dir.joinpath("complete_awesome_perfect")
        path_cwd.mkdir()
        version_file_relpath = "src/complete_awesome_perfect/_version.py"
        path_version_file = path_cwd.joinpath(version_file_relpath)

        # prepare
        #    pyproject.toml
        prep_pyproject_toml(path_config_src, path_cwd)
        #    folders and empty _version.py
        srcs = (version_file_relpath,)
        prepare_folders_files(srcs, path_cwd)

        #    version file -- Avoid fallback sane sem version "0.0.1"
        str_version_file = (
            """__version__ = version = '0.0.3'\n"""
            """__version_tuple__ = version_tuple = (0, 0, 3)\n\n"""
        )
        path_version_file.write_text(str_version_file)

        args = [
            "--path",
            str(path_cwd),
            "--kind",
            kind,
        ]
        result_ver = runner.invoke(setuptools_scm_key_value_pair, args)
        exit_code_actual = result_ver.exit_code
        assert exit_code_actual == exit_code_expected


def test_tag_version(
    tmp_path,
    prep_pyproject_toml,
    prepare_folders_files,
    caplog,
    has_logging_occurred,
):
    """Get semantic version from version file."""
    # pytest --showlocals --log-level INFO -k "test_tag_version" tests
    LOGGING["loggers"][g_app_name]["propagate"] = True
    logging.config.dictConfig(LOGGING)
    logger = logging.getLogger(name=g_app_name)
    logger.addHandler(hdlr=caplog.handler)
    caplog.handler.level = logger.level

    runner = CliRunner(mix_stderr=False)
    with runner.isolated_filesystem(temp_dir=tmp_path) as tmp_dir_path:
        path_tmp_dir = Path(tmp_dir_path)
        path_cwd = path_tmp_dir.joinpath("complete_awesome_perfect")
        path_cwd.mkdir()
        version_file_relpath = "src/complete_awesome_perfect/_version.py"
        path_version_file = path_cwd.joinpath(version_file_relpath)
        path_fish = path_cwd / "fish.txt"

        # prepare

        #    folder and empty version file
        srcs = (version_file_relpath,)
        prepare_folders_files(srcs, path_cwd)

        #    version file
        str_version_file = (
            """__version__ = version = '0.0.3'\n"""
            """__version_tuple__ = version_tuple = (0, 0, 3)\n\n"""
        )
        path_version_file.write_text(str_version_file)

        # AssertionError(6)
        args = ("--path", str(path_fish))
        result_ver = runner.invoke(tag_version, args)
        exit_code_actual = result_ver.exit_code
        assert exit_code_actual == 6

        #    pyproject.toml
        path_pyproject_toml_src = Path(__file__).parent.joinpath(
            "_good_files",
            "complete-manage-pip-prod-unlock.pyproject_toml",
        )
        prep_pyproject_toml(path_pyproject_toml_src, path_cwd)

        result_ver = runner.invoke(tag_version, args)
        exit_code_actual = result_ver.exit_code
        assert exit_code_actual == 0

        with (
            patch(
                "drain_swamp.version_semantic._tag_version",
                return_value=None,
            ),
            patch(
                "drain_swamp.version_semantic._current_version",
                return_value="golf balls",
            ),
        ):
            result_ver = runner.invoke(tag_version, args)
            exit_code_actual = result_ver.exit_code
            assert exit_code_actual == 4

        """
        out = result_ver.stdout
        err = result_ver.stderr
        exc = result_ver.exception
        logger.info(f"out: {out}")
        logger.info(f"err: {err}")
        logger.info(f"exception: {exc}")
        tb = result_ver.exc_info[2]
        traceback.print_tb(tb)
        assert has_logging_occurred(caplog)
        """
        pass
