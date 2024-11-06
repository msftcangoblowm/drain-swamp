"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

Separate out ``.in`` processing from ``.unlock`` and ``.lock`` implementations

.. py:data:: __all__
   :type: tuple[str, str, str, str]
   :value: ("strip_inline_comments", "InFileType", "InFile", "InFiles")

.. py:data:: _logger
   :type: logging.Logger

   Module level logger

.. py:data:: is_module_debug
   :type: bool
   :value: False

   on/off for module level logging

"""

import copy
import dataclasses
import enum
import logging
import os
import pathlib
from collections.abc import Sequence
from pathlib import (
    Path,
    PurePath,
)
from typing import cast

from ._safe_path import resolve_joinpath
from .constants import (
    SUFFIX_UNLOCKED,
    g_app_name,
)
from .exceptions import MissingRequirementsFoldersFiles
from .lock_util import (
    is_shared,
    replace_suffixes_last,
)

_logger = logging.getLogger(f"{g_app_name}.lock_infile")
is_module_debug = False
__all__ = (
    "strip_inline_comments",
    "InFileType",
    "InFile",
    "InFiles",
)


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
        :py:func:`drain_swamp.lock_infile.InFile.check_path` should
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
        # is a sequence
        if in_files is None or not isinstance(in_files, Sequence):
            msg_exc = f"Expecting a list[Path] got unsupported type {in_files}"
            raise TypeError(msg_exc)

        for path_abs in in_files:
            self.files = path_abs

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
        :rtype: collections.abc.Generator[drain_swamp.lock_infile.InFile, None, None]
        """
        yield from self._files

    @files.setter
    def files(self, val):
        """Append an InFile, requirement or constraint

        :param val:

           :py:class:`~drain_swamp.lock_infile.InFile` or absolute path
           to requirement or constraint file

        :type val: typing.Any
        """
        mod_path = f"{g_app_name}.lock_infile.InFiles.files"
        is_abspath = (
            val is not None
            and issubclass(type(val), PurePath)
            and val.is_absolute()
            and val.exists()
            and val.is_file()
        )
        if is_abspath:
            cls = type(self)
            path_abs = val
            try:
                InFile.check_path(self.cwd, path_abs)
            except (TypeError, ValueError, FileNotFoundError):  # pragma: no cover
                # Not Path and absolute so won't create InFile and add it to container
                msg_warn = f"{mod_path} Requirement file does not exist! {path_abs!r}"
                _logger.warning(msg_warn)
            else:
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
                    abspath_to_check = cast(
                        "Path",
                        resolve_joinpath(path_parent, cons_path),
                    )
                    try:
                        path_abs_constraint = abspath_to_check.resolve(strict=True)
                    except FileNotFoundError:
                        msg_warn = (
                            f"{mod_path} Constraint file does not exist! "
                            f"{abspath_to_check.resolve()}"
                        )
                        _logger.warning(msg_warn)
                        path_abs_constraint = abspath_to_check.resolve()
                        """
                        msg_exc = (
                            f"Within requirements file, {path_relpath}, a constraint "
                            f"file does not exist. Create it! {cons_path}"
                        )
                        raise MissingRequirementsFoldersFiles(msg_exc) from exc
                        """
                        pass

                    """Do not get to choose we don't like the constraint
                    cuz file not exists"""
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
                is_new = not self.in_zeroes(in_) and in_ not in self
                if is_new:
                    # Found a new constraint or requirement!
                    val = in_
                else:  # pragma: no cover
                    pass
        else:  # pragma: no cover
            pass

        is_infile = val is not None and isinstance(val, InFile)
        if is_infile:
            self._files.add(val)
        else:  # pragma: no cover
            pass

    @property
    def zeroes(self):
        """Generator of InFile

        :returns: Yields InFile without any constraints
        :rtype: collections.abc.Generator[drain_swamp.lock_infile.InFile, None, None]
        """
        yield from self._zeroes

    @zeroes.setter
    def zeroes(self, val):
        """append an InFile that doesn't have any constraints

        The only acceptable source of zeroes is from :code:`self._files`

        :param val: Supposed to be an :py:class:`~drain_swamp.lock_infile.InFile`
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

           Default :py:attr:`drain_swamp.lock_infile.InFileType.FILES`.
           Which set to search thru. zeroes or files

        :type set_name: drain_swamp.lock_infile.InFileType | None
        :returns: True if InFile contained within zeroes otherwise False
        :rtype: bool
        """
        if set_name is None or not isinstance(set_name, InFileType):
            str_set_name = str(InFileType.FILES)
        else:  # pragma: no cover
            str_set_name = str(set_name)

        """
        if is_module_debug:  # pragma: no cover
            msg_info = f"InFiles.in_generic InFile set name {str_set_name}"
            _logger.info(msg_info)
        else:  # pragma: no cover
            pass
        """
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
        """Get the index and :py:class:`~drain_swamp.lock_infile.InFile`

        :param relpath: relative path of a ``.in`` file
        :type relpath: str
        :param set_name:

           Default :py:attr:`drain_swamp.lock_infile.InFileType.FILES`.
           Which set to search thru. zeroes or files.

        :type set_name: str | None
        :returns:

           The ``.in`` file and index within
           :py:class:`~drain_swamp.lock_infile.InFiles`

        :rtype: drain_swamp.lock_infile.InFile | None
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

        # Add if new constraint?
        abspath_cwd = self.cwd
        add_these = []
        for in_ in self.files:
            for constraint_relpath in in_.constraints:
                is_in_zeroes = self.in_zeroes(constraint_relpath)
                is_in_files = constraint_relpath in self
                is_new = not is_in_zeroes and not is_in_files
                if is_new:
                    abspath_constraint = cast(
                        "Path",
                        resolve_joinpath(abspath_cwd, constraint_relpath),
                    )
                    # Attempt to add the constraint to self._files
                    add_these.append(abspath_constraint)
                else:  # pragma: no cover
                    pass

        # Add new after iterator is exhausted
        for abspath_constraint in add_these:
            self.files = abspath_constraint

        # Any contraints zeroes?
        self.move_zeroes()

        # Resolve with zeroes
        for in_ in self.files:
            constaints_copy = copy.deepcopy(in_.constraints)
            for constraint_relpath in constaints_copy:
                is_in_zeroes = self.in_zeroes(constraint_relpath)
                is_in_files = constraint_relpath in self

                if is_module_debug:  # pragma: no cover
                    msg_info = (
                        f"resolve_zeroes constraint {constraint_relpath} "
                        f"in zeroes {is_in_zeroes} in files {is_in_files}"
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
                msg_warn = (
                    "Missing .in requirements file(s). Unable to resolve "
                    "constraint(s). Files with unresolvable constraints: "
                    f"{unresolvable_requirement_files}. "
                    f"Missing constraints: {missing_contraints}"
                )
                _logger.warning(msg_warn)
                raise MissingRequirementsFoldersFiles(msg_warn)
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
            abspath_zero = in_.abspath(self.cwd)
            is_shared_pin = abspath_zero.name.startswith("pins") and is_shared(
                abspath_zero.name
            )
            if not is_shared_pin:
                abspath_unlocked = replace_suffixes_last(abspath_zero, SUFFIX_UNLOCKED)

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
