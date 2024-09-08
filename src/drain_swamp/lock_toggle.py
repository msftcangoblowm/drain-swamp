"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

Without ``tool.pipenv-unlock.folders``:

   The folders containing .in files is deduced from
   ``[tool.pipenv-unlock]`` ``required`` and ``optionals`` fields. Which contains
   keys: ``target`` and ``relative_path``.

   ``relative_path`` value contains the relative path to a .in file.
   Without dups, use a set, those files' parent folder will contain our .in files.

With ``tool.pipenv-unlock.folders``:

There may be additional folders not implied by required/optionals
(aka ``dependencies`` or ``optional-dependencies``), which contain
``.in`` files.

Example use cases

-  ``ci``
   Used by CI/CD. e.g. mypy.in, tox.in

- ``kit``
  For building tarball and wheels, e.g. kit.in

In which case, there needs to be a way to specify all folders
containing ``.in`` files.

Explicitly specifying all folders is preferred over a derived
(implied) folders list

Example ``pyproject.toml``. specifies an additional folder, ``ci``.

.. code-block:: text

   [tool.pipenv-unlock]
   folders = [
       "docs",
       "requirements",
       "ci",
   ]
   required = { target = "prod", relative_path = "requirements/prod.in" }
   optionals = [
       { target = "pip", relative_path = "requirements/pip.in" },
       { target = "pip_tools", relative_path = "requirements/pip-tools.in" },
       { target = "dev", relative_path = "requirements/dev.in" },
       { target = "manage", relative_path = "requirements/manage.in" },
       { target = "docs", relative_path = "docs/requirements.in" },
   ]

.. py:data:: __all__
   :type: tuple[str, str, str]
   :value: ("lock_compile", "refresh_links", "unlock_compile")

   Module exports

.. py:data:: _logger
   :type: logging.Logger

   Module level logger

.. py:data:: is_module_debug
   :type: bool
   :value: False

   on/off for module level logging

