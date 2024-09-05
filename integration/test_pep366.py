"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

An integration unittest. **DO NOT** include in :code:`coverage run`.

This unit test must **avoid importing anything from drain_swamp** package.

pytest config file, ``tests/conftest.py``, imports from drain_swamp and
therefore pytest is avoided.

.. warning:: 2nd run

   integration unittest are not run along with 1st run unittests.

   Does not play nice with coverage. Necessary to isolate execution; run seperately.

"""

import subprocess
import sys
import unittest
from pathlib import Path


class TestPep366(unittest.TestCase):
    """Call entrypoint from code base rather than from installed package."""

    def setUp(self):
        """Setup cwd and path to this unittest."""
        if "__pycache__" in __file__:
            # cached
            self.path_tests = Path(__file__).parent.parent
        else:
            # not cached
            self.path_tests = Path(__file__).parent
        self.cwd = self.path_tests.parent

    def test_runs_off_source_code(self):
        """Run from source code."""
        cmds = (
            (
                (sys.executable, "src/drain_swamp/cli_igor.py", "list"),
                lambda x: x == 0,
            ),
            (
                (sys.executable, "src/drain_swamp/cli_unlock.py", "is_lock"),
                lambda x: x in [0, 1],
            ),
        )

        for cmd, fcn_exit_compare in cmds:
            try:
                proc = subprocess.run(
                    cmd,
                    shell=False,
                    stdout=subprocess.PIPE,  # click.secho --> sys.stdout
                    stderr=subprocess.PIPE,
                    cwd=self.cwd,  # set cwd. Could have been done within cmd
                    text=True,
                )
            except subprocess.CalledProcessError:  # pragma: no cover
                assert False
            else:
                # str_out = proc.stdout
                # str_err = proc.stderr
                exit_code = proc.returncode
                is_code_match = fcn_exit_compare(exit_code)
                assert is_code_match

    def test_with_relative_path(self):
        """Supply path option.

        --path [relative path]

        Equivalent to
        :code:`python src/drain_swamp/cli_unlock.py is_lock --path pyproject.toml`
        """
        fcn_exit_compare = lambda x: x in [0, 1]  # noqa: E731

        cmd = (
            sys.executable,
            "src/drain_swamp/cli_unlock.py",
            "is_lock",
            "--path",
            "pyproject.toml",
        )
        try:
            proc = subprocess.run(
                cmd,
                shell=False,  # shell understands the relative path
                stdout=subprocess.PIPE,  # click.secho --> sys.stdout
                stderr=subprocess.PIPE,
                cwd=self.cwd,  # set cwd. Could have been done within cmd
                text=True,
            )
        except subprocess.CalledProcessError:  # pragma: no cover
            assert False
        else:
            # str_out = proc.stdout
            # str_err = proc.stderr
            exit_code = proc.returncode
            is_code_match = fcn_exit_compare(exit_code)
            assert is_code_match


if __name__ == "__main__":  # pragma: no cover
    """See warning about necessity for execution isolation

    .. code-block:: shell

       python -m unittest integration.test_pep366 --locals

       python -m unittest integration.test_pep366 \
       -k TestPep366.test_runs_off_source_code --locals --buffer

       python -m unittest integration.test_pep366 \
       -k TestPep366.test_with_relative_path --locals --buffer

    """
    unittest.main(tb_locals=True)
