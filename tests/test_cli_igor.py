"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

Unittest for entrypoint, drain-swamp

With coverage

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
import shlex
import subprocess
import traceback
from pathlib import Path
from typing import TYPE_CHECKING
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
from drain_swamp.constants import g_app_name

if TYPE_CHECKING:
    import logging
    from collections.abc import (
        Callable,
        MutableSet,
        Sequence,
    )


def test_cli_main() -> None:
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
    msg_expected_partial = f"Command-line for {entrypoint_name}. Prints usage"
    assert msg_expected_partial in result.stdout


@pytest.mark.parametrize(
    "relpath_change_rst, exit_code_excepted, stderr_msg",
    (
        pytest.param(
            Path("_changelog_files").joinpath("CHANGES-empty.rst"),
            0,
            "Updating ",
            id="normal-skeleton",
        ),
        pytest.param(
            Path("_changelog_files").joinpath("CHANGES-missing-start-token.rst"),
            1,
            "Start token not found. In CHANGES.rst, add token, ",
            id="start-token-missing",
        ),
    ),
)
def test_seed_cli(
    relpath_change_rst: "Path",
    exit_code_excepted: int,
    stderr_msg: str,
    tmp_path: "Path",
    prep_pyproject_toml: "Callable[[Path, Path, Path | str | None], Path]",
    request: pytest.FixtureRequest,
) -> None:
    """To CHANGES.rst, add seed, later replaced by a changelog versioned entry."""
    # pytest --showlocals --log-level INFO -k "test_seed_cli" tests
    abspath_tests_dir = request.path.parent
    abspath_change_rst = abspath_tests_dir.joinpath(relpath_change_rst)

    runner = CliRunner(mix_stderr=False)
    path_tmp_dir = tmp_path

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
        abspath_change_rst, path_tmp_dir, rename="CHANGES.rst"
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


def test_build_cli(
    tmp_path: "Path",
    prep_pyproject_toml: "Callable[[Path, Path, Path | str | None], Path]",
) -> None:
    """Build package -- drain-swamp only. No refresh locking.

    See cmd within build backend instead.
    """
    # pytest --showlocals --log-level INFO -k "test_build_cli" tests
    runner = CliRunner()
    path_tmp_dir = tmp_path

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
            patch(f"{g_app_name}.version_semantic.get_package_name", return_value=None),
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


@pytest.mark.parametrize(
    "ver, expected_msg, expected_exit_code",
    (
        pytest.param(
            "1!v1.0.1+g4b33a80.d20240129",
            "1.0.1",
            0,
            id="with-epoch-locals-and-prepended-v",
        ),
        pytest.param(
            "0.1.dev0.d20240213",
            "0.0.1.dev0",
            0,
            id="malformed-semantic-ver-str-raise-ValueError",
        ),
        pytest.param(
            "0.0.1.final0.post4.dev0",
            "0.0.1.post4.dev0",
            1,
            id="final-is-not-valid-semantic-str",
        ),
    ),
)
def test_validate_tag(ver: str, expected_msg: str, expected_exit_code: int) -> None:
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


@pytest.mark.parametrize(
    "ret, expected_exit_code",
    (
        pytest.param(
            None,
            1,
            id="call-failure",
        ),
        pytest.param(
            "abcdefg",
            0,
            id="call-succeeds-gets-the-current-version-str",
        ),
    ),
)
def test_current_version(
    ret: str | None,
    expected_exit_code: int,
    path_project_base: "Callable[[], Path]",
) -> None:
    """Test current_version."""
    # demonstrate exit codes, but not that a ver str is returned on a successful call
    runner = CliRunner()

    cmd = ["--path", path_project_base()]
    with (patch(f"{g_app_name}.cli_igor.get_current_version", return_value=ret),):
        result = runner.invoke(current_version, cmd)

    assert result.exit_code == expected_exit_code


