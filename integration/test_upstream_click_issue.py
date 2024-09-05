"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

**Underlying assumption**

Throwing random data types at a click entrypoint, caused failures. Especially
with :py:class:`pathlib.Path`.

**Feedback**

After bringing up the issue, turns out the shell only supports str, not random
data types.

**Conclusion**

Non-issue

.. code-block:: shell

       python -m unittest integration.test_upstream_click_issue --locals


"""

import traceback
import unittest
from pathlib import Path

import click
from click.testing import CliRunner

help_path = "Provide a Path. relative or absolute"

EPILOG_CHOKE = """
Description:

click.Path(resolve_path=True) assumes can resolve the user supplied input.
A float is not a Path, so cannot be resolved. Results in a TypeError and the
entrypoint crashing with a traceback.

End users should never be presented with a traceback. When click is
dealing with these issues the normal exit code is 2

Reproduce issue:

python -m unittest integration.test_upstream_click_issue

Expected behavior:

Do not make assumptions regarding the user input type. Handler should
accept typing.Any

- Ideally and gracefully, use the default as a fallback. No exit code

- Otherwise exit code 2

Why'd this happen?:

Python typing encourages parameters ideally to accept typing.Any
Unless already handled elsewhere, assuming parameters have particular
type(s) is a recipe for disaster. Should always check

Environment:

click: 8.1.7
Python: py39
OS: GNU/Linux
distro: Void Linux

Output:

  File ".venv/lib/python3.9/site-packages/click/testing.py", line 408, in invoke
    return_value = cli.main(args=args or (), prog_name=prog_name, **extra)
  File ".venv/lib/python3.9/site-packages/click/core.py", line 1077, in main
    with self.make_context(prog_name, args, **extra) as ctx:
  File ".venv/lib/python3.9/site-packages/click/core.py", line 943, in make_context
    self.parse_args(ctx, args)
  File ".venv/lib/python3.9/site-packages/click/core.py", line 1408, in parse_args
    value, args = param.handle_parse_result(ctx, opts, args)
  File ".venv/lib/python3.9/site-packages/click/core.py", line 2400, in handle_parse_result
    value = self.process_value(ctx, value)
  File ".venv/lib/python3.9/site-packages/click/core.py", line 2356, in process_value
    value = self.type_cast_value(ctx, value)
  File ".venv/lib/python3.9/site-packages/click/core.py", line 2344, in type_cast_value
    return convert(value)
  File ".venv/lib/python3.9/site-packages/click/core.py", line 2316, in convert
    return self.type(value, param=self, ctx=ctx)
  File ".venv/lib/python3.9/site-packages/click/types.py", line 83, in __call__
    return self.convert(value, param, ctx)
  File ".venv/lib/python3.9/site-packages/click/types.py", line 869, in convert
    rv = os.fsdecode(pathlib.Path(rv).resolve())
  File "~/.pyenv/versions/3.9.16/lib/python3.9/pathlib.py", line 1082, in __new__
    self = cls._from_parts(args, init=False)
  File "~/.pyenv/versions/3.9.16/lib/python3.9/pathlib.py", line 707, in _from_parts
    drv, root, parts = self._parse_args(args)
  File "~/.pyenv/versions/3.9.16/lib/python3.9/pathlib.py", line 691, in _parse_args
    a = os.fspath(a)
F
======================================================================
FAIL: test_choke_on_this (integration.test_upstream_click_issue.TestChokeOnNonPath)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "integration/test_upstream_click_issue.py", line 86, in test_choke_on_this
    assert False
    cmd = ('--path', 0.1234)
    exit_code = 1
    result = <Result TypeError('expected str, bytes or os.PathLike object, not float')>
    runner = <click.testing.CliRunner object at 0x7fdb2060c4c0>
    self = <integration.test_upstream_click_issue.TestChokeOnNonPath testMethod=test_choke_on_this>
    str_tb = ...
    tb = <traceback object at 0x7fdb20b753c0>
AssertionError

----------------------------------------------------------------------
Ran 1 test in 0.003s

FAILED (failures=1)


"""


@click.group(
    context_settings={"help_option_names": ["-h", "--help"]},
)
@click.version_option(version="0.0.1")
def main():
    """Command-line. Prints usage."""


@main.command(
    "choke",
    context_settings={"ignore_unknown_options": True},
    epilog=EPILOG_CHOKE,
)
@click.option(
    "-p",
    "--path",
    "path",
    default=Path.cwd(),
    type=click.Path(exists=False, file_okay=False, dir_okay=True, resolve_path=True),
    help=help_path,
)
def choke_on_non_path(path):
    """When a relative path, gets resolved, but returns a str not pathlib.Path.

    $> cd integrations
    $> printf 'test_upstream_click_issue.py choke --path=%f' 0.1234 | xargs python
    path: /home/faulkmore/Downloads/git_decimals/drain_swamp/integration/0.123400 <class 'str'>
    """
    print(f"path: {path} {type(path)}")
    if isinstance(path, str):
        path = Path(path)


class TestChokeOnNonPath(unittest.TestCase):
    """Demonstrate failure when sending a non-path."""

    def test_choke_on_this(self):
        """This is bypassing the shell, which was the mistake.

        The shell treats everything as a string

        .. seealso::

           `click#2742 <https://github.com/pallets/click/issues/2742>`_

            Thanks `David Lord <https://github.com/davidism>`_ for your time

        """
        runner = CliRunner()
        cmd = (
            "--path",
            0.1234,  # <-- Shell normally would treat as str, not float
        )
        # result = <Result TypeError('expected str, bytes or os.PathLike object, not float')>
        result = runner.invoke(choke_on_non_path, cmd)

        # An uncatchable (within the click command, choke_on_non_path) TypeError
        # is equivalent to click crashing
        assert result.exception.__class__ == TypeError

        tb = result.exc_info[2]
        # str_tb = traceback.format_tb(tb)
        traceback.print_tb(tb)

        exit_code = result.exit_code
        # ideally use the default, Path.cwd() and exit code == 0
        assert exit_code != 2  # expecting 2
        assert exit_code == 1  # meaningless exit code

        # uncomment to see the locals
        # assert False
        pass


if __name__ == "__main__":  # pragma: no cover
    """Process shield."""
    unittest.main(tb_locals=True)
