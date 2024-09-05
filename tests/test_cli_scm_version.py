"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

Unit test -- Module

.. code-block:: shell

   python -m coverage run --source='drain_swamp.cli_scm_version' -m pytest \
   --showlocals tests/test_cli_scm_version.py && coverage report \
   --data-file=.coverage --include="**/cli_scm_version.py"

Integration test

.. code-block:: shell

   make coverage
   pytest --showlocals --cov="drain_swamp" --cov-report=term-missing \
   --cov-config=pyproject.toml tests

"""

import logging
import logging.config
from pathlib import Path
from unittest.mock import patch

import pytest  # noqa: F401
from click.testing import CliRunner

from drain_swamp.cli_scm_version import (
    entrypoint_name,
    get_scm_version,
    main,
    write_scm_version,
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


def test_get_scm_version_missing_pyproject_toml(tmp_path, prepare_folders_files):
    """Test write_scm_version and get_scm_version."""
    # pytest --showlocals --log-level INFO -k "test_get_scm_version_missing_pyproject_toml" tests
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path) as tmp_dir_path:
        path_tmp_dir = Path(tmp_dir_path)
        seq_rel_path = ("_version.py",)
        path_version_file = path_tmp_dir.joinpath(seq_rel_path[0])

        # prepare
        prepare_folders_files(seq_rel_path, path_tmp_dir)

        # no pyproject.toml --> LookupError (3). Missing sections
        scm_ver = "0.0.1"
        cmd = (scm_ver, "--path", path_tmp_dir, "--write-to", seq_rel_path[0])
        result = runner.invoke(write_scm_version, cmd)
        assert result.exit_code == 3
        assert path_version_file.stat().st_size == 0
        del scm_ver

        # no pyproject.toml --> LookupError (3). Missing sections
        cmd = ("--path", path_tmp_dir, "--is-write", "--write-to", seq_rel_path[0])
        result = runner.invoke(get_scm_version, cmd)
        assert result.exit_code == 3


def test_get_scm_version_normal(
    tmp_path, prep_pyproject_toml, prepare_folders_files, caplog, has_logging_occurred
):
    """How to simulate reading version from git?

    .. todo:: is git

       skip if no git
       skip if git not initialized

    """
    # pytest --showlocals --log-level INFO -k "test_get_scm_version_normal" tests
    LOGGING["loggers"][g_app_name]["propagate"] = True
    logging.config.dictConfig(LOGGING)
    logger = logging.getLogger(name=g_app_name)
    logger.addHandler(hdlr=caplog.handler)
    caplog.handler.level = logger.level

    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path) as tmp_dir_path:
        path_tmp_dir = Path(tmp_dir_path)
        version_file = "src/complete_awesome_perfect/_version.py"
        seq_rel_path = (version_file,)
        path_version_file = path_tmp_dir.joinpath(seq_rel_path[0])

        # prepare
        #    pyproject.toml
        p_toml_file = Path(__file__).parent.joinpath(
            "_good_files", "complete-manage-pip-prod-unlock.pyproject_toml"
        )
        prep_pyproject_toml(p_toml_file, path_tmp_dir)
        #    version_file folders and empty file
        prepare_folders_files(seq_rel_path, path_tmp_dir)

        #    version file (skeleton/minimal)
        str_version_file = (
            """__version__ = version = '0.2.0'\n"""
            """__version_tuple__ = version_tuple = (0, 2, 0)\n\n"""
        )
        path_version_file.write_text(str_version_file)

        # act -- get_scm_version
        cmd = ("--path", path_tmp_dir, "--is-write", "--write-to", seq_rel_path[0])
        result = runner.invoke(get_scm_version, cmd)
        assert result.exit_code == 0
        #    repo scm version
        assert len(result.output) != 0
        scm_ver = result.output
        #    wrote to version_file
        assert path_version_file.stat().st_size != 0
        path_version_file.unlink()

        # act -- write_scm_version -- valid semantic version str
        cmd = (scm_ver, "--path", path_tmp_dir, "--write-to", seq_rel_path[0])
        result = runner.invoke(write_scm_version, cmd)
        assert result.exit_code == 0
        assert path_version_file.stat().st_size != 0
        path_version_file.unlink()

        # version_file from pyproject.toml
        cmd = (scm_ver, "--path", path_tmp_dir)
        result = runner.invoke(write_scm_version, cmd)
        assert result.exit_code == 0
        assert path_version_file.stat().st_size != 0
        path_version_file.unlink()

        # invalid semantic version str -->  ValueError(4)
        scm_ver = "golf balls get lost"
        cmd = (scm_ver, "--path", path_tmp_dir)
        result = runner.invoke(write_scm_version, cmd)
        assert result.exit_code == 4

        """upstream bug. Passes regex, but invalid semantic version str.
        exception not caught in setuptools_scm.version.tag_to_version

        Exception properly handled in setuptools_scm._version_cls._version_as_tuple"""
        with patch(
            "drain_swamp.cli_scm_version.scm_version",
            return_value="0.0.1-dev1.g1234123",
        ):
            cmd = ("--path", path_tmp_dir, "--is-write", "--write-to", seq_rel_path[0])
            result = runner.invoke(get_scm_version, cmd)
            assert result.exit_code == 4

    assert has_logging_occurred(caplog)