"""

from __future__ import annotations

import abc
import copy
import dataclasses
import enum
import fileinput
import logging
import os
import pathlib
import shutil
import sys
from collections.abc import Sequence
from pathlib import (
    Path,
    PurePath,
)

from ._package_installed import is_package_installed
from ._run_cmd import run_cmd
from ._safe_path import (
    is_win,
    resolve_joinpath,
    resolve_path,
)
from .constants import (
    SUFFIX_LOCKED,
    SUFFIX_SYMLINK,
    SUFFIX_UNLOCKED,
    g_app_name,
)
from .exceptions import MissingRequirementsFoldersFiles

__package__ = "drain_swamp"
__all__ = (
    "lock_compile",
    "refresh_links",
    "unlock_compile",
)

_logger = logging.getLogger(f"{g_app_name}.lock_toggle")
is_module_debug = False


class DependencyLockLnkFile(abc.ABC):
    """ABC for creating .lnk files."""

    @classmethod
    @abc.abstractmethod
    def is_file(cls, abspath) -> bool:
        """Encapsulate positive file type check implementation.

        :param abspath: Absolute path to a file or folder
        :type abspath: pathlib.Path | pathlib.PurePath
        :returns: True if an existing file
        :rtype: bool
        """
        ...

    @classmethod
    @abc.abstractmethod
    def is_not_file(cls, abspath) -> bool:
        """Encapsulate file type check implementation.

        :param abspath: Absolute path to a file or folder
        :type abspath: pathlib.Path | pathlib.PurePath
        :returns:

           True if not a .lnk file of the type appropriate for the
           platform implementation

        :rtype: bool
        """

    @staticmethod
    @abc.abstractmethod
    def is_support() -> bool:
        """The platform the implementation should use.

        :returns: True if implementation applies to current platform
        :rtype: bool
        """
        ...

    def _shared_checks(self, src, dest, cwd_path):
        """Boilerplate normally done by a constructor

        :param src: relative path to source file
        :type src: str
        :param dest: relative path to what will be the symlink
        :type dest: str
        :param cwd_path: Absolute path a folder
        :type cwd_path: str

        :raises:

           - :py:exc:`NotADirectoryError` -- Directory not found or not a directory
           - :py:exc:`FileNotFoundError` -- Source file not found
           - :py:exc:`ValueError` -- destination symlink must suffix must be .lnk
           - :py:exc:`OSError` -- opening file descriptor on folder permission denied

        """
        mod_path = f"{g_app_name}.lock_toggle.DependencyLockLnkFile._shared_checks"

        path_cwd = Path(cwd_path)

        # e.g. src requirements/dev.lock or requirements\\dev.lock
        path_src = resolve_joinpath(path_cwd, src)

        # e.g. {tmp_path}/requirements or {tmp_path}\\requirements
        path_parent = path_src.parent

        # e.g. dev.lock
        src_name = path_src.name
        # e.g. dev.lnk
        dest_name = Path(dest).name
        # e.g. {tmp_path}\\requirements\\dev.lock
        path_parent_src = path_parent.joinpath(src_name)
        # e.g. {tmp_path}\\requirements\\dev.lnk
        path_parent_dest = path_parent.joinpath(dest_name)

        is_not_exists = not path_cwd.exists()

        # base folder, not including subfolders
        is_dir_bad = is_not_exists or (path_cwd.exists() and not path_cwd.is_dir())
        if is_dir_bad:
            msg_exc = "Expecting folder to already exist"
            raise NotADirectoryError(msg_exc)

        is_not_src = not path_parent_src.exists()
        if is_not_src:
            msg_exc = f"Source file not found: {src} folder: {path_cwd}"
            raise FileNotFoundError(msg_exc)

        # Assert dest suffixes indicate it's a .lnk file
        if path_parent_dest.suffixes != [
            SUFFIX_SYMLINK,
        ]:
            msg_exc = "Destination symlink must suffix must be .lnk"
            raise ValueError(msg_exc)

        # All implementations
        self._path_parent_dest = path_parent_dest

        # For symlink implementation
        self._dir = str(path_parent)
        self._src_name = src_name
        self._dest_name = dest_name

        # For copy implementation
        self._path_parent_src = path_parent_src

        # Folder permissions
        is_readable = os.access(self._dir, os.R_OK)
        is_writable = os.access(self._dir, os.W_OK)
        if is_module_debug:  # pragma: no cover
            msg_info = f"{mod_path} {self._dir} readable?: {is_readable}"
            print(msg_info, file=sys.stderr)
            msg_info = f"{mod_path} {self._dir} writable?: {is_writable}"
            print(msg_info, file=sys.stderr)
        else:  # pragma: no cover
            pass

    @abc.abstractmethod
    def __call__(self, src, dest, cwd_path):
        """Create a file copy. Either an actual copy or a symlink

        :param src: relative path to source file
        :type src: str
        :param dest: relative path to what will be the symlink
        :type dest: str
        :param cwd_path: Absolute path a folder
        :type cwd_path: str
        """
        ...


class DependencyLockSymlink(DependencyLockLnkFile):
    """Dependency lock files are symlinks.

    .. py:attribute:: IMPLEMENTATION
       :type: str
       :value: "os.symlink"

       What to patch

    """

    IMPLEMENTATION = "os.symlink"

    @classmethod
    def is_file(cls, abspath) -> bool:  # pragma: no cover
        """Encapsulate positive file/symlink check implementation.

        .. note:: Could become a file

           When Python builds a sdist package, symlinks are resolved;
           symlinks --> files. :py:meth:`pathlib.Path.is_symlink`
           is insufficient. Also check for :py:meth:`pathlib.Path.is_file`

        :param abspath: Absolute path to a file or folder
        :type abspath: pathlib.Path | pathlib.PurePath
        :returns: True if an existing file
        :rtype: bool
        """
        path_f = Path(abspath)
        ret = path_f.exists() and (path_f.is_symlink() or path_f.is_file())

        return ret

    @classmethod
    def is_not_file(cls, abspath) -> bool:  # pragma: no cover
        """Encapsulate file type check implementation.

        :param abspath: Absolute path to a file or folder
        :type abspath: pathlib.Path | pathlib.PurePath
        :returns: True if not a symlink
        :rtype: bool
        """
        path_f = Path(abspath)
        is_not_exists = not path_f.exists()
        is_bad = is_not_exists or (
            path_f.exists() and not path_f.is_symlink() and not path_f.is_file()
        )
        return is_bad

    @staticmethod
    def is_support() -> bool:
        """Platform that implements symlinks with minimal trouble.

        :returns: True if implementation applies to current platform
        :rtype: bool
        """
        ret = not is_win()

        return ret

    def __call__(self, src: str, dest: str, cwd_path: str) -> None:  # pragma: no cover
        """Create a copy by symlink.

        :param src: relative path to source file
        :type src: str
        :param dest: relative path to what will be the symlink
        :type dest: str
        :param cwd_path: Absolute path a folder
        :type cwd_path: str

        :raises:

           - :py:exc:`NotADirectoryError` -- Directory not found or not a directory
           - :py:exc:`FileNotFoundError` -- Source file not found
           - :py:exc:`ValueError` -- destination symlink must suffix must be .lnk
           - :py:exc:`OSError` -- opening file descriptor on folder permission denied

        """
        cls = type(self)
        mod_path = f"{g_app_name}.lock_toggle.{cls.__name__}.__call__"
        # Raises: NotADirectoryError FileNotFoundError ValueError
        self._shared_checks(src, dest, cwd_path)

        if is_module_debug:  # pragma: no cover

            _logger.info(f"{mod_path} parent {self._dir!r}")
            _logger.info(f"{mod_path} src name {self._src_name!r}")
            _logger.info(f"{mod_path} dest name {self._dest_name!r}")
        else:  # pragma: no cover
            pass

        # Remove dest symlink, if it exists
        if cls.is_file(self._path_parent_dest):  # pragma: no cover
            self._path_parent_dest.unlink(missing_ok=True)
        else:  # pragma: no cover
            pass

        """:py:func:`os.symlink` on problematic platforms should
        raise NotImplementedError but doesn't."""
        try:
            dir_fd = os.open(self._dir, os.O_RDONLY)
            #    Create relative symlink
            os.symlink(self._src_name, self._dest_name, dir_fd=dir_fd)
            #    Don't leak a file descriptor
            os.close(dir_fd)
        except OSError as exc:
            msg_warn = (
                f"{mod_path} {str(exc)} folder {self._dir!r} src name "
                f"{self._src_name!r} dest name {self._dest_name!r} "
                f"is dest({self._path_parent_dest!r}): "
                f"{cls.is_file(self._path_parent_dest)} "
                f"is src({self._path_parent_src!r}): "
                f"{cls.is_file(self._path_parent_src)}"
            )

            raise OSError(msg_warn) from exc


class DependencyLockFile(DependencyLockLnkFile):
    """Dependency lock files are files.

    .. py:attribute:: IMPLEMENTATION
       :type: str
       :value: "shutil.copy2"

       What to patch

    """

    IMPLEMENTATION = "shutil.copy2"

    @classmethod
    def is_file(cls, abspath) -> bool:  # pragma: no cover
        """Encapsulate positive file type check implementation.

        :param abspath: Absolute path to a file or folder
        :type abspath: pathlib.Path | pathlib.PurePath
        :returns: True if an existing file
        :rtype: bool
        """
        path_f = Path(abspath)
        ret = path_f.exists() and path_f.is_file()

        return ret

    @classmethod
    def is_not_file(cls, abspath) -> bool:  # pragma: no cover
        """Encapsulate negative file type check implementation.

        :param abspath: Absolute path to a file or folder
        :type abspath: pathlib.Path | pathlib.PurePath
        :returns: True if not a file
        :rtype: bool
        """
        path_f = Path(abspath)
        is_not_exists = not path_f.exists()
        is_bad = is_not_exists or (path_f.exists() and not path_f.is_file())
        return is_bad

    @staticmethod
    def is_support() -> bool:
        """Platform that doesn't implement symlinks with minimal trouble.

        :returns: True if implementation applies to current platform
        :rtype: bool
        """
        ret = is_win()

        return ret

    def __call__(self, src: str, dest: str, cwd_path: str) -> None:  # pragma: no cover
        """Create a copy by symlink.

        :param src: relative path to source file
        :type src: str
        :param dest: relative path to what will be the symlink
        :type dest: str
        :param cwd_path: Absolute path a folder
        :type cwd_path: str

        :raises:

           - :py:exc:`NotADirectoryError` -- Directory not found or not a directory
           - :py:exc:`FileNotFoundError` -- Source file not found
           - :py:exc:`ValueError` -- destination symlink must suffix must be .lnk
           - :py:exc:`OSError` -- opening file descriptor on folder permission denied

        """
        cls = type(self)
        # Raises: NotADirectoryError FileNotFoundError ValueError
        self._shared_checks(src, dest, cwd_path)

        # Remove dest file, if it exists
        if cls.is_file(self._path_parent_dest):  # pragma: no cover
            self._path_parent_dest.unlink(missing_ok=True)
        else:  # pragma: no cover
            pass

        try:
            shutil.copy2(
                self._path_parent_src,
                self._path_parent_dest,
                follow_symlinks=False,
            )
        except OSError:
            raise


