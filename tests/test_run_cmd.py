"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

Module _run_cmd encapsulates subprocess typical usage.

Unit test -- Module

.. code-block:: shell

   python -m coverage run --source='drain_swamp._run_cmd' -m pytest \
   --showlocals tests/test_run_cmd.py && coverage report \
   --data-file=.coverage --include="**/_run_cmd.py"

Integration test

.. code-block:: shell

   make coverage
   pytest --showlocals --cov="drain_swamp" --cov-report=term-missing \
   --cov-config=pyproject.toml tests

"""

import logging
import logging.config
import os
import sys

import pytest

from drain_swamp._run_cmd import run_cmd
from drain_swamp._safe_path import (
    is_win,
    resolve_path,
)
from drain_swamp.constants import (
    LOGGING,
    g_app_name,
)


def test_run_cmd(tmp_path, prepare_folders_files, caplog, has_logging_occurred):
    """Test run_cmd."""
    # pytest --showlocals --log-level INFO -k "test_run_cmd" tests
    LOGGING["loggers"][g_app_name]["propagate"] = True
    logging.config.dictConfig(LOGGING)
    logger = logging.getLogger(name=g_app_name)
    logger.addHandler(hdlr=caplog.handler)
    caplog.handler.level = logger.level

    # expecting Sequence
    cwd = tmp_path
    env = os.environ

    # cmd unsupported type
    invalids = (
        0.1234,
        None,
    )
    for invalid in invalids:
        with pytest.raises(TypeError):
            run_cmd(invalid)

        # executable path is incorrect. env --> None. cwd --> None
        cmd = ("bin/true",)
        t_ret = run_cmd(cmd, env=invalid, cwd=invalid)
        out, err, exit_code, str_exc = t_ret
        if is_win():
            expected_msg = """The system cannot find the file specified"""
        else:
            expected_msg = """No such file or directory"""
        assert str_exc.startswith(expected_msg)

    # Something printed to stderr
    # prepare
    #    create CHANGES.rst
    seq_rel_paths = ("CHANGES.rst",)
    prepare_folders_files(seq_rel_paths, tmp_path)

    # act
    cmd = (resolve_path("drain-swamp"), "seed")
    t_ret = run_cmd(cmd, cwd=cwd)
    out, err, exit_code, str_exc = t_ret

    # verify
    assert exit_code != 0
    assert len(err.strip()) != 0

    # Something printed to stdout
    valids = (
        (sys.executable, "-V"),
        f"{sys.executable} -V",
    )
    for cmd in valids:
        logger.info(f"cmd: {cmd!r}")

        t_ret = run_cmd(cmd, env=env)
        out, err, exit_code, str_exc = t_ret
        if exit_code != 0:
            logger.info(f"str_exc: {str_exc!r}")
            logger.info(f"err: {err!r}")
            logger.info(f"out: {out!r}")
        assert exit_code == 0
        assert len(out.strip()) != 0
