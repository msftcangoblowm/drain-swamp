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

import os

import pytest

from drain_swamp._run_cmd import run_cmd
from drain_swamp._safe_path import resolve_path


def test_run_cmd(tmp_path, prepare_folders_files):
    """Test run_cmd."""
    # pytest --showlocals --log-level INFO -k "test_run_cmd" tests
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
        assert str_exc == """No such file or directory bin/true"""

    # executable path is correct
    true_path = resolve_path("true")
    valids = (
        (true_path,),
        true_path,
    )
    for cmd in valids:
        t_ret = run_cmd(cmd, cwd=cwd)
        out, err, exit_code, str_exc = t_ret
        assert exit_code == 0

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
    executable_path = resolve_path("python")
    cmd = f"{executable_path} -V"
    t_ret = run_cmd(cmd, env=env)
    out, err, exit_code, str_exc = t_ret
    assert exit_code == 0
    assert len(out.strip()) != 0