class DependencyLockLnkFactory:
    """Supported implementation chooser."""

    @staticmethod
    def get_supported() -> type[DependencyLockLnkFile]:
        """Get the supported implementation class

        :returns: Supported implementation class
        :rtype: type[drain_swamp.lock_toggle.DependencyLockLnkFile]
        """
        # These implementations are hardcoded
        _impl_klasses = (DependencyLockSymlink, DependencyLockFile)
        cls_impls = [cls_impl for cls_impl in _impl_klasses if cls_impl.is_support()]
        impl = cls_impls[0]

        return impl

    def __call__(self, src: str, dest: str, cwd_path: str) -> None:
        """Call the supported DependencyLockLnkFile subclass.

        :param src: relative path to source file
        :type src: str
        :param dest: relative path to what will be the symlink
        :type dest: str
        :param cwd_path: Absolute path a folder
        :type cwd_path: str
        :raises:

           - :py:exc:`NotADirectoryError` -- Directory not found or not a directory
           - :py:exc:`FileNotFoundError` -- Source file not found
           - :py:exc:`ValueError` -- destination symlink must suffix must be .lnk
           - :py:exc:`OSError` -- opening file descriptor on folder permission denied

        .. todo:: Dynamically get implementations

           Troublesome, but possible, to get subclasses of DependencyLockLnkFile

        """
        cls = type(self)
        impl = cls.get_supported()
        impl()(src, dest, cwd_path)


def _maintain_symlink(path_cwd, abspath_src):
    """Create/Update symlink which indicates current state file

    ``%.lnk`` --> [``%.unlock`` | ``%.lock`]

    Symlink path must be relative, not absolute to the machine base folder
    :param path_cwd:

       folder containing the src file. Relative to the package or a requirements folder

    :type path_cwd: pathlib.Path
    :param abspath_src: Absolute path to the source file. With suffix .unlock or .lock
    :type abspath_src: pathlib.Path
    :raises:

       - :py:exc:`NotADirectoryError` -- Directory not found or not a directory
       - :py:exc:`FileNotFoundError` -- Source file not found
       - :py:exc:`NotImplementedError` -- os.symlink not supported on this platform

    :meta private:
    """
    mod_path = f"{g_app_name}.lock_toggle._maintain_symlink"
    msg_warn_create_relative_symlink = (
        "{mod_path} {exc} relative path lock/unlock file: {src!r} "
        "symlink file name: {dest!r} cwd: {path_cwd!r}"
    )
    is_dir_bad = not path_cwd.exists() or (path_cwd.exists() and not path_cwd.is_dir())
    if is_dir_bad:
        msg_exc = "Expecting folder to already exist"
        raise NotADirectoryError(msg_exc)

    is_not_src = not abspath_src.exists()
    if is_not_src:
        msg_exc = f"Source file not found: {abspath_src} folder: {path_cwd}"
        raise FileNotFoundError(msg_exc)

    relpath_src = abspath_src.relative_to(path_cwd)
    src = str(relpath_src)

    # dest suffix is .lnk, so ValueError impossible
    src_stem = abspath_src.stem
    dest = f"{src_stem}{SUFFIX_SYMLINK}"

    try:
        # Chooses supported implementation
        DependencyLockLnkFactory()(src, dest, str(path_cwd))
    except Exception as e:  # pragma: no cover
        d_kwargs = {
            "mod_path": mod_path,
            "exc": str(e),
            "src": relpath_src,
            "dest": dest,
            "path_cwd": path_cwd,
        }
        msg_warn = msg_warn_create_relative_symlink.format(**d_kwargs)
        _logger.warning(msg_warn)
        raise


def _postprocess_abspath_to_relpath(path_out, path_parent):
    """Within a lock file (contents), if an absolute path make relative
    by removing parent path

    To see the lock file format

    .. code-block:: shell

       pip-compile --dry-run docs/requirements.in

    :param path_out: Absolute path of the requirements file
    :type path_out: pathlib.Path
    :param path_parent: Absolute path to the parent folder of the requirements file
    :type path_parent: pathlib.Path
    """
    files = (path_out,)
    # py310 encoding="utf-8"
    with fileinput.input(files, inplace=True) as f:
        for line in f:
            is_lock_requirement_line = line.startswith("    # ")
            if is_lock_requirement_line:
                # process line
                line_modified = line.replace(f"{path_parent!s}/", "")
                sys.stdout.write(line_modified)
            else:  # pragma: no cover
                # do not modify line
                sys.stdout.write(line)


