"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

When reading an ``.in`` file, in one shot, parse all pins.

``PinDatum`` do not ignore qualifiers.
With :py:class:`~drain_swamp.lock_datum.Pin`, qualifiers are not a first class citizen

.. py:data:: __all__
   :type: tuple[str, str]
   :value: ("FilePins", "get_path_cwd")

   Module exports

"""

from __future__ import annotations

import dataclasses
import logging
from collections.abc import (
    Collection,
    Hashable,
    Iterator,
)
from pathlib import (
    Path,
    PurePath,
)
from typing import cast

from pip_requirements_parser import (
    InstallationError,
    RequirementsFile,
)

from .check_type import is_ok
from .constants import g_app_name
from .exceptions import (
    MissingPackageBaseFolder,
    MissingRequirementsFoldersFiles,
)
from .lock_datum import (
    PinDatum,
    _parse_qualifiers,
    has_qualifiers,
    is_pin,
)
from .lock_util import is_suffixes_ok
from .pep518_venvs import check_loader

__all__ = (
    "FilePins",
    "get_path_cwd",
)

is_module_debug = False
_logger = logging.getLogger(f"{g_app_name}.lock_filepins")


def get_path_cwd(loader):
    """package base folder. During testing this will be tmp_path,
    not the source package folder. Patch would be helpful here

    :param loader: Contains some paths and loaded not parsed venv reqs
    :type loader: drain_swamp.pep518_venvs.VenvMapLoader
    :returns: package base folder
    :rtype: pathlib.Path

    :raises:

       - :py:exc:`drain_swamp.exceptions.MissingPackageBaseFolder` --
         loader did not provide package base folder

    """
    # VenvMapLoader data class validation is solid. Check useful only during testing
    check_loader(loader)

    ret = loader.project_base

    return ret


@dataclasses.dataclass
class FilePins(Collection[PinDatum], Hashable):
    """:py:class:`~drain_swamp.lock_inspect.Pins` from a `.in` file.
    Can contain packages with same name, but different qualifiers.

    :ivar file_abspath: ``.in`` file absolute Path
    :vartype: pathlib.Path

    .. py:attribute:: _pins
       :type: list[drain_swamp.lock_datum.PinDatum]

       Container of PinDatum

    .. py:attribute:: _iter
       :type: collections.abc.Iterator[drain_swamp.lock_datum.PinDatum]

       Iterator of PinDatum

    :raises:

       - :py:exc:`drain_swamp.exceptions.MissingRequirementsFoldersFiles` --
         .in requirements file not found

       - :py:exc:`ValueError` -- file suffixes are not ok

    """

    file_abspath: Path
    _pins: list[PinDatum] = dataclasses.field(init=False, default_factory=list)
    _iter: Iterator[PinDatum] = dataclasses.field(init=False)
    constraints: set[str] = dataclasses.field(init=False, default_factory=set)
    requirements: set[str] = dataclasses.field(init=False, default_factory=set)
    pkgs_from_resolved: set[str] = dataclasses.field(init=False, default_factory=set)

    def __post_init__(self):
        """From the requirements file retrieve package requirements."""

        try:
            abspath_file = is_suffixes_ok(self.file_abspath)
            rf = RequirementsFile.from_file(abspath_file)
        except InstallationError as exc:
            if is_module_debug:  # pragma: no cover
                # msg_info = f"file_abspath(before): {self.file_abspath}"
                # _logger.info(msg_info)
                msg_info = f"file_abspath(after): {abspath_file}"
                _logger.info(msg_info)
            else:  # pragma: no cover
                pass
            msg_exc = f"Requirements file not found {abspath_file!r}. Create it"
            raise MissingRequirementsFoldersFiles(msg_exc) from exc
        except ValueError:
            raise

        self.file_abspath = abspath_file

        d_rf_all = rf.to_dict()
        rf_reqs = d_rf_all["requirements"]

        lst_tmp = []
        for d_req in rf_reqs:
            # fields: line, line_number
            pkg_name: str = cast("str", d_req.get("name", ""))

            # list[specifier]
            specifiers: list[str] = cast("list[str]", d_req.get("specifier", []))

            # line
            d_req_line: dict[str, int | str] = cast(
                "dict[str, int | str]",
                d_req.get("requirement_line", {}),
            )
            is_line_str = "line" in d_req_line.keys() and isinstance(
                d_req_line["line"], str
            )
            if is_line_str:
                line: str = cast(str, d_req_line["line"])
            else:  # pragma: no cover
                line: str = ""

            if len(line.strip()) != 0:
                qualifiers = _parse_qualifiers(line)

                # Create Pin
                pin = PinDatum(
                    self.file_abspath, pkg_name, line, specifiers, qualifiers
                )

                # Filter out if an exact match
                if pin not in lst_tmp:
                    lst_tmp.append(pin)
                else:  # pragma: no cover
                    pass
            else:  # pragma: no cover
                # Dup
                pass

        # List items must implement: __hash__, __eq__, and __lt__
        self._pins = sorted(lst_tmp)

        # initialize iterator
        self._iter = iter(self._pins)

        """Example options list[dict[str, int|list[str]]]
        'options': [{'constraints': ['pins.shared.in'],
              'line': '-c pins.shared.in',
              'line_number': 4},
             {'constraints': ['pins-cffi.in'],
              'line': '-c pins-cffi.in',
              'line_number': 5},
             {'line': '-r prod.shared.in',
              'line_number': 6,
              'requirements': ['prod.shared.in']}],
        """
        rf_opts: list[dict[str, int | list[str]]] = d_rf_all["options"]
        set_constraints = set()
        set_requirements = set()
        for d_opt in rf_opts:
            # constraints|requirements, line, line_number
            is_constraint = "constraints" in d_opt.keys()
            is_requirements = "requirements" in d_opt.keys()
            if is_constraint:
                # strip_inline_comments
                constraints_relpath = cast("list[str]", d_opt["constraints"])
                for constraint_relpath in constraints_relpath:
                    set_constraints.add(constraint_relpath)
                else:  # pragma: no cover
                    pass
            else:  # pragma: no cover
                pass

            if is_requirements:
                # strip_inline_comments
                requirements_relpath = cast("list[str]", d_opt["requirements"])
                for requirement_relpath in requirements_relpath:
                    set_requirements.add(requirement_relpath)
                else:  # pragma: no cover
                    pass
            else:  # pragma: no cover
                pass

        # constraints and requirements are relpath. Existance not checked
        # lock_infile.InFile checked only the constraints and not the requirements
        self.constraints = set_constraints
        self.requirements = set_requirements
        """catalog of packages copied, into parent, from resolved
        constraints|requirements"""
        self.pkgs_from_resolved = set()

    def __len__(self):
        """Item count.

        :returns: Pin count
        :rtype: int
        """
        ret = len(self._pins)

        return ret

    def __next__(self):
        """Recreates the iterator every time it's completely consumed

        :returns: One pin within a requirements file
        :rtype: drain_swamp.lock_datum.PinDatum

        .. seealso::

           `reusable_range <https://realpython.com/python-iterators-iterables/#understanding-some-constraints-of-python-iterators>`_

        """
        try:
            return next(self._iter)
        except StopIteration:
            # Reinitialize iterator
            self._iter = iter(self._pins)
            # signal end of iteration
            raise

    def __iter__(self):
        """Entire Iterator

        :returns: Iterator
        :rtype: collections.abc.Iterator[typing_extensions.Self[drain_swamp.lock_datum.PinDatum]]
        """
        return self

    def __contains__(self, item):
        """``in`` support

        :param item: Item to test if within collection
        :type item: typing.Any
        :returns: True if a pin and pin in pins otherwise False
        :rtype: bool
        """
        is_ng = item is None or not isinstance(item, PinDatum)
        if is_ng:
            ret = False
        else:
            is_found = False
            for pin in self._pins:
                # Pin is a dataclass. Automagically has __eq__
                if pin == item:
                    is_found = True
                else:  # pragma: no cover
                    pass
            ret = is_found

        return ret

    def __hash__(self):
        """Constraints as constraints are resolved, are removed,
        increasing the requirements.

        Both fields are dynamic. For the point of identification,
        the relpath is unique

        :returns: hash of absolute path
        :rtype: int
        """
        ret = hash((self.file_abspath,))

        return ret

    def __eq__(self, right):
        """Compares equality

        :param right: right side of the equal comparison
        :type right: typing.Any
        :returns:

           True if both are same FilePins otherwise False. Does not take
           in account, constraints and requirements.

        :rtype: bool
        """
        is_type_same = right is not None and isinstance(right, FilePins)
        is_str = is_ok(right)
        is_abspath = (
            right is not None
            and issubclass(type(right), PurePath)
            and right.is_absolute()
        )
        if is_abspath:
            abspath_right = right
        elif is_str:
            abspath_right = Path(right)
        else:  # pragma: no cover
            pass

        if is_type_same:
            is_eq = self.__hash__() == right.__hash__()
            ret = is_eq
        elif is_str or is_abspath:
            # abspath
            left_hash = hash(self)
            right_hash = hash((abspath_right,))
            is_eq = left_hash == right_hash
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
        is_ng = right is None or not isinstance(right, FilePins)
        if is_ng:
            msg_warn = f"Expecting an FilePins got unsupported type {type(right)}"
            raise TypeError(msg_warn)
        else:  # pragma: no cover
            pass

        is_lt = str(self.file_abspath) < str(right.file_abspath)

        return is_lt

    def resolve(self, constraint, plural="constraints", singular="constraint"):
        """Constraint or requirement to discard

        Signature differs from
        :py:meth:`InFile.resolve <drain_swamp.lock_infile.InFile.resolve>`

        :param constraint:

           As provided by pip_requirements_parser.RequirementsFile, is
           a relative path, not absolute. Relative to the .in file, not cwd
           (package base folder)

        :type constraint: str
        :param plural: attribute name. There are two set, constraints and requirements
        :type plural: str
        :param singular: Just used in error messages. Singular form of the word
        :type singular: str
        :raises:

           - :py:exc:`AssertionError` -- object attribute does not exist.
             Should be either constraints or requirements

        """
        dotted_path = f"{g_app_name}.lock_filepins.FilePins.resolve"

        # Check plural
        is_plural_attrib_exists = is_ok(plural) and hasattr(self, plural)
        assert is_plural_attrib_exists

        # Check singular
        #    package pandantic could also change word forms
        singular_forms = ("constraint", "requirement")
        if is_ok(singular) and singular in singular_forms:  # pragma: no cover
            pass
        else:
            singular = "constraint"

        set_plural = getattr(self, plural)

        if is_module_debug:  # pragma: no cover
            msg_info = (
                f"{dotted_path} remove {singular!s} {constraint} "
                f"""from {set_plural!r}"""
            )
            _logger.info(msg_info)
        else:  # pragma: no cover
            pass

        """Both constraint and requirement, as provided by
        pip_requirements_parser.RequirementsFile, is a relative path,
        not absolute. And relative to the .in file, not cwd
        """
        # self.constraints.discard(constraint)
        set_plural.discard(constraint)

    def packages_save_to_parent(self, fpins, requirements):
        """During the resolution loop, as the resolved
        constraints|requirements are moved into zeroes, their packages
        are saved into parent

        :param fpins:

           Resolved child PinDatum, from resolved constraint|requirements.
           Store into parent

        :type fpins: list[drain_swamp.lock_datum.PinDatum]
        :param requirements:

           Resolved child ancestors packages.

        :type requirements: set[str]
        """
        # From child's ancestors. Obtained recursively
        for req in requirements:
            self.pkgs_from_resolved.add(req)

        # From child
        for pindatum in fpins:
            self.pkgs_from_resolved.add(pindatum.line)

    @property
    def depth(self):
        """Number of unresolved constraints. One this number gets down
        to zero, the FilePins is moved from files set --> zeroes set

        :returns: unresolved constraints count
        :rtype: int
        """
        return len(self.constraints)

    def relpath(self, loader):
        """Get the absolute path. The relative path is relative to the
        package folder.

        :param path_package_base: package base folder
        :type path_package_base: pathlib.Path
        :returns: absolute path
        :rtype: pathlib.Path
        :raises:

           - :py:exc:`drain_swamp.exceptions.MissingPackageBaseFolder` --
             loader did not provide package base folder

        """
        try:
            path_package_base = get_path_cwd(loader)
        except MissingPackageBaseFolder:
            raise
        ret = self.file_abspath.relative_to(path_package_base)

        return ret

    def by_pkg(self, pkg_name):
        """Get PinDatum by package name. Can have differing qualifiers

        :param pkg_name: Package name
        :type pkg_name: typing.Any
        :returns: For one package, list of PinDatum. Differs by qualifiers
        :rtype: list[drain_swamp.lock_datum.PinDatum]
        """
        if is_ok(pkg_name):
            ret = [pin for pin in self._pins if pin.pkg_name == pkg_name]
        else:
            ret = []

        return ret

    def by_pin_or_qualifier(self):
        """Yield if either a Pin or has qualifiers

        :returns: collections.abc.Generator[drain_swamp.lock_datum.PinDatum, None, None]
        """
        for pin in self._pins:
            is_notable = is_pin(pin.specifiers) or has_qualifiers(pin.qualifiers)
            if is_notable:
                yield pin
            else:  # pragma: no cover
                pass

        yield from ()