@pytest.mark.logging_package_name(g_app_name)
@pytest.mark.parametrize(
    "doc_relpath, relpath_confpy_src, expected_exit_code, keys_expected",
    (
        pytest.param(
            "docs",
            Path("_good_snips").joinpath("test_snip_harden_one_snip__with_id_.txt"),
            0,
            ("little_shop_of_horrors_shrine_candles",),
            id="Has-a-snippet",
        ),
        pytest.param(
            "docs",
            Path("_good_snips").joinpath(
                "test_snip_harden_No_snippet__Nothing_to_do_.txt",
            ),
            6,
            (),
            id="No-snippets",
        ),
        pytest.param(
            "docs",
            Path("_bad_snips").joinpath("nested-snips.txt"),
            5,
            (),
            id="Nested-snips--ReplaceResult.VALIDATE_FAIL",
        ),
    ),
)
def test_snippets_list(
    doc_relpath: str,
    relpath_confpy_src: "Path",
    expected_exit_code: int,
    keys_expected: tuple[str, ...],
    tmp_path: "Path",
    request: pytest.FixtureRequest,
    logging_strict: "Callable[[], tuple[logging.Logger, Sequence[logging.Logger]]]",
) -> None:
    """lists snippets in doc?/conf.py --> :code:`drain-swamp list`."""
    # pytest --showlocals --log-level INFO -k "test_snippets_list" tests
    abspath_tests_dir = request.path.parent
    abspath_confpy_src = abspath_tests_dir.joinpath(relpath_confpy_src)

    t_two = logging_strict()
    logger, loggers = t_two

    runner = CliRunner()
    path_tmp_dir = tmp_path

    # a folder --> ReplaceResult.VALIDATE_FAIL
    cmd = [
        "--path",
        path_tmp_dir,
    ]
    result = runner.invoke(snippets_list, cmd)
    assert result.exit_code == 3
    msg_expected_0 = "Expected a doc/ or docs/ folder"
    msg_actual_0 = result.output.rstrip()
    assert msg_actual_0 == msg_expected_0

    # prepare
    #    docs/ folder
    path_dir = path_tmp_dir.joinpath(doc_relpath)
    path_dir.mkdir()

    result = runner.invoke(snippets_list, cmd)
    assert result.exit_code == 4
    msg_expected_1 = "Expected to find file, doc/conf.py or docs/conf.py"
    msg_actual_1 = result.output.rstrip()
    assert msg_actual_1 == msg_expected_1

    # prepare
    #    [docs folder]/conf.py
    contents = abspath_confpy_src.read_text()
    path_confpy = path_dir.joinpath("conf.py")
    path_confpy.write_text(contents)
    assert path_confpy.exists() and path_confpy.is_file()

    result = runner.invoke(snippets_list, cmd)
    assert result.exit_code == expected_exit_code


@pytest.mark.parametrize(
    "is_tmp, kind, exit_code_expected",
    (
        pytest.param(
            True,
            "current",
            3,
            id="Expecting-a-folder",
        ),
        pytest.param(
            False,
            "dog food tastes better than this",
            4,
            id="--kind-nonsense.-Explicit-version-str-invalid",
        ),
        pytest.param(
            False,
            "current",
            0,
            id="package_name-ignored",
        ),
    ),
)
def test_cheats_exceptions(
    is_tmp: bool,
    kind: str,
    exit_code_expected: int,
    path_project_base: "Callable[[], Path]",
    tmp_path: "Path",
) -> None:
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
    result = CliRunner().invoke(do_cheats, cmd)

    # out = result.output

    tb = result.exc_info[2]
    traceback.print_tb(tb)
    # str_tb = traceback.format_tb(tb)
    # result_exc = result.exception
    pass

    exit_code_actual = result.exit_code
    assert exit_code_actual == exit_code_expected


def test_cheats_unusual(
    tmp_path: "Path",
    path_project_base: "Callable[[], Path]",
) -> None:
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