def lock_compile(inst):
    """In a subprocess, call :command:`pip-compile` to create ``.lock`` files

    :param inst:

       Backend subclass instance which has folders property containing
       ``collections.abc.Sequence[Path]``

    :type inst: drain_swamp.backend_abc.BackendType
    :returns: Generator of abs path to ``.lock`` files
    :rtype: collections.abc.Generator[pathlib.Path, None, None]
    :raises:

       - :py:exc:`AssertionError` -- pip-tools is not installed and is
         a dependency of this package

    """
    str_func_name = f"{g_app_name}.lock_toggle.lock_compile"
    assert is_package_installed("pip-tools") is True

    # store pairs
    lst_pairs = []
    t_excludes = ("pins.in",)

    # Look at the folders. Then convert all ``.in`` --> ``.lock``
    gen_unlocked_files = inst.in_files()

    in_files = list(gen_unlocked_files)
    del gen_unlocked_files

    if is_module_debug:  # pragma: no cover
        msg_info = f"{str_func_name} in_files: {in_files}"
        _logger.info(msg_info)
    else:  # pragma: no cover
        pass

    gen_unlocked_files = inst.in_files()
    for path_abs in gen_unlocked_files:
        if path_abs.name not in t_excludes:
            file_name = f"{path_abs.stem}{SUFFIX_LOCKED}"
            abspath_locked = path_abs.parent.joinpath(file_name)
            lst_pairs.append((str(path_abs), str(abspath_locked)))
        else:  # pragma: no cover
            # Not a ``*.in`` file. Ignore
            pass

    if is_module_debug:  # pragma: no cover
        msg_info = f"{str_func_name} pairs: {lst_pairs}"
        _logger.info(msg_info)
    else:  # pragma: no cover
        pass

    # Serial it's whats for breakfast
    for in_path, out_path in lst_pairs:
        # str(PATH_PIP_COMPILE),
        cmd = (
            resolve_path("pip-compile"),
            "--allow-unsafe",
            "--resolver",
            "backtracking",
            "-o",
            out_path,
            in_path,
        )

        if is_module_debug:  # pragma: no cover
            msg_info = f"{str_func_name} cmd: {cmd}"
            _logger.info(msg_info)
        else:  # pragma: no cover
            pass

        t_ret = run_cmd(cmd, cwd=inst.parent_dir)
        _, err, exit_code, exc = t_ret

        if exit_code != 0:  # pragma: no cover
            msg_info = f"{str_func_name} pip-compile exit code {exit_code} {err} {exc}"
            _logger.warning(msg_info)
        else:  # pragma: no cover
            pass

        path_out = Path(out_path)
        is_confirm = path_out.exists() and path_out.is_file()
        if is_confirm:
            if is_module_debug:  # pragma: no cover
                msg_info = f"{str_func_name} yield: {out_path!s}"
                _logger.info(msg_info)
            else:  # pragma: no cover
                pass

            # post processing
            _postprocess_abspath_to_relpath(path_out, inst.parent_dir)

            yield path_out
        else:
            # File not created. Darn you pip-compile!
            if is_module_debug:  # pragma: no cover
                msg_info = f"{str_func_name} pip-compile did not create: {out_path}"
                _logger.warning(msg_info)
            else:  # pragma: no cover
                pass
            yield from ()

    yield from ()


def strip_inline_comments(val):
    """Strip off inline comments. Which may be to the right of a requirement

    :param val: line with contains a requirement and optionally an in-line comment
    :type val: str
    :returns: Requirement without a inline comment
    :rtype: str
    """
    try:
        pos = val.index("#")
    except ValueError:
        # not found
        ret = val
    else:
        ret = val[:pos]
        ret = ret.rstrip()

    return ret


@dataclasses.dataclass
class InFile:
    """
    :ivar relpath: Relative path to requirements file
    :vartype relpath: str
    :ivar stem:

       Requirements file stem. Later, appends suffix ``.unlock``

    :vartype stem: str
    :ivar constraints:

       Requirement files may contain lines starting with
       ``-c [requirements file relative path]``. This constitutes a
       constraint. The requirements file referenced by a constraint, can
       also contain constraints. The tree of constraints is resolved
       recursively until all constraints on all requirements files are resolved.

    :vartype constraints: set[str]
    :ivar requirements:

       Contains all dependencies from a requirements file. There is no
       attempt made to resolve package versions.

    :vartype requirements: set[str]
    """

    relpath: str
    stem: str
    constraints: set[str] = dataclasses.field(default_factory=set)
    requirements: set[str] = dataclasses.field(default_factory=set)

    def __post_init__(self):
        """relpath given as a Path, convert into a str.
        :py:func:`drain_swamp.lock_toggle.InFile.check_path` should
        have already been performed/called prior
        """
        is_path = issubclass(type(self.relpath), PurePath)
        if is_path:
            self.relpath = str(self.relpath)
        else:  # pragma: no cover
            pass

    @staticmethod
    def check_path(cwd, path_to_check):
        """Check Path. Should not be a str

        :param cwd: Package base folder
        :type cwd: pathlib.Path
        :param path_to_check: Hopefully a relative Path
        :type path_to_check: typing.Any
        :raises:

           - :py:exc:`TypeError` -- Sequence contains one or more unsupported types
           - :py:exc:`ValueError` -- Requirements file, (.in), not relative to base folder
           - :py:exc:`FileNotFoundError` -- Requirements file, (.in), not found

        """
        # contains only Path
        is_path = path_to_check is not None and issubclass(
            type(path_to_check), PurePath
        )
        if not is_path:
            msg_exc = (
                f"in_files Sequence contains unsupported type, {type(path_to_check)}"
            )
            raise TypeError(msg_exc)
        else:  # pragma: no cover
            pass

        # FileNotFoundError
        is_abs_path = path_to_check.is_absolute() and path_to_check.is_file()
        if not is_abs_path:
            msg_exc = "Requirement (.in) file does not exist"
            raise FileNotFoundError(msg_exc)

        # relative to self.cwd
        try:
            path_to_check.relative_to(cwd)
        except Exception as e:
            msg_exc = (
                f"requirements file, {path_to_check}, not relative to folder, {cwd}"
            )
            raise ValueError(msg_exc) from e

    def abspath(self, path_package_base):
        """Get the absolute path. The relative path is relative to the
        package folder.

        :param path_package_base: package base folder
        :type path_package_base: pathlib.Path
        :returns: absolute path
        :rtype: pathlib.Path
        """
        return path_package_base.joinpath(self.relpath)

    @property
    def depth(self):
        """Number of unresolved constraints. One this number gets down
        to zero, the InFile is moved from files set --> zeroes set

        :returns: unresolved constraints count
        :rtype: int
        """
        return len(self.constraints)

    def resolve(self, constraint, requirements):
        """
        :param constraint: A ``.in`` file relative path
        :type constraint: str
        :param requirements:

           The ``.in`` file's requirement lines, which might have silly
           version upper limits. No attempt is made to address these
           upper bounds version limits

        :type requirements: set[str]
        """
        self.constraints.remove(constraint)

        # Removes duplicates, but ignores version constraints
        for req in requirements:
            self.requirements.add(req)

    def __hash__(self):
        """Constraints as constraints are resolved, are removed,
        increasing the requirements.

        Both fields are dynamic. For the point of identification,
        the relpath is unique

        :returns: hash of relpath
        :rtype: int
        """
        return hash((self.relpath,))

    def __eq__(self, right):
        """Compares equality

        :param right: right side of the equal comparison
        :type right: typing.Any
        :returns:

           True if both are same InFile otherwise False. Does not take
           in account, constraints and requirements.

        :rtype: bool
        """
        is_infile = isinstance(right, InFile)
        is_str = isinstance(right, str)
        is_relpath = issubclass(type(right), PurePath) and not right.is_absolute()
        if is_relpath:
            str_right = str(right)
        elif is_str:
            str_right = right
        else:  # pragma: no cover
            pass

        if is_infile:
            is_eq = self.__hash__() == right.__hash__()
            ret = is_eq
        elif is_str or is_relpath:
            # relpath
            left_hash = hash(self)
            right_hash = hash((str_right,))
            is_eq = left_hash == right_hash
            ret = is_eq
        else:
            ret = False

        return ret


