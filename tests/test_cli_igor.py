"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

Unittest for entrypoint, cli_igor

Without coverage

.. code-block:: shell

   pytest --showlocals --log-level INFO tests/test_cli_igor.py

With coverage

Needs a config file to specify exact files to include / omit from report.
Will fail with exit code 1 even with 100% coverage

.. code-block:: shell

   pytest --showlocals --cov="drain_swamp" --cov-report=term-missing tests/test_cli_igor.py


"""

import copy
import logging
import logging.config
import shlex
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest  # noqa: F401
from click.testing import CliRunner

from drain_swamp.cli_igor import (
    current_version,
    entrypoint_name,
    main,
    seed,
    semantic_version_aware_build,
    snippets_list,
    validate_tag,
)
from drain_swamp.constants import (
    LOGGING,
    g_app_name,
)


def test_cli_main():
    """Minimally test package version is printed"""
    runner = CliRunner()
    # --version
    cmd = ["--version"]
    result = runner.invoke(main, cmd)
    assert result.exit_code == 0
    assert "version" in result.stdout

    # --help
    cmd = ["--help"]
    result = runner.invoke(main, cmd)
    assert result.exit_code == 0
    assert f"Command-line for {entrypoint_name}. Prints usage" in result.stdout


def test_seed(tmp_path, prep_pyproject_toml):
    """To CHANGES.rst, add seed, later to be replaced by a changelog versioned entry"""
    # prepare
    path_change_rst = Path(__file__).parent.joinpath(
        "_changelog_files",
        "CHANGES-empty.rst",
    )

    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path) as tmp_dir_path:
        path_tmp_dir = Path(tmp_dir_path)
        cmd = ["--path", path_tmp_dir]

        # without prepare
        result = runner.invoke(seed, cmd)
        expected = "Provide an absolute path to a file. Got, "
        actual = result.stdout
        assert expected in actual

        # prepare
        path_empty = prep_pyproject_toml(
            path_change_rst, path_tmp_dir, rename="CHANGES.rst"
        )
        existing_text = path_empty.read_text()

        result = runner.invoke(seed, cmd)
        expected_out = "Updating "
        actual_out = result.stdout
        assert expected_out in actual_out

        actual_text = path_empty.read_text()
        assert existing_text != actual_text
        assert "Nothing yet." in actual_text


def test_build(tmp_path):
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
            cmd_folder_invalid.append("--package-name")
            cmd_folder_invalid.append(invalid)
            with (
                patch(
                    f"{g_app_name}.version_semantic._get_app_name", return_value=None
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
            "--package-name",
            g_app_name,
        ]
        result = runner.invoke(semantic_version_aware_build, cmd)
        assert result.exit_code == 5

        # simulate no initial git tag --> kind either current or now
        kinds = (
            "now",
            "current",
        )
        for kind in kinds:
            cmd_folder_no_commits = [
                "--path",
                path_tmp_dir,
                "--kind",
                kind,
                "--package-name",
                g_app_name,
            ]
            with (
                patch(
                    f"{g_app_name}.version_semantic._current_version",
                    return_value=None,
                ),
            ):
                result = runner.invoke(
                    semantic_version_aware_build, cmd_folder_no_commits
                )
                assert result.exit_code == 6
            del cmd_folder_no_commits

        # simulate no initial git tag --> kind == tag
        cmd_folder_no_commits = [
            "--path",
            path_tmp_dir,
            "--kind",
            "tag",
            "--package-name",
            g_app_name,
        ]
        with (
            patch(f"{g_app_name}.version_semantic._tag_version", return_value=None),
            patch(
                f"{g_app_name}.version_semantic._current_version",
                return_value=None,
            ),
        ):
            result = runner.invoke(semantic_version_aware_build, cmd_folder_no_commits)
            assert result.exit_code == 6

        # build fail
        cmd = []
        cmd_folder_no_commits = [
            "--path",
            path_tmp_dir,
            "--kind",
            "0.0.1",
            "--package-name",
            g_app_name,
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
    ("0.1.1.candidate1dev1+g4b33a80.d20240129", "0.1.1rc1.dev1", 1),
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
    # demonstrate exit codes, but not that a ver str is returned on a successful call
    runner = CliRunner()

    cmd = ["--path", path_project_base()]
    with (patch(f"{g_app_name}.cli_igor.get_current_version", return_value=ret),):
        result = runner.invoke(current_version, cmd)

    assert result.exit_code == expected_exit_code


testdata_snippets_list = (
    (
        Path(__file__).parent.joinpath(
            "_good_files", "complete-manage-pip-prod.pyproject_toml"
        ),
        "docs",
        Path(__file__).parent.joinpath(
            "test_snip",
            "test_snip_harden_one_snip__with_id_.txt",
        ),
        0,
        ("little_shop_of_horrors_shrine_candles",),
    ),
    (
        Path(__file__).parent.joinpath(
            "_good_files", "complete-manage-pip-prod.pyproject_toml"
        ),
        "docs",
        Path(__file__).parent.joinpath(
            "test_snip",
            "test_snip_harden_No_snippet__Nothing_to_do_.txt",
        ),
        6,
        (),
    ),
    (
        Path(__file__).parent.joinpath(
            "_good_files", "complete-manage-pip-prod.pyproject_toml"
        ),
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
    "path_file, doc_relpath, path_confpy_src, expected_exit_code, keys_expected",
    testdata_snippets_list,
    ids=ids_snippets_list,
)
def test_snippets_list(
    path_file,
    doc_relpath,
    path_confpy_src,
    expected_exit_code,
    keys_expected,
    tmp_path,
    caplog,
):
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

        # prepare docs/ folder
        path_dir = path_tmp_dir.joinpath(doc_relpath)
        path_dir.mkdir()

        result = runner.invoke(snippets_list, cmd)
        assert result.exit_code == 4
        assert (
            result.output.rstrip()
            == "Expected to find file, doc/conf.py or docs/conf.py"
        )

        # prepare [docs folder]/conf.py
        contents = path_confpy_src.read_text()
        path_confpy = path_dir.joinpath("conf.py")
        path_confpy.write_text(contents)
        assert path_confpy.exists() and path_confpy.is_file()

        result = runner.invoke(snippets_list, cmd)
        assert result.exit_code == expected_exit_code