@pytest.mark.logging_package_name(g_app_name)
@pytest.mark.parametrize(
    "relpath_toml_src, kind, expected",
    (
        pytest.param(
            Path("_good_files").joinpath(
                "complete-manage-pip-prod-unlock.pyproject_toml",
            ),
            "tag",
            "0.0.3",
            id="version-from-version-file",
        ),
        pytest.param(
            Path("_good_files").joinpath(
                "complete-manage-pip-prod-unlock.pyproject_toml",
            ),
            "0.0.2",
            "0.0.2",
            id="explicit-valid-semantic-version-str",
        ),
    ),
)
def test_write_version_normal(
    relpath_toml_src: "Path",
    kind: str,
    expected: str,
    tmp_path: "Path",
    prep_pyproject_toml: "Callable[[Path, Path, Path | None], Path | None]",
    prepare_folders_files: "Callable[[Sequence[str | Path] | MutableSet[str | Path]], set[Path]]",
    logging_strict: "Callable[[], tuple[logging.Logger, Sequence[logging.Logger]]]",
    # has_logging_occurred,
    request: pytest.FixtureRequest,
) -> None:
    """Write version file typical situation."""
    # pytest --showlocals --log-level INFO -k "test_write_version_normal" tests
    abspath_tests_dir = request.path.parent
    abspath_toml_src = abspath_tests_dir.joinpath(relpath_toml_src)

    t_two = logging_strict()
    logger, loggers = t_two

    runner = CliRunner(mix_stderr=False)
    path_tmp_dir = tmp_path
    path_cwd = path_tmp_dir.joinpath("complete_awesome_perfect")
    path_cwd.mkdir()
    version_file_relpath = "src/complete_awesome_perfect/_version.py"
    path_version_file = path_cwd.joinpath(version_file_relpath)
    # prepare
    #    pyproject.toml
    prep_pyproject_toml(abspath_toml_src, path_cwd)
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
    # assert has_logging_occurred(caplog)

    assert result_ver.exit_code == 0
    # str_ver_stderr = result_ver.stderr.strip()
    str_ver_stdout = result_ver.stdout.strip()
    assert str_ver_stdout == expected


@pytest.mark.parametrize(
    "relpath_config_src, kind, exit_code_expected",
    (
        pytest.param(
            Path("_good_files").joinpath(
                "complete-manage-pip-prod-unlock.pyproject_toml",
            ),
            "golf balls",
            5,
            id="kind-invalid--ValueError--5",
        ),
        pytest.param(
            Path("_good_files").joinpath("no_project_name.pyproject_toml"),
            "0.0.4",
            4,
            id="pyproject.toml-no-project.name-missing--AssertionError--4",
        ),
    ),
)
def test_write_version_exceptions(
    relpath_config_src: "Path",
    kind: str,
    exit_code_expected: int,
    tmp_path: "Path",
    caplog: pytest.LogCaptureFixture,
    request: pytest.FixtureRequest,
    prep_pyproject_toml: "Callable[[Path, Path, Path | None], Path | None]",
    prepare_folders_files: "Callable[[Sequence[str | Path] | MutableSet[str | Path]], set[Path]]",
    has_logging_occurred: "Callable[[], bool]",
) -> None:
    """Write version file exceptions."""
    # pytest --showlocals --log-level INFO -k "test_write_version_exceptions" tests
    abspath_tests_dir = request.path.parent
    abspath_config_src = abspath_tests_dir.joinpath(relpath_config_src)

    runner = CliRunner(mix_stderr=False)
    path_tmp_dir = tmp_path

    path_cwd = path_tmp_dir.joinpath("complete_awesome_perfect")
    path_cwd.mkdir()
    version_file_relpath = "src/complete_awesome_perfect/_version.py"
    path_version_file = path_cwd.joinpath(version_file_relpath)

    # prepare
    #    pyproject.toml
    prep_pyproject_toml(abspath_config_src, path_cwd)
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


@pytest.mark.logging_package_name(g_app_name)
def test_tag_version(
    tmp_path: "Path",
    prep_pyproject_toml: "Callable[[Path, Path, Path | None], Path | None]",
    prepare_folders_files: "Callable[[Sequence[str | Path] | MutableSet[str | Path]], set[Path]]",
    logging_strict: "Callable[[], tuple[logging.Logger, Sequence[logging.Logger]]]",
    # has_logging_occurred,
) -> None:
    """Get semantic version from version file."""
    # pytest --showlocals --log-level INFO -k "test_tag_version" tests
    t_two = logging_strict()
    logger, loggers = t_two

    runner = CliRunner(mix_stderr=False)
    path_tmp_dir = tmp_path

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
            f"{g_app_name}.version_semantic._tag_version",
            return_value=None,
        ),
        patch(
            f"{g_app_name}.version_semantic._current_version",
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