class InFileType(enum.Enum):
    """Each .in files constaints and requirements have to be resolved.
    This occurs recursively. Once resolved, InFile is moved from FILES --> ZEROES set

    .. py:attribute:: FILES
       :value: "_files"

       .in file that has unresolved -c (constraints) and -r (requirements)

    .. py:attribute:: ZEROES
       :value: "_zeroes"

       .in file that have all -c (constraints) and -r (requirements) resolved

    """

    FILES = "_files"
    ZEROES = "_zeroes"

    def __str__(self):
        """Resolve to the InFiles set's name

        :returns: InFiles set's name
        :rtype: str
        """
        return f"{self.value}"

    def __eq__(self, other):
        """Equality check

        :param other: Should be same Enum class
        :type other: typing.Any
        :returns: True if equal otherwise False
        :rtype: bool
        """
        return self.__class__ is other.__class__ and other.value == self.value


@dataclasses.dataclass
class InFiles:
    """Container of InFile

    :ivar cwd: current working directory
    :vartype cwd: pathlib.Path
    :ivar in_files: Requirements files. Relative path to ``.in`` files
    :vartype in_files: collections.abc.Sequence[pathlib.Path]
    :ivar _files:

       Set of InFile. Which contains the relative path to a Requirement
       file. May contain unresolved constraints

    :vartype _files: set[InFile]
    :ivar _zeroes: Set of InFile that have all constraints resolved
    :vartype _zeroes: set[InFile]

    :raises:

       - :py:exc:`TypeError` -- in_files unsupported type, expecting
         ``Sequence[Path]``

       - :py:exc:`ValueError` -- An element within in_files is not
         relative to folder, cwd

       - :py:exc:`FileNotFoundError` -- Requirements .in file not found

       - :py:exc:`drain_swamp.exceptions.MissingRequirementsFoldersFiles` --
         A requirements file references a nonexistent constraint

    """

    cwd: pathlib.Path
    in_files: dataclasses.InitVar[Sequence[pathlib.Path]]
    _files: set[InFile] = dataclasses.field(init=False, default_factory=set)
    _zeroes: set[InFile] = dataclasses.field(init=False, default_factory=set)

    def __post_init__(self, in_files):
        """Read in and initial pass over ``.in`` files

        :param in_files: Requirements files. Relative path to ``.in`` files
        :type in_files: collections.abc.Sequence[pathlib.Path]
        """
        cls = type(self)
        # is a sequence
        if in_files is None or not isinstance(in_files, Sequence):
            msg_exc = f"Expecting a list[Path] got unsupported type {in_files}"
            raise TypeError(msg_exc)

        # Checks
        for path_abs in in_files:
            try:
                InFile.check_path(self.cwd, path_abs)
            except (TypeError, ValueError, FileNotFoundError):
                raise

        for path_abs in in_files:
            path_relpath = path_abs.relative_to(self.cwd)
            str_file = path_abs.read_text()
            lines = str_file.split("\n")
            constraint_raw = []
            requirement = set()
            for line in lines:
                if cls.line_comment_or_blank(line):
                    continue
                elif cls.is_requirement_or_constraint(line):
                    # -r or -c are treated as equivalents
                    line_pkg = line[3:]
                    line_pkg = strip_inline_comments(line_pkg)
                    constraint_raw.append(line_pkg)
                else:
                    """unknown pip file options, will be considered a requirement"""
                    line_pkg = strip_inline_comments(line)
                    requirement.add(line_pkg)

            """Normalize constraint
            Assume .in files constraints are relative path only
            """
            path_parent = path_abs.parent
            constraint = set()
            for cons_path in constraint_raw:
                try:
                    path_abs_constraint = path_parent.joinpath(cons_path).resolve(
                        strict=True
                    )
                except FileNotFoundError as exc:
                    msg_exc = (
                        f"Within requirements file, {path_relpath}, a constraint "
                        f"file does not exist. Create it! {cons_path}"
                    )
                    raise MissingRequirementsFoldersFiles(msg_exc) from exc
                else:
                    path_rel_constraint = path_abs_constraint.relative_to(self.cwd)
                    constraint.add(str(path_rel_constraint))

            # Checks already performed for: TypeError, ValueError or FileNotFoundError
            in_ = InFile(
                relpath=path_relpath,
                stem=path_abs.stem,
                constraints=constraint,
                requirements=requirement,
            )
            if is_module_debug:  # pragma: no cover
                msg_info = f"in_: {repr(in_)}"
                _logger.info(msg_info)
            else:  # pragma: no cover
                pass
            # set.add an InFile
            self.files = in_

    @staticmethod
    def line_comment_or_blank(line):
        """Comments or blank lines can be safely ignored

        :param line: .in file line to check if inconsequential
        :type line: str
        :returns: True if a line which can be safely ignored otherwise False
        :rtype: bool
        """
        is_comment = line.startswith("#")
        is_blank_line = len(line.strip()) == 0
        return is_comment or is_blank_line

    @staticmethod
    def is_requirement_or_constraint(line):
        """Line identify if a requirement (-r) or constraint (-c)

        :param line: .in file line is a file which should be included
        :type line: str
        :returns: True if a line needs to be included otherwise False
        :rtype: bool
        """
        return line.startswith("-c ") or line.startswith("-r ")

    @property
    def files(self):
        """Generator of InFile

        :returns: Yields InFile. These tend to contain constraints
        :rtype: collections.abc.Generator[drain_swamp.lock_toggle.InFile, None, None]
        """
        yield from self._files

    @files.setter
    def files(self, val):
        """append an InFile

        The constructor performs checks. Not intended to add requirements
        files outside of the constructor

        :param val: Supposed to be an :py:class:`~drain_swamp.lock_toggle.InFile`
        :type val: typing.Any
        """
        is_infile = val is not None and isinstance(val, InFile)
        if is_infile:
            self._files.add(val)
        else:  # pragma: no cover
            pass

    @property
    def zeroes(self):
        """Generator of InFile

        :returns: Yields InFile without any constraints
        :rtype: collections.abc.Generator[drain_swamp.lock_toggle.InFile, None, None]
        """
        yield from self._zeroes

    @zeroes.setter
    def zeroes(self, val):
        """append an InFile that doesn't have any constraints

        The only acceptable source of zeroes is from :code:`self._files`

        :param val: Supposed to be an :py:class:`~drain_swamp.lock_toggle.InFile`
        :type val: typing.Any
        """
        is_infile = val is not None and isinstance(val, InFile)
        if is_infile:
            self._zeroes.add(val)
        else:  # pragma: no cover
            pass

    def in_generic(self, val, set_name=InFileType.FILES):
        """A generic __contains__

        :param val: item to check if within zeroes
        :type val: typing.Any
        :param set_name:

           Default :py:attr:`drain_swamp.lock_toggle.InFileType.FILES`.
           Which set to search thru. zeroes or files

        :type set_name: drain_swamp.lock_toggle.InFileType | None
        :returns: True if InFile contained within zeroes otherwise False
        :rtype: bool
        """
        if set_name is None or not isinstance(set_name, InFileType):
            str_set_name = str(InFileType.FILES)
        else:  # pragma: no cover
            str_set_name = str(set_name)

        if is_module_debug:  # pragma: no cover
            msg_info = f"InFiles.in_generic InFile set name {str_set_name}"
            _logger.info(msg_info)
        else:  # pragma: no cover
            pass

        ret = False
        set_ = getattr(self, str_set_name, set())
        for in_ in set_:
            if val is not None:
                is_match_infile = isinstance(val, InFile) and in_ == val
                is_match_str = isinstance(val, str) and in_.relpath == val

                is_match_path = issubclass(type(val), PurePath) and in_.relpath == str(
                    val
                )
                if is_match_infile or is_match_str or is_match_path:
                    ret = True
                else:  # pragma: no cover
                    # unsupported type
                    pass
            else:  # pragma: no cover
                # is None
                pass

        return ret

    def in_zeroes(self, val):
        """Check if within zeroes

        :param val: item to check if within zeroes
        :type val: typing.Any
        :returns: True if InFile contained within zeroes otherwise False
        :rtype: bool
        """

        return self.in_generic(val, set_name=InFileType.ZEROES)

    def __contains__(self, val):
        """Check if within InFiles

        :param val: item to check if within InFiles
        :type val: typing.Any
        :returns: True if InFile contained within InFiles otherwise False
        :rtype: bool
        """
        return self.in_generic(val)

    def get_by_relpath(self, relpath, set_name=InFileType.FILES):
        """Get the index and :py:class:`~drain_swamp.lock_toggle.InFile`

        :param relpath: relative path of a ``.in`` file
        :type relpath: str
        :param set_name:

           Default :py:attr:`drain_swamp.lock_toggle.InFileType.FILES`.
           Which set to search thru. zeroes or files.

        :type set_name: str | None
        :returns:

           The ``.in`` file and index within
           :py:class:`~drain_swamp.lock_toggle.InFiles`

        :rtype: drain_swamp.lock_toggle.InFile | None
        :raises:

            - :py:exc:`ValueError` -- Unsupported type. relpath is neither str nor Path

        """
        if set_name is None or not isinstance(set_name, InFileType):
            str_set_name = str(InFileType.FILES)
        else:  # pragma: no cover
            str_set_name = str(set_name)

        msg_exc = f"Expected a relative path as str or Path. Got {type(relpath)}"
        str_relpath = None
        if relpath is not None:
            if isinstance(relpath, str):
                str_relpath = relpath
            elif issubclass(type(relpath), PurePath):
                str_relpath = str(relpath)
            else:
                raise ValueError(msg_exc)
        else:
            raise ValueError(msg_exc)

        ret = None
        set_ = getattr(self, str_set_name, set())
        for in_ in set_:
            if in_.relpath == str_relpath:
                ret = in_
                break
            else:  # pragma: no cover
                # not a match
                pass
        else:
            # set empty
            ret = None

        return ret

    def move_zeroes(self):
        """Zeroes have had all their constraints resolved and therefore
        do not need to be further scrutinized.
        """
        # add to self.zeroes
        del_these = []
        for in_ in self.files:
            if in_.depth == 0:
                # set.add an InFile
                self.zeroes = in_
                del_these.append(in_)
            else:  # pragma: no cover
                pass

        if is_module_debug:  # pragma: no cover
            msg_info = f"self.zeroes (after): {self._zeroes}"
            _logger.info(msg_info)
        else:  # pragma: no cover
            pass

        # remove from self._files
        for in_ in del_these:
            self._files.remove(in_)

        if is_module_debug:  # pragma: no cover
            msg_info = f"self.files (after): {self._files}"
            _logger.info(msg_info)
        else:  # pragma: no cover
            pass

    def resolve_zeroes(self):
        """If a requirements file have constraint(s) that can be
        resolved, by a zero, do so.

        _files and _zeroes are both type, set. Modifying an element
        modifies element within the set
        """
        # Take the win, early and often!
        self.move_zeroes()

        # Resolve with zeroes
        for in_ in self.files:
            constaints_copy = copy.deepcopy(in_.constraints)
            for constraint_relpath in constaints_copy:
                is_in_zeroes = self.in_zeroes(constraint_relpath)

                if is_module_debug:  # pragma: no cover
                    msg_info = (
                        f"resolve_zeroes constraint {constraint_relpath} in "
                        f"zeroes {is_in_zeroes}"
                    )
                    _logger.info(msg_info)
                else:  # pragma: no cover
                    pass

                if is_in_zeroes:
                    # Raises ValueError if constraint_relpath is neither str nor Path
                    item = self.get_by_relpath(
                        constraint_relpath, set_name=InFileType.ZEROES
                    )

                    if is_module_debug:  # pragma: no cover
                        msg_info = f"resolve_zeroes in_ (before) {in_}"
                        _logger.info(msg_info)
                    else:  # pragma: no cover
                        pass

                    in_.resolve(constraint_relpath, item.requirements)

                    if is_module_debug:  # pragma: no cover
                        msg_info = f"resolve_zeroes in_ (after) {in_}"
                        _logger.info(msg_info)
                    else:  # pragma: no cover
                        pass
                else:  # pragma: no cover
                    pass

        # For an InFile, are all it's constraints resolved?
        self.move_zeroes()

    def resolution_loop(self):
        """Run loop of resolve_zeroes calls, sampling before and after
        counts. If not fully resolved and two iterations have the same
        result, raise an Exception

        :raises:

           - :py:exc:`drain_swamp.exceptions.MissingRequirementsFoldersFiles` --
             there are unresolvable constraint(s)

        """
        initial_count = len(list(self.files))
        current_count = initial_count
        previous_count = initial_count
        while current_count != 0:
            self.resolve_zeroes()
            current_count = len(list(self.files))
            # Check previous run results vs current run results, if same raise Exception
            is_resolved = current_count == 0
            is_same_result = previous_count == current_count

            # raise exception if not making any progress
            if not is_resolved and is_same_result:
                unresolvable_requirement_files = [in_.relpath for in_ in self.files]
                missing_contraints = [in_.constraints for in_ in self.files]
                msg_exc = (
                    "Missing .in requirements file(s). Unable to resolve "
                    "constraint(s). Files with unresolvable constraints: "
                    f"{unresolvable_requirement_files}. "
                    f"Missing constraints: {missing_contraints}"
                )
                _logger.info(msg_exc)
                raise MissingRequirementsFoldersFiles(msg_exc)
            else:  # pragma: no cover
                pass

            previous_count = current_count

    def write(self):
        """After resolving all constraints. Write out all .unlock files

        :returns: Generator of ``.unlock`` absolute paths
        :rtype: collections.abc.Generator[pathlib.Path, None, None]
        """
        if is_module_debug:  # pragma: no cover
            msg_info = f"InFiles.write zeroes count: {len(list(self.zeroes))}"
            _logger.info(msg_info)
        else:  # pragma: no cover
            pass

        for in_ in self.zeroes:
            if in_.stem != "pins":
                abspath_zero = in_.abspath(self.cwd)
                file_name = f"{in_.stem}{SUFFIX_UNLOCKED}"
                abspath_unlocked = abspath_zero.parent.joinpath(file_name)

                if is_module_debug:  # pragma: no cover
                    msg_info = f"InFiles.write abspath_unlocked: {abspath_unlocked}"
                    _logger.info(msg_info)
                else:  # pragma: no cover
                    pass

                abspath_unlocked.touch(mode=0o644, exist_ok=True)
                is_file = abspath_unlocked.exists() and abspath_unlocked.is_file()

                if is_module_debug:  # pragma: no cover
                    _logger.info(f"InFiles.write is_file: {is_file}")
                else:  # pragma: no cover
                    pass

                if is_file:
                    sep = os.linesep
                    contents = sep.join(list(in_.requirements))
                    contents = f"{contents}{sep}"
                    abspath_unlocked.write_text(contents)
                    yield abspath_unlocked
                else:  # pragma: no cover
                    pass
            else:  # pragma: no cover
                pass

        yield from ()


