"""git (and git config) utility class, WorkDir.

.. seealso::

   Credit
   `[Author] <https://github.com/pypa/setuptools-scm/blob/main/pyproject.toml>`_
   `[Source] <https://github.com/pypa/setuptools_scm/blob/main/testing/wd_wrapper.py>`_
   `[License: MIT] <https://github.com/pypa/setuptools-scm/blob/main/LICENSE>`_

"""

from __future__ import annotations

import itertools
from pathlib import Path
from typing import Any


class WorkDir:
    """Work with git and git config.

    :cvar commit_command: Non-signed :code:`git commit` command
    :vartype commit_command: str
    :cvar signed_commit_command: Signed :code:`git commit` command
    :vartype signed_commit_command: str
    :cvar add_command: :code:`git add` command

    :ivar cwd: current working folder
    :vartype cwd: pathlib.Path
    """

    commit_command: str
    signed_commit_command: str
    add_command: str

    def __repr__(self) -> str:
        """For programmically restore instance.

        :returns: WorkDir repr
        :rtype: str
        """
        return f"<WorkDir {self.cwd}>"

    def __init__(self, cwd: Path) -> None:
        """WorkDir constructor."""
        self.cwd = cwd
        self.__counter = itertools.count()

    def __call__(self, cmd: list[str] | str, **kw: object) -> str:
        """Run a subprocess command.

        :param cmd:

           Full command to execute in a subprocess. On Windows, the
           executable path must be resolved

        :type cmd: list[str] | str
        :param kw: keyword options
        :type kw: object
        :returns: subprocess stdout
        :rtype: str
        """
        if kw:
            assert isinstance(cmd, str), "formatting the command requires text input"
            cmd = cmd.format(**kw)
        from setuptools_scm._run_cmd import run

        return run(cmd, cwd=self.cwd).stdout

    def write(self, name: str, content: str | bytes) -> Path:
        """Write file.

        :param name: relative path to file
        :type name: str
        :param content: contents to write to file
        :type content: str | bytes
        :returns: file absolute path
        :rtype: pathlib.Path
        """
        path = self.cwd / name
        if isinstance(content, bytes):
            path.write_bytes(content)
        else:
            path.write_text(content, encoding="utf-8")
        return path

    def _reason(self, given_reason: str | None) -> str:
        """If a git commit message is None, use a fallback message.

        :param given_reason: commit message
        :type given_reason: str | None
        :returns: commit message
        :rtype: str
        """
        if given_reason is None:
            return f"number-{next(self.__counter)}"
        else:
            return given_reason

    def add_and_commit(
        self, reason: str | None = None, signed: bool = False, **kwargs: object
    ) -> None:
        """Runs git add and git commit commands.

        :param reason:

           Default None. commit message. If None a fallback reason will be used.

        :type reason: str | None
        :param signed:

           Default False. True to sign the commit otherwise commit not signed.

        :type signed: bool
        :param kwargs: Additional keyword options to pass onto commit
        :type kwargs: object
        """
        self(self.add_command)
        self.commit(reason=reason, signed=signed, **kwargs)

    def commit(self, reason: str | None = None, signed: bool = False) -> None:
        """Wraps :code:`git commit` command.

        :param reason:

           Default None. commit message. If None a fallback reason will be used.

        :type reason: str | None
        :param signed:

           Default False. True to sign the commit otherwise commit not signed.

        :type signed: bool
        """
        reason = self._reason(reason)
        self(
            self.commit_command if not signed else self.signed_commit_command,
            reason=reason,
        )

    def commit_testfile(self, reason: str | None = None, signed: bool = False) -> None:
        """Create a file. For unittesting this class.

        :param reason:

           Default None. commit message. If None a fallback reason will be used.

        :type reason: str | None
        :param signed:

           Default False. True to sign the commit otherwise commit not signed.

        :type signed: bool
        """
        reason = self._reason(reason)
        self.write("test.txt", f"test {reason}")
        self(self.add_command)
        self.commit(reason=reason, signed=signed)

    def get_version(self, **kw: Any) -> str:
        """Get current scm version.

        :param kw: keyword options to pass thru
        :type kw: typing.Any
        :returns: current scm version
        :rtype: str
        """
        __tracebackhide__ = True
        from setuptools_scm import get_version

        version = get_version(root=self.cwd, fallback_root=self.cwd, **kw)
        print(self.cwd.name, version, sep=": ")
        return version
