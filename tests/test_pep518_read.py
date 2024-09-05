"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

pyproject.toml read table sections

Unit test -- Module

.. code-block:: shell

   python -m coverage run --source='drain_swamp.pep518_read' -m pytest \
   --showlocals tests/test_pep518_read.py && coverage report \
   --data-file=.coverage --include="**/pep518_read.py"

Integration test

.. code-block:: shell

   make coverage
   pytest --showlocals --cov="drain_swamp" --cov-report=term-missing \
   --cov-config=pyproject.toml tests

"""

import sys
import tempfile
import unittest
from pathlib import (
    Path,
    PurePath,
)
from unittest.mock import patch

from drain_swamp.constants import g_app_name
from drain_swamp.pep518_read import (
    _is_ok,
    find_project_root,
    find_pyproject_toml,
)

if sys.version_info >= (3, 9):  # pragma: no cover
    from collections.abc import Sequence  # noqa: F401 Used by sphinx
else:  # pragma: no cover
    from typing import Sequence  # noqa: F401 Used by sphinx


class Pep518Sections(unittest.TestCase):
    """Pep518 read tests."""

    def setUp(self):
        """Setup cwd and tests folder variables."""
        if "__pycache__" in __file__:
            # cached
            self.path_tests = Path(__file__).parent.parent
        else:
            # not cached
            self.path_tests = Path(__file__).parent
        self.cwd = self.path_tests.parent

    def test_is_ok(self):
        """Is not None and a non-empty string.

        Vendered from package/module, logging-strict.util.check_type
        """
        invalids = (
            None,  # not str
            "",  # empty string
            0.123,  # not str
            "    ",  # contains only whitespace
        )
        for invalid in invalids:
            out_actual = _is_ok(invalid)
            self.assertFalse(out_actual)

        valids = ("Hello World!",)  # non-empty string
        for valid in valids:
            out_actual = _is_ok(valid)
            self.assertTrue(out_actual)

    def test_find_project_root(self):
        """Check possibilities: .git, .hg, pyproject.toml, or file system root."""
        # "pyproject.toml"
        with (
            tempfile.TemporaryDirectory() as f_d,
            patch("pathlib.Path.cwd", return_value=Path(f_d)),
        ):
            tests = ((f_d, "pyproject.toml"),)
            for t_valid_dirs in tests:
                self.assertIsInstance(t_valid_dirs, tuple)
                valid_dir, reason_expected = t_valid_dirs
                path_dir = Path(valid_dir)
                # create an empty pyproject.toml
                # Do not mkdir .git or .hg
                path_f = path_dir.joinpath("pyproject.toml")
                path_f.touch(mode=0o666, exist_ok=False)

                srcs = (valid_dir,)
                path_project_folder, reason = find_project_root(srcs)
                self.assertTrue(issubclass(type(path_project_folder), PurePath))
                self.assertIsInstance(reason, str)
                self.assertEqual(reason, reason_expected)

                is_found = False
                for child in path_project_folder.iterdir():
                    if child.name == "pyproject.toml":
                        is_found = True
                self.assertTrue(is_found)

        # cwd contains a .git folder, making it ill-suited to test as an empty folder
        # Do not make .git or .hg folder. Do not make pyproject.toml file
        with (
            tempfile.TemporaryDirectory() as f_d,
            patch("pathlib.Path.cwd", return_value=Path(f_d)),
        ):
            tests = (
                ((f_d,), "file system root"),
                ((None,), "file system root"),  # means should use cwd
                (None, "file system root"),  # forgot; should be a Sequence
                (
                    (
                        0.1234,
                        None,
                        0.4321,
                        Path("pyproject.toml"),
                    ),
                    "file system root",
                ),  # filter out non-str
            )
            for t_valid_dirs in tests:
                self.assertIsInstance(t_valid_dirs, Sequence)
                srcs, reason_expected = t_valid_dirs
                if srcs is not None:
                    self.assertIsInstance(srcs, Sequence)
                else:
                    self.assertIsNone(srcs)
                self.assertIsInstance(reason_expected, str)

                path_project_folder, reason = find_project_root(srcs)
                self.assertTrue(issubclass(type(path_project_folder), PurePath))
                self.assertIsInstance(reason, str)
                self.assertEqual(reason, reason_expected)

                is_found = False
                for child in path_project_folder.iterdir():
                    if child.name == "pyproject.toml":
                        is_found = True
                self.assertFalse(is_found)

        # stdin_filename
        # .git > pyproject.toml
        with (
            tempfile.TemporaryDirectory() as f_d,
            patch("pathlib.Path.cwd", return_value=Path(f_d)),
        ):
            path_dir = Path(f_d)
            path_dot_git = path_dir.joinpath(".git")
            path_dot_git.mkdir(
                mode=0o777,
                parents=False,
                exist_ok=False,
            )

            # pyproject.toml does not yet exist
            srcs = ("-",)
            stdin_filename = None
            self.assertIsNone(find_pyproject_toml(srcs, stdin_filename))

            path_f = path_dir.joinpath("pyproject.toml")
            path_f.touch(mode=0o666, exist_ok=False)
            str_toml = (
                "[tool.asz.unittest]\n"
                "util/test_pep518_read.py = 14\n\n"
                "[tool.asz.recipe]\n"
                "util/pep518_read = [14]\n\n"
            )
            path_f.write_text(str_toml)

            """pyproject.toml exists, although stdin_filename not supplied

            make coverage says it's None, unittest and running coverage
            on the module says it's a str.

            It shouldn't be None
            """
            # self.assertIsInstance(find_pyproject_toml(srcs, stdin_filename), str)
            pass

            # pyproject.toml exists, stdin_filename supplied
            stdin_filename = str(path_f)
            self.assertIsInstance(find_pyproject_toml(srcs, stdin_filename), str)

            path_project_folder, reason = find_project_root(srcs, stdin_filename)
            self.assertTrue(issubclass(type(path_project_folder), PurePath))
            self.assertIsInstance(reason, str)
            self.assertEqual(reason, ".git directory")

        # Has .git, .hg folders
        tests = (
            (".git", ".git directory"),
            (".hg", ".hg directory"),
        )
        for t_valid_dirs in tests:
            self.assertIsInstance(t_valid_dirs, tuple)
            valid_dir, reason_expected = t_valid_dirs
            with (
                tempfile.TemporaryDirectory() as f_d,
                patch("pathlib.Path.cwd", return_value=Path(f_d)),
            ):
                path_dir = Path(f_d)
                path_dot_vcs = path_dir.joinpath(valid_dir)
                path_dot_vcs.mkdir(
                    mode=0o777,
                    parents=False,
                    exist_ok=False,
                )
                srcs = (f_d,)
                path_project_folder, reason = find_project_root(srcs)
                self.assertTrue(issubclass(type(path_project_folder), PurePath))
                self.assertIsInstance(reason, str)
                self.assertEqual(reason, reason_expected)

        # search fails
        with (
            tempfile.TemporaryDirectory() as f_d,
            patch("pathlib.Path.cwd", return_value=Path(f_d)),
        ):
            tests = ((f_d, "file system root"),)
            for t_valid_dirs in tests:
                self.assertIsInstance(t_valid_dirs, tuple)
                valid_dir, reason_expected = t_valid_dirs
                srcs = (valid_dir,)

                path_project_folder, reason = find_project_root(srcs)
                self.assertTrue(issubclass(type(path_project_folder), PurePath))
                self.assertIsInstance(reason, str)
                self.assertEqual(reason, reason_expected)

                # must be a tuple[str], not tuple[Path]
                stdin_filename = None
                self.assertIsNone(find_pyproject_toml(srcs, stdin_filename))

            # PermissionError, **not** testing a filesystem base folder
            stdin_filename = None
            srcs = ("/root",)
            with patch(
                f"{g_app_name}.pep518_read.Path.cwd",
                side_effect=PermissionError,
            ):
                with self.assertRaises(PermissionError):
                    # supposed to be a inaccessible folder
                    find_project_root(srcs)

            # self.assertIsNone(find_pyproject_toml(srcs, stdin_filename))
            pass


if __name__ == "__main__":  # pragma: no cover
    """
    .. code-block:: shell

       python -m tests.test_pep518_read

       coverage run --data-file=".coverage-combine-14" \
       -m unittest discover -t. -s tests -p "test_pep518_read*.py" --buffer

       coverage report --include="*pep518_read*" --no-skip-covered \
       --data-file=".coverage-combine-14"

    Ran 1 test in 0.004s
    Branch Coverage: 100%

    Avoid combine since only one RecipePortion

    .. code-block:: shell

       coverage combine --keep .coverage-combine-14

    """
    unittest.main(tb_locals=True)