def unlock_compile(inst):
    """pip requirement files can contain both ``-r`` and ``-c`` lines.
    Relative path to requirement files and constraint files respectively.

    Originally thought ``-c`` was a :command:`pip-compile` convention,
    not a pip convention. Opps!

    With presence of both ``.in`` and ``.lock`` files and then using the
    ``.in`` files would imply the package is (dependency) unlocked.

    So ``.in`` files are ``.unlock`` files.

    Creating ``.unlock`` files would serve no additional purpose, besides
    being explicit about the state of the package. That the author probably
    is no longer actively maintaining the package and thus has purposefully
    left the dependencies unlocked.

    :param inst:

       Backend subclass instance which has folders property containing
       ``collections.abc.Sequence[pathlib.Path]``

    :type inst: BackendType
    :returns: Generator of abs path to .lock files
    :rtype: collections.abc.Generator[pathlib.Path, None, None]
    :raises:

       - :py:exc:`drain_swamp.exceptions.MissingRequirementsFoldersFiles` --
         there are unresolvable constraint(s)

    """
    # Look at the folders. Then convert all ``.in`` --> ``.unlock``
    path_cwd = inst.parent_dir
    gen_unlocked_files = inst.in_files()
    in_files = list(gen_unlocked_files)
    del gen_unlocked_files

    # read in all .in files. key path_abs
    try:
        files = InFiles(path_cwd, in_files)
        files.resolution_loop()
    except MissingRequirementsFoldersFiles:
        raise
    else:
        gen = files.write()
        lst_called = list(gen)
        for abspath in lst_called:
            assert abspath.exists() and abspath.is_file()

        yield from lst_called

    yield from ()


