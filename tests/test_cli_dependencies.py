"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

..

Unittest for entrypoint, cli_dependencies

.. code-block:: shell

   python -m coverage run --source='drain_swamp.cli_dependencies' -m pytest \
   --showlocals tests/test_cli_dependencies.py && coverage report \
   --data-file=.coverage --include="**/cli_dependencies.py"

"""

import logging
import logging.config
import shutil
import sys
import traceback
from pathlib import Path
from typing import cast
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from drain_swamp._safe_path import resolve_joinpath
from drain_swamp.cli_dependencies import (
    dependencies_lock,
    dependencies_unlock,
    entrypoint_name,
    main,
    requirements_fix,
)
from drain_swamp.constants import (
    LOGGING,
    SUFFIX_IN,
    g_app_name,
)
from drain_swamp.lock_util import replace_suffixes_last

from .testdata_lock_inspect import (
    ids_resolve_resolvable_conflicts,
    testdata_resolve_resolvable_conflicts,
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


test_data_venvmap_loader_exceptions = (
    (
        dependencies_lock,
        Path(__file__).parent.joinpath(
            "_bad_files", "section_misspelled.pyproject_toml"
        ),
        ".doc/.venv",
        (
            "requirements/pins.shared.in",
            "requirements/prod.shared.in",
            "docs/pip-tools.in",
            "docs/requirements.in",
        ),
        4,
    ),
    (
        dependencies_unlock,
        Path(__file__).parent.joinpath(
            "_bad_files", "section_misspelled.pyproject_toml"
        ),
        ".doc/.venv",
        (
            "requirements/pins.shared.in",
            "requirements/prod.shared.in",
            "docs/pip-tools.in",
            "docs/requirements.in",
        ),
        4,
    ),
    (
        requirements_fix,
        Path(__file__).parent.joinpath(
            "_bad_files", "section_misspelled.pyproject_toml"
        ),
        ".doc/.venv",
        (
            "requirements/pins.shared.in",
            "requirements/prod.shared.in",
            "docs/pip-tools.in",
            "docs/requirements.in",
        ),
        4,
    ),
)
ids_venvmap_loader_exceptions = (
    "lock no tool.venv section",
    "unlock no tool.venv section",
    "fix no tool.venv section",
)


@pytest.mark.parametrize(
    "fcn, path_pyproject_toml, venv_path, seq_in, expected_exit_code",
    test_data_venvmap_loader_exceptions,
    ids=ids_venvmap_loader_exceptions,
)
def test_venvmap_loader_exceptions(
    fcn,
    path_pyproject_toml,
    venv_path,
    seq_in,
    expected_exit_code,
    caplog,
    tmp_path,
    prep_pyproject_toml,
):
    """Test VenvMapLoader exceptions 3 and 4."""
    # pytest -vv --showlocals --log-level INFO -k "test_venvmap_loader_exceptions" -v tests
    LOGGING["loggers"][g_app_name]["propagate"] = True
    logging.config.dictConfig(LOGGING)
    logger = logging.getLogger(name=g_app_name)
    logger.addHandler(hdlr=caplog.handler)
    caplog.handler.level = logger.level

    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path) as tmp_dir_path:
        path_tmp_dir = Path(tmp_dir_path)

        cmd = (
            "--path",
            path_tmp_dir,
            "--venv-relpath",
            venv_path,
        )

        # Couldn't find the pyproject.toml file (3)
        result = runner.invoke(fcn, cmd)
        actual_exit_code = 3

        # prepare
        #    pyproject.toml
        prep_pyproject_toml(path_pyproject_toml, path_tmp_dir)

        # In pyproject.toml, expecting sections [[tool.venvs]]. Create them (4)
        result = runner.invoke(fcn, cmd)
        actual_exit_code = result.exit_code
        assert actual_exit_code == expected_exit_code


testdata_lock_unlock_docs_venv = (
    (
        dependencies_unlock,
        Path(__file__).parent.joinpath("_good_files", "complete.pyproject_toml"),
        ".doc/.venv",
        (
            "requirements/pins.shared.in",
            "requirements/prod.shared.in",
            "docs/pip-tools.in",
            "docs/requirements.in",
        ),
        0,
    ),
    (
        dependencies_lock,
        Path(__file__).parent.joinpath("_req_files", "venvs_minimal.pyproject_toml"),
        ".tools",
        (
            "requirements/pins.shared.in",
            "requirements/pip.in",
            "requirements/pip-tools.in",
            "docs/pip-tools.in",
        ),
        0,
    ),
    pytest.param(
        dependencies_lock,
        Path(__file__).parent.joinpath("_good_files", "complete.pyproject_toml"),
        ".doc/.venv",
        (
            "requirements/prod.shared.in",
            "requirements/pins.shared.in",
            "docs/pip-tools.in",
            "docs/requirements.in",
        ),
        0,
        marks=pytest.mark.skipif(sys.version_info < (3, 10), reason="Sphinx>=8 py310+"),
    ),
    pytest.param(
        dependencies_lock,
        Path(__file__).parent.joinpath("_good_files", "complete.pyproject_toml"),
        ".doc/.venv",
        (
            "requirements/prod.shared.in",
            "requirements/pins.shared.in",
            "docs/pip-tools.in",
            "docs/requirements.in",
        ),
        1,
        marks=pytest.mark.skipif(sys.version_info > (3, 9), reason="Sphinx>=8 py310+"),
    ),
)
ids_lock_unlock_docs_venv = (
    "unlock for drain-swamp and docs",
    "lock for docs/pip-tools",
    "lock for drain-swamp and docs",
    "lock for drain-swamp and docs. Sphinx>=8 py310+",
)


@pytest.mark.parametrize(
    "fcn, path_pyproject_toml, venv_path, seq_in, expected_exit_code",
    testdata_lock_unlock_docs_venv,
    ids=ids_lock_unlock_docs_venv,
)
def test_lock_unlock_docs_venv(
    fcn,
    path_pyproject_toml,
    venv_path,
    tmp_path,
    seq_in,
    expected_exit_code,
    caplog,
    prep_pyproject_toml,
    prepare_folders_files,
    path_project_base,
):
    """Test dependency lock and unlock."""
    # pytest -vv --showlocals --log-level INFO -k "test_lock_unlock_docs_venv" -v tests
    # pytest --showlocals tests/test_cli_dependencies.py::test_lock_unlock_docs_venv[lock\ for\ drain-swamp\ and\ docs]
    # python [path to project base]src/drain_swamp/cli_dependencies.py unlock --path=[tmp path folder] --venv-relpath='.doc/.venv'
    # python [path to project base]src/drain_swamp/cli_dependencies.py unlock --path=[tmp path folder]
    LOGGING["loggers"][g_app_name]["propagate"] = True
    logging.config.dictConfig(LOGGING)
    logger = logging.getLogger(name=g_app_name)
    logger.addHandler(hdlr=caplog.handler)
    caplog.handler.level = logger.level

    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path) as tmp_dir_path:
        path_tmp_dir = Path(tmp_dir_path)

        # prepare
        #    pyproject.toml
        prep_pyproject_toml(path_pyproject_toml, path_tmp_dir)
        cmd = (
            "--path",
            path_tmp_dir,
            "--venv-relpath",
            venv_path,
        )

        # Missing venv folders --> NotADirectoryError (7)
        result = runner.invoke(fcn, cmd)
        actual_exit_code = 7

        #    venv folder(s)
        venv_relpaths = (
            ".venv",
            ".tools",
            ".doc/.venv",
        )
        for create_relpath in venv_relpaths:
            abspath_venv = resolve_joinpath(path_tmp_dir, create_relpath)
            abspath_venv.mkdir(parents=True, exist_ok=True)

        # Missing ``.in`` files --> MissingRequirementsFoldersFiles (6)
        result = runner.invoke(fcn, cmd)
        actual_exit_code = 6

        #    requirements folders (and empty files)
        prepare_folders_files(seq_in, path_tmp_dir)

        #    requirements .in (real files)
        path_cwd = path_project_base()
        for relpath_f in seq_in:
            abspath_src = resolve_joinpath(path_cwd, relpath_f)
            abspath_dest = resolve_joinpath(path_tmp_dir, relpath_f)
            shutil.copy2(abspath_src, abspath_dest)

        #    Needed by '.venv'
        seq_in_supplamental = [
            "requirements/pip.in",
            "requirements/pip-tools.in",
            "requirements/dev.in",
            "requirements/manage.in",
        ]
        prepare_folders_files(seq_in_supplamental, path_tmp_dir)
        for relpath_f in seq_in_supplamental:
            abspath_src = resolve_joinpath(path_cwd, relpath_f)
            abspath_dest = resolve_joinpath(path_tmp_dir, relpath_f)
            shutil.copy2(abspath_src, abspath_dest)

        # Limit to one venv relpath, rather than run all
        is_lock_compile = fcn.callback.__name__ == "dependencies_lock"
        result = runner.invoke(fcn, cmd)
        actual_exit_code = result.exit_code
        # Contains venv_relpath, lock file, err, exception
        actual_output = result.output  # noqa: F841
        if not is_lock_compile:
            assert actual_exit_code == expected_exit_code
        else:
            # Is lock_compile
            is_not_timeout = actual_exit_code != 10
            if is_not_timeout:
                assert actual_exit_code == expected_exit_code
                if actual_exit_code == 0:
                    # Fake a timeout
                    with patch(
                        f"{g_app_name}.cli_dependencies.is_timeout",
                        return_value=True,
                    ):
                        result = runner.invoke(fcn, cmd)
                        actual_exit_code = result.exit_code
                        assert actual_exit_code == 10
            else:
                # Timeout occurred, do not have to fake one
                pass


testdata_lock_unlock_and_back_wo_prepare = (
    (
        dependencies_unlock,
        Path(__file__).parent.joinpath("_good_files", "complete.pyproject_toml"),
        ".venv/docs",
        3,  # FileNotFoundError
    ),
    (
        dependencies_lock,
        Path(__file__).parent.joinpath("_good_files", "complete.pyproject_toml"),
        ".venv/docs",
        3,  # FileNotFoundError
    ),
)
ids_lock_unlock_and_back_wo_prepare = (
    "call dependencies_unlock. Additional file ci/kit.in",
    "call dependencies_lock. Additional file ci/kit.in",
)


@pytest.mark.parametrize(
    "func, path_pyproject_toml, venv_path, expected_exit_code",
    testdata_lock_unlock_and_back_wo_prepare,
    ids=ids_lock_unlock_and_back_wo_prepare,
)
def test_lock_unlock_and_back_wo_prepare(
    func,
    path_pyproject_toml,
    venv_path,
    expected_exit_code,
    tmp_path,
    prep_pyproject_toml,
    caplog,
    has_logging_occurred,
):
    """Test dependency lock and unlock without prepare."""
    # pytest --showlocals --log-level INFO -k "test_lock_unlock_and_back_wo_prepare" -v tests
    LOGGING["loggers"][g_app_name]["propagate"] = True
    logging.config.dictConfig(LOGGING)
    logger = logging.getLogger(name=g_app_name)
    logger.addHandler(hdlr=caplog.handler)
    caplog.handler.level = logger.level

    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path) as tmp_dir_path:
        path_tmp_dir = Path(tmp_dir_path)

        # w/o prepare pyproject.toml
        cmd = (
            "--path",
            path_tmp_dir,
            "--venv-relpath",
            venv_path,
        )
        result = runner.invoke(func, cmd)

        logger.info(result.output)
        tb = result.exc_info[2]
        # msg_info = f"traceback: {pprint(traceback.format_tb(tb))}"
        msg_info = f"traceback: {traceback.format_tb(tb)}"
        logger.info(msg_info)

        actual_exit_code = result.exit_code
        assert actual_exit_code == expected_exit_code


testdata_lock_unlock_compile_with_prepare = (
    (
        dependencies_lock,
        Path(__file__).parent.joinpath("_good_files", "complete.pyproject_toml"),
        ".venv/docs",
        True,
        False,
        6,  # 6 MissingRequirementsFoldersFiles
    ),
    (
        dependencies_unlock,
        Path(__file__).parent.joinpath("_good_files", "complete.pyproject_toml"),
        ".venv/docs",
        True,
        False,
        6,  # 6 MissingRequirementsFoldersFiles
    ),
    pytest.param(
        dependencies_lock,
        Path(__file__).parent.joinpath("_good_files", "complete.pyproject_toml"),
        ".venv/docs",
        True,
        True,
        9,
    ),
    (
        dependencies_unlock,
        Path(__file__).parent.joinpath("_good_files", "complete.pyproject_toml"),
        ".venv/docs",
        True,
        True,
        9,
    ),
)
ids_lock_unlock_compile_with_prepare = (
    "lock missing folders and files",
    "unlock missing folders and files",
    "lock nonexistant venv path",
    "unlock nonexistant venv path",
)


@pytest.mark.parametrize(
    "func, path_pyproject_toml, venv_path, is_prep_pyproject_toml, is_prep_files, expected_exit_code",
    testdata_lock_unlock_compile_with_prepare,
    ids=ids_lock_unlock_compile_with_prepare,
)
def test_lock_unlock_compile_with_prepare(
    func,
    path_pyproject_toml,
    venv_path,
    is_prep_pyproject_toml,
    is_prep_files,
    expected_exit_code,
    tmp_path,
    prep_pyproject_toml,
    path_project_base,
    prepare_folders_files,
    caplog,
    has_logging_occurred,
):
    """Test dependency lock and unlock with prepare."""
    # pytest -v --showlocals --log-level INFO -k "test_lock_unlock_compile_with_prepare" tests
    LOGGING["loggers"][g_app_name]["propagate"] = True
    logging.config.dictConfig(LOGGING)
    logger = logging.getLogger(name=g_app_name)
    logger.addHandler(hdlr=caplog.handler)
    caplog.handler.level = logger.level

    path_cwd = path_project_base()

    # Must copy otherwise path_tmp_dir will not be able to find missing reqs
    seq_reqs_relpath = (
        "requirements/pins.shared.in",
        "requirements/prod.shared.in",
        "docs/pip-tools.in",
        "docs/requirements.in",
        "requirements/pip.in",
        "requirements/pip-tools.in",
        "requirements/dev.in",
        "requirements/manage.in",
        "requirements/pins-cffi.in",
        "requirements/tox.in",
    )

    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path) as tmp_dir_path:
        path_tmp_dir = Path(tmp_dir_path)
        # prepare -- pyproject.toml
        if is_prep_pyproject_toml:
            prep_pyproject_toml(path_pyproject_toml, path_tmp_dir)

        # prepare -- venv folder(s)
        venv_relpaths = (
            ".venv",
            ".doc/.venv",
        )
        for create_relpath in venv_relpaths:
            abspath_venv = resolve_joinpath(path_tmp_dir, create_relpath)
            abspath_venv.mkdir(parents=True, exist_ok=True)

        if is_prep_files:
            prepare_folders_files(seq_reqs_relpath, path_tmp_dir)
            for relpath_f in seq_reqs_relpath:
                abspath_src = resolve_joinpath(path_cwd, relpath_f)
                abspath_dest = resolve_joinpath(path_tmp_dir, relpath_f)
                shutil.copy2(abspath_src, abspath_dest)

        cmd = (
            "--path",
            path_tmp_dir,
            "--venv-relpath",
            venv_path,
        )
        # Call cli func blind; no BackendType.is_locked
        result = runner.invoke(func, cmd)

        logger.info(f"exit_code: {result.exit_code}")
        logger.info(f"exception: {result.exception}")
        logger.info(f"output: {result.output}")

        tb = result.exc_info[2]
        # msg_info = f"traceback: {pprint(traceback.format_tb(tb))}"
        msg_info = f"traceback: {traceback.format_tb(tb)}"
        logger.info(msg_info)

        actual_exit_code = result.exit_code
        assert actual_exit_code == expected_exit_code


@pytest.mark.parametrize(
    "path_pyproject_toml, venv_path, base_relpaths, to_requirements_dir, expected_resolvable_count, expected_unresolvable_count,",
    testdata_resolve_resolvable_conflicts,
    ids=ids_resolve_resolvable_conflicts,
)
def test_cli_dependencies_requirements_fix(
    path_pyproject_toml,
    venv_path,
    base_relpaths,
    to_requirements_dir,
    expected_resolvable_count,
    expected_unresolvable_count,
    tmp_path,
    caplog,
    has_logging_occurred,
    prepare_folders_files,
    prep_pyproject_toml,
):
    """Same as resolve_resolvable_conflicts, but all venv requirements are fixed."""
    # pytest -vv --showlocals --log-level INFO -k "test_cli_dependencies_requirements_fix" tests
    LOGGING["loggers"][g_app_name]["propagate"] = True
    logging.config.dictConfig(LOGGING)
    logger = logging.getLogger(name=g_app_name)
    logger.addHandler(hdlr=caplog.handler)
    caplog.handler.level = logger.level

    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path) as tmp_dir_path:
        path_tmp_dir = Path(tmp_dir_path)

        # no pyproject.toml file --> 3
        cmd = (
            "--path",
            path_tmp_dir,
            "--venv-relpath",
            venv_path,
            "--dry-run",
        )
        result = runner.invoke(requirements_fix, cmd)
        assert result.exit_code == 3

        # prepare
        #    Copy to base dir
        path_dest_pyproject_toml = prep_pyproject_toml(
            path_pyproject_toml, path_tmp_dir
        )

        # no .venv folder. Or anything else
        cmd = (
            "--path",
            path_dest_pyproject_toml,
            "--venv-relpath",
            venv_path,
            "--dry-run",
        )
        result = runner.invoke(requirements_fix, cmd)
        assert result.exit_code == 5

        #    venv_path must be a folder. If not or no folder --> NotADirectoryError
        prep_these = (".venv/.python-version",)
        prepare_folders_files(prep_these, path_tmp_dir)

        # Missing .in, .unlock, and/or .lock files --> MissingRequirementsFoldersFiles
        cmd = (
            "--path",
            path_dest_pyproject_toml,
            "--venv-relpath",
            venv_path,
            "--dry-run",
        )
        result = runner.invoke(requirements_fix, cmd)
        assert result.exit_code == 8

        #   Create requirements folder, since there are no base_relpaths
        prep_these = ("requirements/junk.deleteme",)
        prepare_folders_files(prep_these, path_tmp_dir)

        #   Copy empties
        prep_these = []
        for suffix in (".in", ".unlock", ".lock"):
            for base_relpath in base_relpaths:
                prep_these.append(f"{base_relpath}{suffix}")
            prepare_folders_files(prep_these, path_tmp_dir)

        #    Copy real .unlock and .lock files
        for abspath_src in to_requirements_dir:
            src_abspath = str(abspath_src)
            abspath_dest = path_tmp_dir / "requirements" / abspath_src.name
            shutil.copy(src_abspath, abspath_dest)

        cmd = (
            "--path",
            path_dest_pyproject_toml,
            "--venv-relpath",
            venv_path,
            "--dry-run",
        )
        result = runner.invoke(requirements_fix, cmd, catch_exceptions=True)
        assert result.exit_code == 0


testdata_lock_compile_requires_pip_tools = (
    (
        dependencies_lock,
        Path(__file__).parent.joinpath("_req_files", "venvs_minimal.pyproject_toml"),
        ".venv/docs",
        (
            "docs/pip-tools",
            "requirements/pins.shared",
        ),
        5,
    ),
    (
        dependencies_lock,
        Path(__file__).parent.joinpath("_req_files", "venvs_minimal.pyproject_toml"),
        ".awesome",
        (
            "docs/pip-tools",
            "requirements/pins.shared",
            "requirements/pip-tools",
            "requirements/pip",
        ),
        9,
    ),
)
ids_lock_compile_requires_pip_tools = (
    "pip-tools is not installed",
    "no such venv key",
)


@pytest.mark.parametrize(
    "fcn, path_pyproject_toml, venv_path, seqs_reqs, expected_exit_code",
    testdata_lock_compile_requires_pip_tools,
    ids=ids_lock_compile_requires_pip_tools,
)
def test_lock_compile_requires_pip_tools(
    fcn,
    path_pyproject_toml,
    venv_path,
    seqs_reqs,
    expected_exit_code,
    tmp_path,
    prep_pyproject_toml,
    caplog,
    path_project_base,
):
    """Test lock_compile install pip-tools 5"""
    # pytest -vv --showlocals --log-level INFO -k "test_lock_compile_requires_pip_tools" tests
    LOGGING["loggers"][g_app_name]["propagate"] = True
    logging.config.dictConfig(LOGGING)
    logger = logging.getLogger(name=g_app_name)
    logger.addHandler(hdlr=caplog.handler)
    caplog.handler.level = logger.level

    path_cwd = path_project_base()

    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path) as tmp_dir_path:
        path_tmp_dir = Path(tmp_dir_path)
        cmd = (
            "--path",
            path_tmp_dir,
            "--venv-relpath",
            venv_path,
        )

        # prepare
        #    Copy to base dir
        prep_pyproject_toml(path_pyproject_toml, path_tmp_dir)

        # copy reqs
        for src_relpath in seqs_reqs:
            abspath_src = cast("Path", resolve_joinpath(path_cwd, src_relpath))
            abspath_src_in = replace_suffixes_last(abspath_src, SUFFIX_IN)
            src_in_abspath = str(abspath_src_in)
            abspath_dest = cast("Path", resolve_joinpath(path_tmp_dir, src_relpath))
            abspath_dest_in = replace_suffixes_last(abspath_dest, SUFFIX_IN)
            abspath_dest_in.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(src_in_abspath, abspath_dest_in)

        #    create all venv folders. If missing --> 7
        venv_dirs = (".venv/docs", ".awesome", ".tools")
        for venv_dir in venv_dirs:
            path_dir = cast("Path", resolve_joinpath(path_tmp_dir, venv_dir))
            path_dir.mkdir(parents=True, exist_ok=True)

        if expected_exit_code == 5:
            with patch(
                f"{g_app_name}.lock_inspect.is_package_installed",
                return_value=False,
            ):
                result = runner.invoke(dependencies_lock, cmd)
                assert result.exit_code == expected_exit_code
        else:
            result = runner.invoke(dependencies_lock, cmd, catch_exceptions=True)

            logger.info(f"exception: {result.exception}")
            logger.info(f"output: {result.output}")

            tb = result.exc_info[2]
            # msg_info = f"traceback: {pprint(traceback.format_tb(tb))}"
            msg_info = f"traceback: {traceback.format_tb(tb)}"
            logger.info(msg_info)

            assert result.exit_code == expected_exit_code


testdata_lock_compile_valueerror = (
    (
        dependencies_lock,
        Path(__file__).parent.joinpath(
            "_bad_files",
            "keys-wrong-data-type.pyproject_toml",
        ),
        ".venv",
        (
            "docs/pip-tools",
            "requirements/pins.shared",
        ),
        8,
    ),
    (
        dependencies_unlock,
        Path(__file__).parent.joinpath(
            "_bad_files",
            "keys-wrong-data-type.pyproject_toml",
        ),
        ".venv",
        (
            "docs/pip-tools",
            "requirements/pins.shared",
        ),
        8,
    ),
    (
        requirements_fix,
        Path(__file__).parent.joinpath(
            "_bad_files",
            "keys-wrong-data-type.pyproject_toml",
        ),
        ".venv",
        (
            "docs/pip-tools",
            "requirements/pins.shared",
        ),
        6,
    ),
)
ids_lock_compile_valueerror = (
    "lock expecting tool.venvs.reqs to be a sequence",
    "unlock expecting tool.venvs.reqs to be a sequence",
    "fix expecting tool.venvs.reqs to be a sequence",
)


@pytest.mark.parametrize(
    "fcn, path_pyproject_toml, venv_path, seqs_reqs, expected_exit_code",
    testdata_lock_compile_valueerror,
    ids=ids_lock_compile_valueerror,
)
def test_lock_compile_valueerror(
    fcn,
    path_pyproject_toml,
    venv_path,
    seqs_reqs,
    expected_exit_code,
    tmp_path,
    prep_pyproject_toml,
    caplog,
):
    """Test lock_compile ValueError 8"""
    # pytest -vv --showlocals --log-level INFO -k "test_lock_compile_valueerror" tests
    LOGGING["loggers"][g_app_name]["propagate"] = True
    logging.config.dictConfig(LOGGING)
    logger = logging.getLogger(name=g_app_name)
    logger.addHandler(hdlr=caplog.handler)
    caplog.handler.level = logger.level

    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path) as tmp_dir_path:
        path_tmp_dir = Path(tmp_dir_path)

        # prepare
        #    Copy to base dir
        prep_pyproject_toml(path_pyproject_toml, path_tmp_dir)

        cmd = (
            "--path",
            path_tmp_dir,
            "--venv-relpath",
            venv_path,
        )

        result = runner.invoke(fcn, cmd, catch_exceptions=True)
        assert result.exit_code == expected_exit_code
