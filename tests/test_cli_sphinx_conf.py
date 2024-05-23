"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

Unittest for entrypoint, cli_sphinx_conf

Without coverage

.. code-block:: shell

   pytest --showlocals --log-level INFO tests/test_cli_sphinx_conf.py

With coverage

Needs a config file to specify exact files to include / omit from report.
Will fail with exit code 1 even with 100% coverage

.. code-block:: shell

   pytest --showlocals --cov="drain_swamp" --cov-report=term-missing tests/test_cli_sphinx_conf.py


"""

import logging
import logging.config
import traceback
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from drain_swamp.cli_sphinx_conf import (
    entrypoint_name,
    main,
    sphinx_conf_snip,
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


testdata_find_sphinx_conf = (
    (
        Path(__file__).parent.joinpath("_good_files", "no_project_name.pyproject_toml"),
        "docs",
        Path(__file__).parent.joinpath(
            "test_snip", "test_snip_harden_one_snip__with_id_.txt"
        ),
        "asdf",
        6,
    ),
    (
        Path(__file__).parent.joinpath("_good_files", "complete.pyproject_toml"),
        "doc",
        Path(__file__).parent.joinpath(
            "test_snip", "test_snip_harden_one_snip__with_id_.txt"
        ),
        "asdf",
        0,
    ),
    (
        Path(__file__).parent.joinpath("_good_files", "complete.pyproject_toml"),
        "doc",
        Path(__file__).parent.joinpath(
            "test_snip", "test_snip_harden_one_snip__with_id_.txt"
        ),
        "george",
        1,
    ),
)
ids_find_sphinx_conf = (
    "doc/ folder. In pyproject.toml no project.name",
    "docs/ folder. In pyproject.toml has project.name",
    "wrong snippet code. Replacement will not occur",
)


@pytest.mark.parametrize(
    "abspath_pyproject_src, doc_relpath, path_confpy_src, id_, int_expected",
    testdata_find_sphinx_conf,
    ids=ids_find_sphinx_conf,
)
def test_find_sphinx_conf(
    abspath_pyproject_src,
    doc_relpath,
    path_confpy_src,
    id_,
    int_expected,
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

    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path) as tmp_dir_path:
        path_tmp_dir = Path(tmp_dir_path)

        # no prep
        cmd = [
            "--path",
            path_tmp_dir,
            "--snip",
            id_,
            "--kind",
            "0.0.1",
        ]

        # Expecting to find doc/ or docs/ folder
        result = runner.invoke(sphinx_conf_snip, cmd)
        assert result.exit_code == 3

        # prepare docs/ folder
        path_dir = path_tmp_dir.joinpath(doc_relpath)
        path_dir.mkdir()

        # Need a [docs folder]/conf.py
        result = runner.invoke(sphinx_conf_snip, cmd)
        assert result.exit_code == 4

        # prepare [docs folder]/conf.py
        contents = path_confpy_src.read_text()
        path_confpy = path_dir.joinpath("conf.py")
        path_confpy.write_text(contents)
        assert path_confpy.exists() and path_confpy.is_file()

        # pyproject.toml not found
        result = runner.invoke(sphinx_conf_snip, cmd)
        assert result.exit_code == 5
        logger.info(f"stdout (5): {result.stdout}")

        # prepare pyproject.toml
        prep_pyproject_toml(abspath_pyproject_src, path_tmp_dir)
        path_pyproject_abspath = path_tmp_dir.joinpath("pyproject.toml")
        assert path_pyproject_abspath.exists() and path_pyproject_abspath.is_file()

        # Need a setup.py too! Otherwise version_semantic

        pass

        """During testing, the Path.cwd is the path_tmp_dir, which is
        a fake project folder"""
        with patch("pathlib.Path.cwd", return_value=path_tmp_dir):
            result = runner.invoke(sphinx_conf_snip, cmd)

        # result     = <Result PackageNotFoundError('complete-awesome-perfect')>

        actual = result.exit_code
        tb = result.exc_info[2]
        exc = result.exception
        logger.info(f"stdout (0|1): {repr(exc)}")
        logger.info(f"stdout (0|1): {traceback.print_tb(tb)}")

        assert has_logging_occurred(caplog)

        assert actual == int_expected
