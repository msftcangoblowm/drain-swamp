"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

drain-swamp pytest conftest.py
"""

import copy
import re
import shutil
from collections.abc import Sequence
from pathlib import (
    Path,
    PurePath,
)
from typing import Any

import pytest

from drain_swamp._run_cmd import run_cmd
from drain_swamp._safe_path import resolve_path
from drain_swamp.backend_abc import (
    get_optionals_cli,
    get_optionals_pyproject_toml,
    get_required_pyproject_toml,
)

from .wd_wrapper import WorkDir


class FileRegression:
    """Compare previous runs files.

    :ivar file_regression: file to compare against?
    :vartype file_regression: typing.Self

    .. todo:: when Sphinx<=6 is dropped

       Remove line starting with re.escape(" translation_progress=

    .. todo:: when Sphinx<7.2 is dropped

       Remove line starting with original_url=

    """

    ignores = (
        # Remove when support for Sphinx<=6 is dropped,
        re.escape(" translation_progress=\"{'total': 0, 'translated': 0}\""),
        # Remove when support for Sphinx<7.2 is dropped,
        r"original_uri=\"[^\"]*\"\s",
    )

    def __init__(self, file_regression: "FileRegression") -> None:
        """FileRegression constructor."""
        self.file_regression = file_regression

    def check(self, data: str, **kwargs: dict[str, Any]) -> str:
        """Check previous run against current run file.

        :param data: file contents
        :type data: str
        :param kwargs: keyword options are passed thru
        :type kwargs: dict[str, typing.Any]
        :returns: diff of file contents?
        :rtype: str
        """
        return self.file_regression.check(self._strip_ignores(data), **kwargs)

    def _strip_ignores(self, data: str) -> str:
        """Helper to strip ignores from data.

        :param data: file contents w/o ignore statements
        :type data: str
        :returns: sanitized file contents
        :rtype: str
        """
        cls = type(self)
        for ig in cls.ignores:
            data = re.sub(ig, "", data)
        return data


@pytest.fixture()
def file_regression(file_regression: "FileRegression") -> FileRegression:
    """Comparison files will need updating.

    .. seealso::

       Awaiting resolution of `pytest-regressions#32 <https://github.com/ESSS/pytest-regressions/issues/32>`_

    """
    return FileRegression(file_regression)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    attach each test's TestReport to the test Item so fixtures can
    decide how to finalize based on the test result.

    fixtures can access the TestReport from the `request` fixture at
    `request.node.test_report`.

    .. seealso::

       https://stackoverflow.com/a/70598731

    """
    test_report = (yield).get_result()
    if test_report.when == "call":
        item.test_report = test_report


@pytest.fixture()
def has_logging_occurred():
    """Display caplog capture text.

    Usage

    .. code-block: text

       import pytest
       import logging
       import logging.config
       from drain_swamp.constants import g_app_name, LOGGING

       def test_something(caplog, has_logging_occurred):
           LOGGING['loggers'][g_app_name]['propagate'] = True
           logging.config.dictConfig(LOGGING)
           logger = logging.getLogger(name=g_app_name)
           logger.addHandler(hdlr=caplog.handler)
           caplog.handler.level = logger.level
           assert has_logging_occurred(caplog)

    .. seealso::

       https://github.com/pytest-dev/pytest/discussions/11011
       https://github.com/thebuzzstop/pytest_caplog/tree/master
       `pass params fixture <https://stackoverflow.com/a/44701916>`_

    """

    def _method(caplog) -> bool:
        """Check if there is at least one log message. Print log messages.

        :returns: True if logging occurred otherwise False
        :rtype: bool
        """
        print("\nCAPLOG:")
        output = caplog.text.rstrip("\n").split(sep="\n")
        if output == [""]:
            print("Nothing captured")
            return False
        for i in range(len(output)):
            print(f"{i}: {output[i]}")
        return True

    return _method


@pytest.fixture()
def prepare_folders_files(request):
    """Prepare folders and files within folder."""

    set_folders = set()

    def _method(seq_rel_paths, tmp_path):
        """Creates folders and empty files

        :param seq_rel_paths: Relative file paths. Creates folders as well
        :type seq_rel_paths:

           collections.abc.Sequence[str | pathlib.Path] | collections.abc.MutableSet[str | pathlib.Path]

        :param tmp_path: Start absolute path
        :type tmp_path: pathlib.Path
        """
        set_abs_paths = set()
        is_seq = seq_rel_paths is not None and (
            isinstance(seq_rel_paths, Sequence) or isinstance(seq_rel_paths, set)
        )
        if is_seq:
            for posix in seq_rel_paths:
                if isinstance(posix, str):
                    abs_path = tmp_path.joinpath(*posix.split("/"))
                elif issubclass(type(posix), PurePath):
                    if not posix.is_absolute():
                        abs_path = tmp_path / posix
                    else:  # pragma: no cover
                        # already absolute
                        abs_path = posix
                else:
                    abs_path = None

                if abs_path is not None:
                    set_abs_paths.add(abs_path)
                    set_folders.add(abs_path.parent)
                    abs_path.parent.mkdir(parents=True, exist_ok=True)
                    abs_path.touch()
        else:
            abs_path = None

        return set_abs_paths

    yield _method

    # cleanup
    if request.node.test_report.outcome == "passed":
        for abspath_folder in set_folders:
            shutil.rmtree(abspath_folder, ignore_errors=True)


@pytest.fixture()
def prep_pyproject_toml(request):
    """cli doesn't offer a ``parent_dir`` option to bypass ``--path``.
    Instead copy and rename the test ``pyproject.toml`` to the ``tmp_path``
    """
    lst_delete_me = []

    def _method(p_toml_file, path_dest_dir, rename="pyproject.toml"):
        """Copy and rename file. Does not necessarily have to be ``pyproject.toml``

        :param p_toml_file:

           Path to a ``pyproject.toml``. A copy will be made, original untouched

        :type p_toml_file: pathlib.Path
        :param path_dest_dir: destination tmp_path
        :type path_dest_dir: pathlib.Path
        :returns: Path to the copied and renamed file within it's new home, temp folder
        :rtype: pathlib.Path
        """
        if p_toml_file is not None and issubclass(type(p_toml_file), PurePath):
            # copy
            path_dest = path_dest_dir.joinpath(p_toml_file.name)
            shutil.copy(p_toml_file, path_dest_dir)
            # rename
            path_f = path_dest.parent.joinpath(rename)
            shutil.move(path_dest, path_f)
            ret = path_f
            lst_delete_me.append(path_f)
        else:
            ret = None

        return ret

    yield _method

    # cleanup
    if request.node.test_report.outcome == "passed":
        for path_delete_me in lst_delete_me:
            if (
                path_delete_me is not None
                and issubclass(type(path_delete_me), PurePath)
                and path_delete_me.exists()
                and path_delete_me.is_file()
            ):
                path_delete_me.unlink()


@pytest.fixture()
def prep_cmd_unlock_lock():
    """Prepare the cmd for:

    - drain_swamp.cli_unlock.dependencies_lock

    - drain_swamp.cli_unlock.dependencies_unlock

    """

    def _method(
        path_tmp_dir,
        t_req=(),
        d_opts={},
        add_folders=(),
        snip_co=None,
    ):
        """Prepare the cmd for pipenv-unlock [lock|unlock].

        :param path_tmp_dir: temp folder path
        :type path_tmp_dir: pathlib.Path
        :param t_req:
        :type t_req: tuple[str, pathlib.Path] | None
        :param d_opts: cli optionals target / relative path
        :type d_opts: dict[str, pathlib.Path]
        :param add_folders:

           relative paths to additional folders which contain ``.in`` requirements files

        :type add_folders: list[pathlib.Path]
        :returns:

           cmd usable with :py:mod:`subprocess` or :py:class:`click.testing.CliRunner`

        :rtype: list[str | pathlib.Path]
        """
        cmd = [
            "--path",
            path_tmp_dir,
        ]

        if t_req is not None and len(t_req) == 2:
            cmd.append("--required")
            cmd.append(t_req[0])
            cmd.append(t_req[1])

        for target, path_rel in d_opts.items():
            cmd.append("--optional")
            cmd.append(target)
            cmd.append(path_rel)

        for path_dir in add_folders:
            cmd.append("--dir")
            cmd.append(path_dir)

        if snip_co is not None:
            cmd.append("--snip")
            cmd.append(snip_co)

        return cmd

    return _method


@pytest.fixture()
def prepare_files_empties(prepare_folders_files):
    """Fixture for preparing empty files."""

    def _method(d_pyproject_toml, path_dir, d_add_files={}, d_optionals={}):
        """Prepare empty files.

        :param d_pyproject_toml: dict of a ``pyproject.toml``
        :type d_pyproject_toml: dict[str, typing.Any]
        :param path_dir: A temporary folder to place the file tree
        :type path_dir: pathlib.Path
        :param d_add_files:

           Default empty dict. Additional files. Not to be confused with
           cli optionals. Relative paths

        :type d_add_files: dict[str, pathlib.Path]
        """
        # pyproject.toml optionals + additional files (w/o optionals_cli)
        d_both = copy.deepcopy(d_add_files)
        get_optionals_pyproject_toml(
            d_both,
            d_pyproject_toml,
            path_dir,
            is_bypass=True,
        )
        seq_prepare_these = list(d_both.values())
        prepare_folders_files(seq_prepare_these, path_dir)

        d_both.clear()

        # optionals_cli
        d_both = copy.deepcopy(d_optionals)
        get_optionals_cli(
            d_both,
            path_dir,
            d_optionals,
        )
        seq_prepare_these = list(d_both.values())
        prepare_folders_files(seq_prepare_these, path_dir)

        # required -- pyproject.toml
        t_required = get_required_pyproject_toml(
            d_pyproject_toml,
            path_dir,
            is_bypass=True,
        )
        if (
            t_required is not None
            and isinstance(t_required, Sequence)
            and len(t_required) == 2
        ):
            seq_prepare_these = (t_required[1],)
            prepare_folders_files(seq_prepare_these, path_dir)

    return _method


@pytest.fixture
def path_project_base():
    """Fixture to get project base folder"""

    def _method():
        """Get project base folder."""
        if "__pycache__" in __file__:
            # cached
            path_tests = Path(__file__).parent.parent
        else:
            # not cached
            path_tests = Path(__file__).parent
        path_cwd = path_tests.parent

        return path_cwd

    return _method


@pytest.fixture()
def wd(tmp_path: Path) -> WorkDir:
    """Create a workdir within tmp_path.

    In another fixture, add a package base folder.

    :param tmp_path: Temporary folder
    :type tmp_path: pathlib.Path
    :returns: WorkDir instance
    :rtype: .wd_wrapper.WorkDir

    .. seealso::

       Credit
       `[Author] <https://github.com/pypa/setuptools-scm/blob/main/pyproject.toml>`_
       `[Source] <https://github.com/pypa/setuptools_scm/blob/main/testing/conftest.py>`_
       `[License: MIT] <https://github.com/pypa/setuptools-scm/blob/main/LICENSE>`_

    """
    target_wd = tmp_path.resolve() / "wd"
    target_wd.mkdir()
    return WorkDir(target_wd)


@pytest.fixture
def verify_tag_version():
    """Fixture to verify version file contents."""

    def _method(cwd, sem_ver_str):
        """Verify version file contains a given semantic version str.

        :param cwd: package base folder
        :type cwd: pathlib.Path
        :param sem_ver_str: expected semantic version
        :type sem_ver_str: str
        :returns: True if versions match otherwise False
        :rtype: bool
        """
        cmd = [
            resolve_path("drain-swamp"),
            "tag",
        ]
        t_ret = run_cmd(cmd, cwd=cwd)
        out, err, exit_code, exc = t_ret
        is_eq = out == sem_ver_str

        return is_eq

    return _method