def refresh_links(inst, is_set_lock=None):
    """Create/refresh ``.lnk`` files

    Does not write .lock or .unlock files

    :param inst:

       Backend subclass instance. Contains: dependencies, optional
       dependencies, and various paths

    :type inst: BackendType
    :param is_set_lock:

       Force the dependency lock. True to lock. False to unlock. None
       to use current lock state

    :type is_set_lock: bool | None
    :raises:

       - :py:exc:`drain_swamp.exceptions.MissingRequirementsFoldersFiles` --
         there are unresolvable constraint(s)

       - :py:exc:`AssertionError` -- In pyproject.toml no section,
         tool.setuptools.dynamic

       - :py:exc:`drain_swamp.exceptions.PyProjectTOMLParseError` --
         either not found or cannot be parsed

       - :py:exc:`drain_swamp.exceptions.PyProjectTOMLReadError` --
         Either not a file or lacks read permission

       - :py:exc:`TypeError` -- is_set_lock unsupported type expecting None or bool

       - :py:exc:`OSError` -- on Windows, malformed in file path --> PermissionError

    """
    is_invalid_set_lock = is_set_lock is not None and not isinstance(is_set_lock, bool)
    if is_invalid_set_lock:
        msg_exc = (
            "refresh_links parameter is_set_lock can be either None or "
            f"a boolean, got {is_set_lock!r}"
        )
        raise TypeError(msg_exc)
    else:  # pragma: no cover
        pass

    mod_path = "lock_toggle.refresh_links"
    path_cwd = inst.parent_dir
    path_config = inst.path_config
    gen_unlocked_files = inst.in_files()
    in_files = list(gen_unlocked_files)
    del gen_unlocked_files

    if is_module_debug:  # pragma: no cover
        msg_info = f"{mod_path} in_files: {in_files}"
        _logger.info(msg_info)
    else:  # pragma: no cover
        pass

    # read in all .in files. key path_abs
    try:
        files = InFiles(path_cwd, in_files)
        files.resolution_loop()
    except MissingRequirementsFoldersFiles:
        raise

    if is_set_lock is None:
        # Get dependency lock state from pyproject.toml
        try:
            is_locked = inst.is_locked(path_config)
        except Exception:
            # PyProjectTOMLParseError, PyProjectTOMLReadError, AssertionError
            raise
    else:
        """To update symlinks to unlock dependencies

        .. code-block:: shell

           python -m build --config-setting="--set-lock=1" --sdist

        To update symlinks to lock dependencies

        .. code-block:: shell

           python -m build --config-setting="--set-lock=0" --sdist

        """
        is_locked = is_set_lock
    suffix = SUFFIX_LOCKED if is_locked else SUFFIX_UNLOCKED

    if is_module_debug:  # pragma: no cover
        msg_info = (
            f"{mod_path} is_set_lock --> is_locked {is_set_lock!r} --> {is_locked!r}"
        )
        _logger.info(msg_info)
        zeroes_count = len(list(files.zeroes))
        msg_info = f"{mod_path} files.zeroes zeroes_count {zeroes_count}"
        _logger.info(msg_info)
        msg_info = f"{mod_path} files: {files}"
        _logger.info(msg_info)
    else:  # pragma: no cover
        pass

    msg_warn_lock_files = (
        "{}. No corresponding .unlock / .lock files"
        "Cannot make symlink. "
        "In {}, prepare the missing folders and files"
    )
    msg_warn_paths_malformed = (
        "Malformed .in file path. {exc} cwd: {path_cwd!r} abspath: {abspath!r}"
    )
    for in_ in files.zeroes:
        if in_.stem == "pins":
            # pins.in is used as-is
            continue
        else:  # pragma: no cover
            if is_module_debug:  # pragma: no cover
                msg_info = f"{mod_path} files.zeroes InFile {in_}"
                _logger.info(msg_info)
            else:  # pragma: no cover
                pass
            abspath_zero = in_.abspath(path_cwd)
            file_name = f"{in_.stem}{suffix}"
            abspath = abspath_zero.parent.joinpath(file_name)

            if is_module_debug:  # pragma: no cover
                msg_info = f"{mod_path} abspath (before check is exists): {abspath!r}"
                _logger.info(msg_info)
            else:  # pragma: no cover
                pass

            is_dest_file_exists = abspath.exists() and abspath.is_file()

            if not is_dest_file_exists:
                # No lock/unlock file, so skip creating a symlink
                msg_warn = msg_warn_lock_files.format(abspath, path_cwd)
                raise MissingRequirementsFoldersFiles(msg_warn)
            else:
                try:
                    _maintain_symlink(path_cwd, abspath)
                except (NotADirectoryError, FileNotFoundError) as e:
                    # cwd not a folder or lock/unlock file not exists
                    msg_warn = msg_warn_lock_files.format(
                        abspath,
                        path_cwd,
                    )
                    raise MissingRequirementsFoldersFiles(msg_warn) from e
                except OSError as e:
                    # On Windows, malformed path to .in file
                    d_args = {
                        "exc": str(e),
                        "abspath": abspath,
                        "path_cwd": path_cwd,
                    }
                    msg_warn = msg_warn_paths_malformed.format(**d_args)
                    raise OSError(msg_warn) from e
                except Exception as e:  # pragma: no cover
                    # Sad, but not the end of the world
                    if is_module_debug:  # pragma: no cover
                        msg_info = f"{mod_path} path_cwd: {path_cwd}"
                        _logger.info(msg_info)
                        msg_info = f"{mod_path} abspath: {abspath}"
                        _logger.info(msg_info)
                    else:  # pragma: no cover
                        pass
                    msg_exc = str(e)
                    _logger.warning(msg_exc)
