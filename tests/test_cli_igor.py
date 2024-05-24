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
import shlex
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest  # noqa: F401
from click.testing import CliRunner

from drain_swamp.cli_igor import (
    entrypoint_name,
    main,
    seed,
    semantic_version_aware_build,
    validate_tag,
)
from drain_swamp.constants import g_app_name


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
