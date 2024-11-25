"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

.. py:data:: DC_SLOTS
   :type: dict[str, bool]

   Allows dataclasses.dataclass __slots__ support from py310

.. py:class:: DATUM

.. py:data:: DATUM
   :type: typing.TypeVar
   :noindex:

   Class Pins is a Generic container. Allow changing which items
   the container can hold

.. py:class:: DatumByPkg

.. py:data:: DatumByPkg
   :type: dict[str, set[drain_swamp.lock_datum.Pin | drain_swamp.lock_datum.PinDatum]]
   :noindex:

   Store by pkg_name. Either all or notable (has specifiers or qualifiers)

.. py:data:: __all__
   :type: tuple[str, str, str, str, str, str, str, str]
   :value: ("InFileType", "Pin", "PinDatum", "in_generic", "is_pin", \
   "has_qualifiers", "DATUM", "DatumByPkg")

   Module exports

"""

import enum
import sys
from collections.abc import Hashable
from dataclasses import (
    dataclass,
    field,
)
from pathlib import (
    Path,
    PurePath,
)
from typing import (
    TypeVar,
    Union,
)

from pip_requirements_parser import RequirementsFile

if sys.version_info >= (3, 10):  # pragma: no cover py-gte-310-else
    DC_SLOTS = {"slots": True}
else:  # pragma: no cover py-gte-310
    DC_SLOTS = {}

__all__ = (
    "InFileType",
    "Pin",
    "PinDatum",
    "in_generic",
    "is_pin",
    "has_qualifiers",
    "DATUM",
    "DatumByPkg",
)


def is_pin(specifiers):
    """From ``.in`` file, identify as a pin only if has specifiers.

    :param specifiers: package specifiers e.g. ``>=1.0.0``
    :type specifiers: list[str]
    :returns: True if has specifiers otherwise False
    :rtype: bool
    """
    ret = len(specifiers) != 0

    return ret


def has_qualifiers(qualifiers):
    """From ``.in`` file, identify as a pin only if has qualifiers.

    :param qualifiers:

       package qualifiers e.g. ``platform_system=="Windows"``.
       Stored without ``;`` separator

    :type qualifiers: list[str]
    :returns: True if has qualifiers otherwise False
    :rtype: bool
    """
    ret = len(qualifiers) != 0

    return ret


def _parse_qualifiers(line):
    """From the requirement file line, retrieve a clean qualifiers list

    Strip whitespace and without semi colon

    Get qualifier e.g. '; python_version<"3.11"'

    Normalizes

    - ``os_name=="nt"`` --> ``platform_system=="Windows"``

    :returns: qualifiers
    :rtype: list[str]
    """
    qualifiers = []
    # clean qualifiers. strip and remove empties
    if ";" not in line:
        pass
    else:
        qualifiers_raw = line.split(";")
        # nudge pin portion e.g. ``pip<24.2``
        del qualifiers_raw[0]
        for qualifier in qualifiers_raw:
            str_qualifier = qualifier.strip()
            if len(str_qualifier) != 0:
                # Normalize -- ``os_name == "nt"`` --> ``platform_system=="Windows"``
                if str_qualifier.startswith("os_name") and "nt" in str_qualifier:
                    str_qualifier = 'platform_system=="Windows"'
                else:  # pragma: no cover
                    pass
                qualifiers.append(str_qualifier)
            else:  # pragma: no cover
                pass

    return qualifiers


def _hash_pindatum(file_abspath, pkg_name, qualifiers):
    """Determine hash support subclass as well

    :param file_abspath: Absolute path to ``.in`` file
    :type file_abspath: pathlib.Path
    :param pkg_name: Package name
    :type pkg_name: str
    :param qualifiers: List of qualifers. May
    :type qualifiers: list[str]
    :returns: hash of PinDatum or subclass
    :rtype: int
    """
    str_qualifiers = "; ".join(qualifiers)
    t_pieces = (file_abspath.as_posix(), pkg_name, str_qualifiers)

    return hash(t_pieces)


@dataclass(**DC_SLOTS)
class Pin(Hashable):
    """A pin has a specifier e.g. 'pip>=24.2' and may have one or more qualifiers

    Package dependencies w/o specifiers are not pins.

    :ivar file_abspath: absolute path to requirements file
    :vartype file_abspath: pathlib.Path
    :ivar pkg_name: pkg name by itself
    :vartype pkg_name: str
    :ivar line:

       Unaltered line. Spacing not normalized. Normalized with double quotes?
       Will contain ``the rest``. e.g.

       ``; python_version < "3.11"``
       ``; sys_platform == "win32"``
       `` ;platform_system=="Windows"``

    :vartype line: str
    :ivar specifiers: The package version constraints. Is a pin if a non-empty list.
    :vartype specifiers: list[str]
    :raises:

       - :py:exc:`KeyError` -- in requirements file no such package

    """

    file_abspath: Path
    pkg_name: str
    line: str = field(init=False)
    specifiers: list[str] = field(init=False, default_factory=list)

    def __hash__(self):
        """The file abspath and line are enough to produce a hash.

        pkg name is redundant, already contained within the line.
        specifiers is a view what's already within the line.

        :returns: hash of Pin
        :rtype: int
        """
        t_pieces = (self.file_abspath.as_posix(), self.line)
        return hash(t_pieces)

    def __post_init__(self):
        """From the requirements file retrieve package requirements."""
        rf = RequirementsFile.from_file(self.file_abspath)
        d_rf_all = rf.to_dict()
        rf_reqs = d_rf_all["requirements"]
        is_found = False
        is_nonempty_list = (
            rf_reqs is not None and isinstance(rf_reqs, list) and len(rf_reqs) != 0
        )
        if is_nonempty_list:
            for d_req in rf_reqs:
                # fields: line, line_number
                pkg_name_current = d_req.get("name", "")
                if pkg_name_current == self.pkg_name:
                    d_req_line = d_req.get("requirement_line", {})

                    # list[specifier]
                    self.specifiers = d_req.get("specifier", [])

                    # paranoia check
                    is_line_str = "line" in d_req_line.keys() and isinstance(
                        d_req_line["line"], str
                    )
                    if is_line_str:
                        self.line = d_req_line["line"]
                    else:  # pragma: no cover
                        self.line = ""

                    is_found = True
        else:  # pragma: no cover
            pass

        if not is_found:
            msg_exc = (
                f"Requirement file {self.file_abspath!r} does not "
                f"contain package {self.pkg_name}"
            )
            raise KeyError(msg_exc)
        else:  # pragma: no cover
            # if not cls.is_pin(self.specifiers):
            #    Package is not a pin. No specifier e.g. pip>=24.2"
            pass

    @staticmethod
    def is_pin(specifiers):
        """From a ``.unlock`` or ``.in`` file, identify a line as containing a pin.

        :param line: raw line from a ``.unlock`` or ``.in`` file
        :type line: list[str]
        :returns: True if a pin otherwise False
        :rtype: bool
        """
        ret = is_pin(specifiers)

        return ret

    @property
    def qualifiers(self):
        """From the Pin line, retrieve a clean qualifiers list

        Strip whitespace and without semi colon

        :returns: qualifiers
        :rtype: list[str]
        """
        # Get qualifier e.g. '; python_version<"3.11"'
        line = self.line

        # clean qualifiers. strip and remove empties
        qualifiers = []
        if ";" not in line:
            pass
        else:
            qualifiers_raw = line.split(";")
            # nudge pin portion e.g. ``pip<24.2``
            del qualifiers_raw[0]
            qualifiers = []
            for qualifier in qualifiers_raw:
                str_qualifier = qualifier.strip()
                if len(str_qualifier) != 0:
                    qualifiers.append(str_qualifier)
                else:  # pragma: no cover
                    pass

        return qualifiers


@dataclass(**DC_SLOTS)
class PinDatum(Hashable):
    """Qualifiers aware Pin. Use :py:class:`~drain_swamp.lock_filepins.FilePins`
    to instantiate.

    Hashable and Comparable

    """

    file_abspath: Path
    pkg_name: str
    line: str
    specifiers: list[str]
    qualifiers: list[str]

    def __hash__(self):
        """The file abspath and line are enough to produce a hash.

        pkg name is redundant, already contained within the line.
        specifiers is a view what's already within the line.

        :returns: hash of Pin
        :rtype: int
        """
        ret = _hash_pindatum(self.file_abspath, self.pkg_name, self.qualifiers)

        return ret

    def __eq__(self, right):
        """Compares equality

        :param right: right side of the equal comparison
        :type right: typing.Any
        :returns:

           True if both are same PinDatum otherwise False

        :rtype: bool
        """
        is_cls_similar = issubclass(type(right), PinDatum)

        if is_cls_similar:
            # Determine hash(right) without assuming identical fields
            # Subclasses hash(right) might include additional fields. Recalculate
            hash_right = _hash_pindatum(
                right.file_abspath,
                right.pkg_name,
                right.qualifiers,
            )
            is_eq = self.__hash__() == hash_right
            ret = is_eq
        else:
            ret = False

        return ret

    def __lt__(self, right):
        """Try comparing using stem. If both A and B have the same
        stem. Compare using relpath

        Implementing __hash__, __eq__, and __lt__ is the minimal
        requirement for supporting the python built-tin sorted method

        :param right: right side of the comparison
        :type right: typing.Any
        :returns: True if A < B otherwise False
        :rtype: bool
        :raises:

           - :py:exc:`TypeError` -- right operand is unsupported type

        """
        is_ng = right is None or not isinstance(right, PinDatum)
        if is_ng:
            msg_warn = f"Expecting an PinDatum got unsupported type {type(right)}"
            raise TypeError(msg_warn)
        else:  # pragma: no cover
            pass

        """For purposes of sorting, comparing PinDatum from different
        files is not allowed"""
        is_different_file = (
            self.file_abspath.as_posix() != right.file_abspath.as_posix()
        )
        if is_different_file:
            msg_warn = (
                f"PinDatum from different files cannot be compared "
                f"left {self.file_abspath!r} right {self.file_abspath!r}"
            )
            raise TypeError(msg_warn)
        else:  # pragma: no cover
            pass

        # InFiles container stores InFile within a set. So no duplicates
        # Compares tuple(stem_a, relpath_a) vs tuple(stem_b, relpath_b)
        is_pkg_name_eq = self.pkg_name == right.pkg_name
        if not is_pkg_name_eq:
            is_lt = self.pkg_name < right.pkg_name
        else:
            # pkg_name equal. Compare qualifiers
            left_qualifiers = "; ".join(self.qualifiers)
            right_qualifiers = "; ".join(right.qualifiers)
            is_qualifiers_eq = left_qualifiers == right_qualifiers
            if not is_qualifiers_eq:
                is_lt = left_qualifiers < right_qualifiers
            else:
                # qualifiers same. Cannot sort a dup
                is_lt = False

        return is_lt


DATUM = TypeVar("DATUM", bound=Union[Pin, PinDatum])
DatumByPkg = dict[str, set[Union[Pin, PinDatum]]]


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


def in_generic(
    inst,
    val,
    field_name="file_abspath",
    set_name=InFileType.FILES,
    is_abspath_ok=False,
):
    """A generic __contains__

    Comparing instances attribute path was removed

    :param inst: A class instance
    :type inst: object
    :param val: item to check if within zeroes
    :type val: typing.Any
    :param field_name:

       class instances attribute name which holds the relative or absolute path

    :type field_name: str
    :param set_name:

       Default :py:attr:`drain_swamp.lock_datum.InFileType.FILES`.
       Which set to search thru. zeroes or files

    :type set_name: drain_swamp.lock_datum.InFileType | None
    :param is_abspath_ok:

       Default False. True if class instance field is an absolute path.
       False if relative path

    :type is_abspath_ok: bool
    :returns: True if InFile contained within zeroes otherwise False
    :rtype: bool
    """
    if set_name is None or not isinstance(set_name, InFileType):
        str_set_name = str(InFileType.FILES)
    else:  # pragma: no cover
        str_set_name = str(set_name)

    if is_abspath_ok is None or not isinstance(is_abspath_ok, bool):
        is_abspath_ok = False
    else:  # pragma: no cover
        pass

    ret = False
    set_ = getattr(inst, str_set_name, set())
    for in_ in set_:
        # Does not do any path comparisons
        if is_abspath_ok:
            # absolute path (Path)
            mixed_path = getattr(in_, field_name, None)
            is_match_path = (
                mixed_path is not None
                and issubclass(type(val), PurePath)
                and val.is_absolute()
                and str(mixed_path) == str(val)
            )
            is_match_str = (
                mixed_path is not None
                and val is not None
                and isinstance(val, str)
                and Path(val).is_absolute()
                and str(mixed_path) == val
            )
        else:
            # relative path
            mixed_path = getattr(in_, field_name, None)
            assert mixed_path is not None
            str_relpath = str(mixed_path)
            is_match_path = (
                val is not None
                and issubclass(type(val), PurePath)
                and not val.is_absolute()
                and str_relpath == str(val)
            )
            is_match_str = (
                val is not None
                and isinstance(val, str)
                and not Path(val).is_absolute()
                and str_relpath == val
            )

        is_match_type = val is not None and isinstance(val, type(inst)) and in_ == val
        if is_match_type or is_match_path or is_match_str:
            ret = True
        else:  # pragma: no cover
            pass

    return ret
