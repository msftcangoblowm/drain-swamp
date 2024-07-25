"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

.. code-block:: shell

   pytest --showlocals --log-level INFO tests/test_run_cmd.py
   pytest --showlocals --cov="drain_swamp" --cov-report=term-missing tests/test_run_cmd.py

"""

import pytest

from drain_swamp._run_cmd import run_cmd


def test_run_cmd(tmp_path):
    # pytest --showlocals --log-level INFO -k "test_run_cmd" tests
    # expecting Sequence
    cwd = tmp_path
    invalids = (0.1234, None)
    for invalid in invalids:
        with pytest.raises(TypeError):
            run_cmd(invalid)

        # env is None or not os._Environ
        cmd = ("bin/true",)
        t_ret = run_cmd(cmd, env=invalid, cwd=cwd)
        out, err, exit_code, str_exc = t_ret
        assert str_exc == """No such file or directory bin/true"""

        cmd = ("/bin/true",)
        t_ret = run_cmd(cmd, env=invalid, cwd=cwd)
        out, err, exit_code, str_exc = t_ret
        assert exit_code == 0
