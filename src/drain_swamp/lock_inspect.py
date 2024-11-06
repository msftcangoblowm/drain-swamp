"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

Multiple ``pip-compile`` runs are not coordinated. Without coordination,
the output files most likely will contain different package versions for
the same package. This issue will occur many times.

Due to the plethora of packages, manually searching for these
discrepancies, across ``.lock`` files, is error prone; even with grep.

Creates a demand for a output files post processor. To find
and report these discrepancies and suggest how to resolve them.

``drain-swamp`` has ``.in``, ``.unlock``, **and** ``.lock`` files.
Since the ``.in`` are cascading, ``.unlock`` files are flattened. So
the constraints are easy to find. Rather than digging thru a bunch of
``.in`` files.

.. py:data:: DC_SLOTS
   :type: dict[str, bool]

   Allows dataclasses.dataclass __slots__ support from py310

.. py:data:: is_module_debug
   :type: bool
   :value: False

   Flag to turn on module level logging. Should be off in production

.. py:data:: _logger
   :type: logging.Logger

   Module level logger

.. py:class:: _T

.. py:data:: _T
   :type: typing.TypeVar
   :noindex:

   Class Pins is a Generic container. Allowing to change which items
   are allowed into the container

.. py:class:: PinsByPkg

.. py:data:: PinsByPkg
   :type: dict[str, set[drain_swamp.lock_inspect.Pin]]
   :noindex:

   dict of package name by set of Pins or locks. ``.unlock`` contains pin.
   ``.lock`` contain locks. Both are stored as Pin

.. py:class:: PkgsWithIssues

.. py:data:: PkgsWithIssues
   :type: dict[str, dict[str, packaging.version.Version | set[packaging.version.Version]]]
   :noindex:

   Packages by a dict containing highest version and other versions

"""

from __future__ import annotations

import fileinput
import io
import logging
import os
import re
import sys
from collections.abc import (
    Iterator,
    MutableSet,
    Sequence,
)
from dataclasses import (
    dataclass,
    field,
)
from functools import singledispatch
from pathlib import (
    Path,
    PurePath,
)
from pprint import pprint
from typing import (
    TYPE_CHECKING,
    TypeVar,
    Union,
    cast,
)

from packaging.specifiers import SpecifierSet
from packaging.version import Version
from pip_requirements_parser import (
    InstallationError,
    RequirementsFile,
)

from ._package_installed import is_package_installed
from ._run_cmd import run_cmd
from ._safe_path import (
    resolve_joinpath,
    resolve_path,
)
from .check_type import is_ok
from .constants import (
    SUFFIX_IN,
    SUFFIX_LOCKED,
    SUFFIX_UNLOCKED,
    g_app_name,
)
from .exceptions import MissingRequirementsFoldersFiles
from .lock_infile import InFiles
from .lock_util import (
    is_shared,
    replace_suffixes_last,
)
from .pep518_venvs import (
    TOML_SECTION_VENVS,
    VenvMap,
)

# Use dataclasses slots True for reduced memory usage and performance gain
if sys.version_info >= (3, 10):  # pragma: no cover py-gte-310-else
    DC_SLOTS = {"slots": True}
else:  # pragma: no cover py-gte-310
    DC_SLOTS = {}

is_module_debug = False
_logger = logging.getLogger(f"{g_app_name}.lock_inspect")


@dataclass(**DC_SLOTS)
class Pin:
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
        ret = len(specifiers) != 0

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


PinsByPkg = dict[str, list[Pin]]

_T = TypeVar("_T", bound=Pin)

PkgsWithIssues = dict[str, dict[str, Union[Version, set[Version]]]]


class Pins(MutableSet[_T]):
    """Pin container.

    :ivar pins: Expecting either a Sequence[_T] or Set[_T]
    :vartype pins: typing.Any

    .. py:attribute:: _pins
       :type: set[drain_swamp.lock_inspect._T]

       Container of Pin

    .. py:attribute:: _iter
       :type: collections.abc.Iterator[drain_swamp.lock_inspect._T]

       Holds the reusable iterator

    """

    _pins: set[_T]
    _iter: Iterator[_T]
    __slots__ = ("_pins", "_iter")

    def __init__(self, pins):
        """First create a factory. Then feed in the factory's result."""
        is_ng = pins is None or not (
            isinstance(pins, Sequence) or isinstance(pins, set)
        )
        if is_ng:
            cls_name = self.__class__.__name__
            msg_exc = f"{cls_name} expects Sequence[Pin] or Set[Pin] got {type(pins)}"
            raise TypeError(msg_exc)
        else:  # pragma: no cover
            pass

        self._pins = set()
        for pin in pins:
            self._pins.add(pin)

        # initialize iterator
        self._iter = iter(self._pins)

    def __len__(self):
        """Item count.

        :returns: Pin count
        :rtype: int
        """
        ret = len(self._pins)

        return ret

    def __iter__(self):
        """Iterator.

        :returns: Iterator
        :rtype: collections.abc.Iterator[typing_extensions.Self[drain_swamp.lock_inspect._T]]
        """
        return self

    def __next__(self):
        """Recreates the iterator everyone time it's completely consumed

        :returns: One pin within a requirements file
        :rtype: drain_swamp.lock_inspect._T

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

    def __contains__(self, item):
        """``in`` support.

        :param item: Item to test if within collection
        :type item: typing.Any
        :returns: True if a pin and pin in pins otherwise False
        :rtype: bool
        """
        is_ng = item is None or not isinstance(item, Pin)
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

    def add(self, item):
        """Add item to set

        :param item: Expecting a Pin. Add to set
        :type item: typing.Any
        """
        is_type_ok = item is not None and isinstance(item, Pin)
        if is_type_ok and item not in self:
            self._pins.add(item)
        else:  # pragma: no cover
            pass

    def discard(self, item):
        """Remove item from set if present

        :param item: Expecting a Pin. Remove from set
        :type item: typing.Any
        """
        is_type_ok = item is not None and isinstance(item, Pin)
        if is_type_ok and item in self:
            self._pins.discard(item)
        else:  # pragma: no cover
            pass

    def __repr__(self):
        """See what is going on rather than use to reproduce instance.

        :returns: Shows list[Pin]
        :rtype: str
        """
        cls_name = self.__class__.__name__
        lst = "["
        is_first = True
        for pin in self._pins:
            if is_first:
                lst += f"{pin!r}"
                is_first = False
            else:
                lst += f", {pin!r}"
        lst += "]"
        ret = f"<{cls_name} _pins={lst}>"

        return ret

    @staticmethod
    def from_loader(loader, venv_path, suffix=SUFFIX_UNLOCKED, filter_by_pin=True):
        """Factory. From a venv, get all Pins.

        :param loader: Contains some paths and loaded not parsed venv reqs
        :type loader: drain_swamp.pep518_venvs.VenvMapLoader
        :param venv_path:

           Relative path to venv base folder. Acts as a key

        :type venv_path: typing.Any
        :param suffix:

           Default ``.unlock``. End suffix of compiled requirements file.
           Either ``.unlock`` or ``.lock``

        :type suffix: str
        :param filter_by_pin: Default True. Filter out entries without specifiers
        :type filter_by_pin: bool | None
        :returns: Feed list[Pin] into class constructor to get an Iterator[Pin]
        :rtype: set[drain_swamp.lock_inspect._T]
        :raises:

            - :py:exc:`drain_swamp.exceptions.MissingRequirementsFoldersFiles` --
              missing requirements file(s). Create it

        """
        if filter_by_pin is None or not isinstance(filter_by_pin, bool):
            filter_by_pin = True
        else:  # pragma: no cover
            pass

        """Relative path acts as a dict key. An absolute path is not a key.
        Selecting by always nonexistent key returns empty Sequence, abspath_reqs"""
        is_abs_path = is_ok(venv_path) and Path(venv_path).is_absolute()
        is_abspath = (
            venv_path is not None
            and issubclass(type(venv_path), PurePath)
            and venv_path.is_absolute()
        )
        if is_abs_path or is_abspath:
            venv_path = Path(venv_path).relative_to(loader.project_base).as_posix()
        else:  # pragma: no cover
            pass

        # NotADirectoryError, ValueError, KeyError, MissingRequirementsFoldersFiles
        abspath_reqs = get_reqs(loader, venv_path, suffix_last=suffix)

        pins = set()
        for abspath_req in abspath_reqs:

            """Take only enough details to identify package as a pin.

            In .unlock files, ``-c`` and ``-r`` are resolved. Therefore
            ``options`` section will be empty
            """
            try:
                rf = RequirementsFile.from_file(abspath_req)
            except InstallationError as exc:
                msg_exc = (
                    f"For venv {venv_path!s}, requirements file not "
                    f"found {abspath_req!r}. Create it"
                )
                raise MissingRequirementsFoldersFiles(msg_exc) from exc

            d_rf_all = rf.to_dict()
            rf_reqs = d_rf_all["requirements"]
            has_reqs = (
                rf_reqs is not None and isinstance(rf_reqs, list) and len(rf_reqs) != 0
            )
            if has_reqs:
                for d_req in rf_reqs:
                    pkg_name = d_req.get("name", "")
                    # list[specifier]
                    specifiers = d_req.get("specifier", [])

                    # Only keep package which have specifiers e.g. ``pip>=24.2``
                    if filter_by_pin is True:
                        if Pin.is_pin(specifiers):
                            pin = Pin(abspath_req, pkg_name)
                            pins.add(pin)
                        else:  # pragma: no cover
                            # non-Pin --> filtered out
                            pass
                    else:
                        # Do not apply filter. All entries
                        pin = Pin(abspath_req, pkg_name)
                        pins.add(pin)
            else:  # pragma: no cover
                pass
        else:  # pragma: no cover
            pass

        return pins

    @staticmethod
    def subset_req(venv_reqs, pins, req_relpath):
        """Factory. For a venv Pins, create a subset limited to one requirement
        file.

        :param venv_reqs: All Requirement files (w/o final suffix)
        :type venv_reqs: list[drain_swamp.pep518_venvs.VenvReq]
        :param pins: one venv's Pins
        :type pins: Pins[drain_swamp.lock_inspect._T]
        :param req_relpath: A requirement file (w/o final suffix) relative path
        :type req_relpath: str
        :returns:

           Feed set[T] into class constructor to get an
           Iterator[drain_swamp.lock_inspect._T]

        :rtype: set[drain_swamp.lock_inspect._T]
        """
        if TYPE_CHECKING:
            pins_out: set[_T]
            req_relpath: str

        pins_out = set()

        for venv_req in venv_reqs:
            req_relpath = venv_req.req_relpath
            for pin in pins:
                winsafe_relpath = str(Path(req_relpath))
                winsafe_abspath = str(pin.file_abspath)

                # relpath in abspath
                is_winsafe_comparison = winsafe_relpath in winsafe_abspath
                if is_winsafe_comparison:
                    pins_out.add(pin)
                else:  # pragma: no cover
                    pass

        return pins_out

    @classmethod
    def by_pkg(cls, loader, venv_path, suffix=SUFFIX_LOCKED, filter_by_pin=True):
        """Group Pins by pkg_name.

        :param loader: From pyproject.toml, loads venvs, but does not parse the data
        :type loader: drain_swamp.pep518_venvs.VenvMapLoader
        :param venv_path:

           Path to a virtual env. There should be a cooresponding entry in
           pyproject.toml tool.venvs array of tables.

        :type venv_path: str
        :param suffix:

           Default ``.lock``. Either ``.lock`` or ``.unlock``. Determines
           which files are read. Looks at last suffix so
           ``.shared.[whatever]`` is supported

        :type suffix: str | None
        :param filter_by_pin: Default True. Filter out entries without specifiers
        :type filter_by_pin: bool | None
        :returns: dict which has Pins grouped by package name
        :rtype: drain_swamp.lock_inspect.PinsByPkg
        """
        d_by_pkg = _wrapper_pins_by_pkg(
            loader,
            venv_path,
            suffix=suffix,
            filter_by_pin=filter_by_pin,
        )

        return d_by_pkg

    @classmethod
    def by_pkg_with_issues(cls, loader, venv_path):
        """Filter out packages without issues. Each pin indicate highest
        Version and set of other Versions. Which to choose would need to
        take into account pins located within ``.unlock`` files.

        :param loader:

           From pyproject.toml, loads venvs, but does not parse the data.
           Expecting loader of the ``.lock`` files.

        :type loader: drain_swamp.pep518_venvs.VenvMapLoader
        :param venv_path:

           Path to a virtual env. There should be a cooresponding entry in
           pyproject.toml tool.venvs array of tables.

        :type venv_path: str
        :returns:

           packages by Pins and packages by dict of highest version and other versions

        :rtype: tuple[drain_swamp.lock_inspect.PinsByPkg, drain_swamp.lock_inspect.PkgsWithIssues]
        """
        # Organize pins by package name
        locks_by_pkg = Pins.by_pkg(loader, venv_path)

        # Search thru ``.lock`` files for discrepancies
        d_pkg_by_vers = Pins.has_discrepancies(locks_by_pkg)

        # filters out packages without issues
        locks_by_pkg_w_discrepancies = {
            k: v for k, v in locks_by_pkg.items() if k in d_pkg_by_vers.keys()
        }

        """
        mod_path = f"{g_app_name}.lock_inspect.Pins.by_pkg_with_issues"
        if is_module_debug:  # pragma: no cover
            msg_info = f"{mod_path} Locks by pkg: {locks_by_pkg}"
            _logger.info(msg_info)
            msg_info = f"{mod_path} Discrepancies in .lock files: {d_pkg_by_vers!r}"
            _logger.info(msg_info)
            msg_info = f"{mod_path} Locks by pkg w/ issues: {locks_by_pkg_w_discrepancies!r}"
            _logger.info(msg_info)
            pass
        else:  # pragma: no cover
            pass
        """
        pass

        return locks_by_pkg_w_discrepancies, d_pkg_by_vers

    @staticmethod
    def has_discrepancies(d_by_pkg):
        """Across ``.lock`` files, packages with discrepancies.

        Comparison limited to equality

        :param d_by_pkg: Within one venv, all lock packages' ``set[Pin]``
        :type d_by_pkg: drain_swamp.lock_inspect.PinsByPkg
        :returns:

           pkg name / highest version. Only packages with discrepancies.
           With the highest version, know which version to *nudge* to.

        :rtype: drain_swamp.lock_inspect.PkgsWithIssues
        """
        if TYPE_CHECKING:
            d_out: dict[str, Version]
            pkg_name: str
            highest: Version | None

        d_out = {}
        for pkg_name, pins in d_by_pkg.items():
            # pick latest version
            highest = None
            set_others = set()
            has_changed = False
            for pin in pins:
                """Get version. Since a ``.lock`` file, there will only be one
                specifer ``==[sem version]``"""
                specifier = pin.specifiers[0]
                pkg_sem_version = specifier[2:]
                ver = Version(pkg_sem_version)

                if highest is None:
                    highest = ver
                else:
                    is_greater = ver > highest
                    is_not_eq = ver != highest

                    if is_greater:
                        set_others.add(highest)
                        set_others.discard(ver)
                        highest = ver
                        has_changed = True
                    elif is_not_eq:
                        # lower indicates discrepancy exists.
                        # Keep lowers to have a available versions set
                        set_others.add(ver)
                        has_changed = True
                    else:  # pragma: no cover
                        pass

            if has_changed:
                d_out[pkg_name] = {
                    "highest": cast("Version", highest),
                    "others": cast("set[Version]", set_others),
                }
            else:  # pragma: no cover
                # continue
                pass

        return d_out

    @staticmethod
    def filter_pins_of_pkg(pins_current: Pins[_T], pkg_name: str) -> Pins[_T]:
        """Filter unlock Pins by package name.

        :param pins_current:

           All unlock Pins. Get this one

        :type pins_current: drain_swamp.lock_inspect.Pins[drain_swamp.lock_inspect._T]
        :param pkg_name: Filter by this package name
        :type pkg_name: str
        :returns: Pins of one package
        :rtype: drain_swamp.lock_inspect.Pins[drain_swamp.lock_inspect._T]
        """
        pins = []
        for pin in pins_current:
            if pin.pkg_name == pkg_name:
                pins.append(pin)
            else:  # pragma: no cover
                pass

        return Pins(pins)

    @classmethod
    def qualifiers_by_pkg(cls, loader, venv_path):
        """Get qualifiers by package. First non-empty qualifiers found wins.

        This algo, will fail to discover and fix qualifier disparities.
        Only gets fixed if there are version disparities

        :param loader:

           From pyproject.toml, loads venvs, but does not parse the data.
           Expecting loader of the ``.lock`` files.

        :type loader: drain_swamp.pep518_venvs.VenvMapLoader
        :param venv_path:

           Path to a virtual env. There should be a cooresponding entry in
           pyproject.toml tool.venvs array of tables.

        :type venv_path: str
        :returns: dict of package name by qualifiers
        :rtype: dict[str, str]
        """
        d_out = {}

        # unfiltered pkg entries
        locks_by_pkg = Pins.by_pkg(
            loader,
            venv_path,
            suffix=SUFFIX_UNLOCKED,
            filter_by_pin=False,
        )

        for pkg_name, pins in locks_by_pkg.items():
            for pin in pins:
                # Does this pin have qualifiers?
                quals = pin.qualifiers
                has_quals = len(quals) != 0
                if pkg_name not in d_out.keys() and has_quals:
                    str_pkg_qualifiers = "; ".join(quals)
                    str_pkg_qualifiers = f"; {str_pkg_qualifiers}"
                    d_out[pkg_name] = str_pkg_qualifiers
                else:  # pragma: no cover
                    pass

            # empty str for a package without qualifiers
            if pkg_name not in d_out.keys():
                d_out[pkg_name] = ""
            else:  # pragma: no cover
                pass

        return d_out


def _wrapper_pins_by_pkg(
    loader,
    venv_path,
    suffix=SUFFIX_LOCKED,
    filter_by_pin=True,
):
    """Pins.by_pkg is a boundmethod that is not callable.
    Wrap classmethod; this function will be callable
    """
    possible_suffixes = (
        SUFFIX_UNLOCKED,
        SUFFIX_LOCKED,
        f".shared{SUFFIX_UNLOCKED}",
        f".shared{SUFFIX_LOCKED}",
    )
    is_suffix_ng = (
        suffix is None or not isinstance(suffix, str) or suffix not in possible_suffixes
    )
    if is_suffix_ng:
        suffix = SUFFIX_LOCKED
    else:  # pragma: no cover
        pass

    is_filter_arg_ng = filter_by_pin is None or not isinstance(filter_by_pin, bool)
    if is_filter_arg_ng:
        filter_by_pin = True
    else:  # pragma: no cover
        pass

    d_by_pkg = {}

    # Load all venvs from pyproject.toml (or test file, .pyproject_toml)
    venvs = VenvMap(loader)

    # Limit to one venv. Mixing venvs is not allowed.
    # Go thru, this venv, all reqs files
    lst_venv_reqs = venvs.reqs(venv_path)
    # req_first = lst_venv_reqs[0]
    # path_venv = req_first.venv_abspath

    try:
        lst_pins = Pins.from_loader(
            loader,
            venv_path,
            suffix=suffix,
            filter_by_pin=filter_by_pin,
        )
        pins_locks = Pins(lst_pins)
    except MissingRequirementsFoldersFiles:
        raise

    for venv_req in lst_venv_reqs:
        pins_req = Pins(
            Pins.subset_req(lst_venv_reqs, pins_locks, venv_req.req_relpath)
        )
        for pin in pins_req:
            pkg_name = pin.pkg_name
            is_known_pkg = pin.pkg_name in d_by_pkg.keys()
            if not is_known_pkg:
                # create set
                set_new = set()
                set_new.add(pin)
                d_by_pkg.update({pkg_name: set_new})
            else:
                # update set
                pins = d_by_pkg[pkg_name]
                pins.add(pin)
                d_by_pkg.update({pkg_name: pins})

    return d_by_pkg


@dataclass(**DC_SLOTS)
class Resolvable:
    """Resolvable dependency conflict. Can find the lines for the pkg,
    in ``.unlock`` and ``.lock`` files, using (loader and)
    venv_path and pkg_name.

    Limitation: Qualifiers
    e.g. python_version and os_name

    - haphazard usage

    All pkg lines need the same qualifier. Often missing. Make uniform.
    Like a pair of earings.

    - rigorous usage

    There can be one or more qualifiers. In which case, nonobvious which qualifier
    to use where.

    :ivar venv_path: Relative or absolute path to venv base folder
    :vartype venv_path: str | pathlib.Path
    :ivar pkg_name: package name
    :vartype pkg_name: str
    :ivar qualifiers:

       qualifiers joined together into one str. Whitespace before the
       1st semicolon not preserved.

    :vartype qualifiers: str
    :ivar nudge_unlock:

       For ``.unlock`` files. Nudge pin e.g. ``pkg_name>=some_version``.
       If pkg_name entry in an ``.unlock`` file, replace otherwise add entry

    :vartype nudge_unlock: str
    :ivar nudge_lock:

       For ``.lock`` files. Nudge pin e.g. ``pkg_name==some_version``.
       If pkg_name entry in a ``.lock`` file, replace otherwise add entry

    :vartype nudge_lock: str
    """

    venv_path: str | Path
    pkg_name: str
    qualifiers: str
    nudge_unlock: str
    nudge_lock: str


@dataclass(**DC_SLOTS)
class UnResolvable:
    """Cannot resolve this dependency conflict.

    Go out of our way to clearly and cleanly present sufficient
    details on the issue.

    The most prominent details being the package name and Pins
    (from relevent ``.unlock`` files).

    **Track down issue**

    With issue explanation. Look at the ``.lock`` to see the affected
    package's parent(s). The parents' package pins may be the cause of
    the conflict.

    The parents' package ``pyproject.toml`` file is the first place to look
    for strange dependency restrictions. Why a restriction was imposed upon a
    dependency may not be well documented. Look in the repo issues. Search for
    the dependency package name

    **Upgrading**

    lock inspect is not a dependency upgrader. Priority is to sync
    ``.unlock`` and ``.lock`` files.

    Recommend always doing a dry run
    :code:`pip compile --dry-run some-requirement.in` or
    looking at upgradable packages within the venv. :code:`pip list -o`

    :ivar venv_path: Relative or absolute path to venv base folder
    :vartype venv_path: str | pathlib.Path
    :ivar pkg_name: package name
    :vartype pkg_name: str
    :ivar qualifiers:

       qualifiers joined together into one str. Whitespace before the
       1st semicolon not preserved.

    :vartype qualifiers: str
    :ivar sss:

       Set of SpecifierSet, for this package, are the dependency version
       restrictions found in ``.unlock`` files

    :vartype sss: set[packaging.specifiers.SpecifierSet]
    :ivar v_highest:

       Hints at the process taken to find a Version which
       satisfies SpecifierSets. First this highest version was checked

    :vartype v_highest: packaging.version.Version
    :ivar v_others:

       After highest version, all other potential versions are checked.
       The potential versions come from the ``.lock`` files. So if a
       version doesn't exist in one ``.lock``, it's never tried.

    :vartype v_others: set[packaging.version.Version]
    :ivar pins:

       Has the absolute path to each requirements file and the dependency
       version restriction.

       Make this readable

    :vartype pins: drain_swamp.lock_inspect.Pins[drain_swamp.lock_inspect.Pin]
    """

    venv_path: str
    pkg_name: str
    qualifiers: str
    sss: set[SpecifierSet]
    v_highest: Version
    v_others: set[Version]
    pins: Pins[Pin]

    def pprint_pins(self):
        """Capture pprint and return it.

        :returns: pretty printed representation of the pins
        :rtype: str
        """
        with io.StringIO() as f:
            pprint(self.pins, stream=f)
            ret = f.getvalue()

        return ret

    def __repr__(self):
        """Emphasis is on presentation, not reproducing an instance.

        :returns: Readable presentation of the unresolvable dependency conflict
        :rtype: str
        """
        cls_name = self.__class__.__name__
        ret = (
            f"<{cls_name} pkg_name='{self.pkg_name}' venv_path='{self.venv_path!s}' \n"
        )
        ret += f"qualifiers='{self.qualifiers}' sss={self.sss!r} \n"
        ret += f"v_highest={self.v_highest!r} v_others={self.v_others!r} \n"
        ret += f"pins={self.pprint_pins()}>"

        return ret


@dataclass(**DC_SLOTS)
class ResolvedMsg:
    """Fixed dependency version discrepancies (aka issues)

    Does not include the original line

    :ivar venv_path: venv relative or absolute path
    :vartype venv_path: str
    :ivar abspath_f: Absolute path to requirements file
    :vartype abspath_f: pathlib.Path
    :ivar nudge_pin_line: What the line will become
    :vartype nudge_pin_line: str
    """

    venv_path: str
    abspath_f: Path
    nudge_pin_line: str


def get_reqs(loader, venv_path=None, suffix_last=SUFFIX_IN):
    """get absolute path to requirement files

    Filtering by venv relative or absolute path is recommended

    :param loader: Contains some paths and loaded unparsed mappings
    :type loader: drain_swamp.pep518_venvs.VenvMapLoader
    :param venv_path: Filter by venv relative or absolute path
    :type venv_path: typing.Any
    :param suffix_last: Default ``.in``. Last suffix is replaced, not all suffixes
    :type suffix_last: str
    :returns: Sequence of absolute path to requirements files
    :rtype: tuple[pathlib.Path]
    :raises:

       - :py:exc:`NotADirectoryError` -- venv relative paths do not correspond to
         actual venv folders

       - :py:exc:`ValueError` -- expecting [[tool.venvs]] field reqs to be a
         sequence

       - :py:exc:`KeyError` -- No such venv found

       - :py:exc:`drain_swamp.exceptions.MissingRequirementsFoldersFiles` --
         There are missing ``.in`` files. Support file(s) not checked

    """
    """Relative path acts as a dict key. An absolute path is not a key.
    Selecting by always nonexistent key returns empty Sequence"""
    is_abs_path = is_ok(venv_path) and Path(venv_path).is_absolute()
    is_abspath = (
        venv_path is not None
        and issubclass(type(venv_path), PurePath)
        and venv_path.is_absolute()
    )
    if is_abs_path or is_abspath:
        venv_path = Path(venv_path).relative_to(loader.project_base).as_posix()
    else:  # pragma: no cover
        pass
    check_suffixes = (suffix_last,)

    venv_relpaths = loader.venv_relpaths

    # Ensure requirements files defined in [[tool.venvs]] reqs exists
    try:
        venvs = VenvMap(loader, check_suffixes=check_suffixes)
        msg_missing = "\n".join(venvs.missing)
        is_missing = len(venvs.missing) != 0
        if is_missing:
            raise MissingRequirementsFoldersFiles(msg_missing)
        else:  # pragma: no cover
            pass
        assert len(venvs.missing) == 0, msg_missing
    except (NotADirectoryError, ValueError, AssertionError):
        raise

    set_out = set()
    is_get_all = venv_path is None
    is_venvs_found = venv_path is not None and venv_path in venv_relpaths
    if is_get_all or is_venvs_found:
        venv_relpaths_filtered = [
            venv_path_key
            for venv_path_key in venv_relpaths
            if is_get_all or venv_path_key == venv_path
        ]
        for venv_path_key in venv_relpaths_filtered:
            # filtered so no KeyError
            reqs = venvs.reqs(venv_path_key)

            for path_in_ in reqs:
                # requirements .unlock files, not the source within .in files
                # where to apply ``nudges`` is another story.
                path_venvreq = cast(
                    "Path",
                    resolve_joinpath(path_in_.project_base, path_in_.req_relpath),
                )
                abspath_req = replace_suffixes_last(path_venvreq, suffix_last)
                set_out.add(abspath_req)
    else:
        # venv_path not in venv_relpaths
        msg_warn = (
            f"venv {venv_path} not in [[tool.{TOML_SECTION_VENVS}]] "
            f"venv paths {venv_relpaths}"
        )
        raise KeyError(msg_warn)

    return tuple(set_out)


def get_issues(loader, venv_path):
    """Look thru all the packages with discrepanies. Which have existing
    nudge(s). Find where those nudges are in the ``.in`` files.

    Replace or add as appropriate

    :param loader: Contains some paths and loaded unparsed mappings
    :type loader: drain_swamp.pep518_venvs.VenvMapLoader
    :param venv_path: venv relative or absolute path
    :type venv_path: str
    :returns: Resolvable and unresolvable issues lists
    :rtype: tuple[list[drain_swamp.lock_inspect.Resolvable], list[drain_swamp.lock_inspect.UnResolvable]]
    """
    if TYPE_CHECKING:
        t_out: tuple[PinsByPkg, PkgsWithIssues]
        locks_by_pkg_w_issues: PinsByPkg
        locks_pkg_by_versions: PkgsWithIssues
        d_qualifiers: dict[str, str]
        pins_current: list[Pin]
        unresolvables: list[UnResolvable]
        resolvables: list[Resolvable]

    # missing requirements --> MissingRequirementsFoldersFiles
    try:
        t_out = Pins.by_pkg_with_issues(loader, venv_path)
        locks_by_pkg_w_issues, locks_pkg_by_versions = t_out

        d_qualifiers = Pins.qualifiers_by_pkg(loader, venv_path)
        """Search thru .unlock file to identify current pins, but not
        source ``.in`` file."""
        pins_current = Pins(Pins.from_loader(loader, venv_path, suffix=SUFFIX_UNLOCKED))
    except MissingRequirementsFoldersFiles:
        raise

    unresolvables = []
    resolvables = []
    for pkg_name, d_ver_highest in locks_by_pkg_w_issues.items():
        # Without filtering, get qualifiers
        # pkg in .lock, but not in .unlock files
        str_pkg_qualifiers = d_qualifiers.get(pkg_name, "")

        nudge_pins = Pins.filter_pins_of_pkg(pins_current, pkg_name)
        highest = locks_pkg_by_versions[pkg_name]["highest"]
        others = locks_pkg_by_versions[pkg_name]["others"]

        # Create a set of all SpecifierSet
        set_ss = set()
        for pin in nudge_pins:
            # ss_pre = SpecifierSet(",".join(pin.specifiers), prereleases=True)
            ss_release = SpecifierSet(",".join(pin.specifiers))
            set_ss.add(ss_release)

        # Test highest
        if len(set_ss) == 0:
            found = highest
            is_ge = True
        else:
            is_highest_ok = all([highest in ss for ss in set_ss])
            if is_highest_ok:
                # highest satisfies all pins for this package
                found = highest
                is_ge = True
            else:
                # Get highest version within others that satisfies all pins
                found = None
                v_highest = None
                is_ge = False
                for v_other in others:
                    is_other_ok = all([v_other in ss for ss in set_ss])
                    if v_highest is None:
                        if is_other_ok:
                            v_highest = v_other
                            is_ge = True
                        else:  # pragma: no cover
                            pass
                    else:
                        if is_other_ok and v_other > v_highest:
                            v_highest = v_other
                            is_ge = False
                        else:  # pragma: no cover
                            pass
                found = v_highest
        str_operator = "==" if not is_ge else ">="

        if found is None:
            # unresolvable conflict --> warning
            unresolvables.append(
                UnResolvable(
                    venv_path,
                    pkg_name,
                    str_pkg_qualifiers,
                    set_ss,
                    highest,
                    others,
                    nudge_pins,
                )
            )
        else:
            # resolvable
            nudge_pin_unlock = f"{pkg_name}{str_operator}{found!s}"
            nudge_pin_lock = f"{pkg_name}=={found!s}"
            resolvables.append(
                Resolvable(
                    venv_path,
                    pkg_name,
                    str_pkg_qualifiers,
                    nudge_pin_unlock,
                    nudge_pin_lock,
                )
            )

    return resolvables, unresolvables


def write_to_file_nudge_pin(path_f: Path, pkg_name: str, nudge_pin_line: str) -> None:
    """Nudge pin must include a newline (os.linesep)
    If package line exists in file, overwrite. Otherwise append nudge pin line

    :param path_f:

       Absolute path to either a ``.unlock`` or ``.lock`` file. Only a
       comment if no preceding whitespace

    :type path_f: pathlib.Path
    :param pkg_name: Package name. Should be lowercase
    :type pkg_name: str
    :param nudge_pin_line:

       Format ``[package name][operator][version][qualifiers][os.linesep]``

    :type nudge_pin_line: str
    """
    with io.StringIO() as g:
        with open(path_f, mode="r", encoding="utf-8") as f:
            is_found = False
            for line in f:
                is_comment = line.startswith("#")
                if is_comment or pkg_name not in line:
                    g.writelines([line])
                else:
                    # found. Replace line rather than remove line
                    is_found = True
                    g.writelines([nudge_pin_line])
                    # If not replaced, append line
        if not is_found:
            g.writelines([nudge_pin_line])
        else:  # pragma: no cover
            pass
        contents = g.getvalue()
    # overwrites entire file
    path_f.write_text(contents)


def fix_resolvables(
    resolvables: Sequence[Resolvable],
    loader,
    venv_path,
    is_dry_run=False,
) -> tuple[list[str], list[tuple[str, Resolvable, Pin]]]:
    """Go thru resolvables and fix affected ``.unlock`` and ``.lock`` files

    Assumes target requirements file exists and is a file. This is a post processor. After
    .in, .unlock, and .lock files have been created.

    :param resolvables:

       Unordered list of Resolvable. Use to fix ``.unlock`` and ``.lock`` files

    :type resolvables: collections.abc.Sequence[drain_swamp.lock_inspect.Resolvable]
    :param loader: Contains some paths and loaded unparsed mappings
    :type loader: drain_swamp.pep518_venvs.VenvMapLoader
    :param venv_path: venv relative or absolute path
    :type venv_path: str
    :param is_dry_run:

       Default False. Should be a bool. Do not make changes. Merely
       report what would have been changed

    :type is_dry_run: typing.Any | None
    :returns:

       Wrote messages. For shared, tuple of suffix, resolvable, and Pin (of .lock file).
       This is why the suffix is provided and first within the tuple

    :rtype: tuple[list[drain_swamp.lock_inspect.ResolvedMsg], list[tuple[str, str, drain_swamp.lock_inspect.Resolvable, drain_swamp.lock_inspect.Pin]]]
    :raises:

       - :py:exc:`drain_swamp.exceptions.MissingRequirementsFoldersFiles` --
         one or more requirements files is missing

    """
    if TYPE_CHECKING:
        fixed_issues: list[ResolvedMsg]
        applies_to_shared: list[tuple[str, str, Resolvable, Pin]]

    if is_dry_run is None or not isinstance(is_dry_run, bool):
        is_dry_run = False
    else:  # pragma: no cover
        pass

    fixed_issues = []
    applies_to_shared = []

    # .lock **always** contains the package line
    # .unlock files may not contain the package line
    # Changing the ``.lock`` file will not affect this in-memory snapshot
    try:
        pins_lock = Pins(
            Pins.from_loader(
                loader,
                venv_path,
                suffix=SUFFIX_LOCKED,
                filter_by_pin=False,
            )
        )
    except MissingRequirementsFoldersFiles:
        raise

    # Query all requirements . Do both, but first, ``.lock``
    suffixes = (SUFFIX_LOCKED, SUFFIX_UNLOCKED)
    for suffix in suffixes:
        is_unlock = suffix == SUFFIX_UNLOCKED

        for resolvable in resolvables:
            # Deal with fixing one venv at a time
            if resolvable.venv_path == venv_path:
                # Potential affected files
                for pin in pins_lock:
                    path_f = pin.file_abspath
                    is_shared_type = is_shared(path_f.name)

                    if is_unlock:
                        path_f = replace_suffixes_last(path_f, SUFFIX_UNLOCKED)
                    else:  # pragma: no cover
                        pass

                    is_match = pin.pkg_name == resolvable.pkg_name
                    if is_match:
                        if is_shared_type:
                            """``.shared.*`` files affect multiple venv.
                            Nudge pin takes into account one venv. Inform
                            the human"""
                            applies_to_shared.append(
                                (venv_path, suffix, resolvable, pin)
                            )
                        else:
                            # remove any line dealing with this package
                            # append resolvable.nudge_unlock
                            if is_unlock:
                                nudge = resolvable.nudge_unlock
                            else:
                                nudge = resolvable.nudge_lock
                            nudge_pin_line = (
                                f"{nudge}{resolvable.qualifiers}{os.linesep}"
                            )

                            if not is_dry_run:
                                write_to_file_nudge_pin(
                                    path_f, pin.pkg_name, nudge_pin_line
                                )
                            else:  # pragma: no cover
                                pass

                            msg_fixed = ResolvedMsg(
                                venv_path, path_f, nudge_pin_line.rstrip()
                            )
                            fixed_issues.append(msg_fixed)
                    else:  # pragma: no cover
                        pass
            else:  # pragma: no cover
                pass

    return fixed_issues, applies_to_shared


def fix_requirements(loader, venv_relpath, is_dry_run=False):
    """Iterate thru venv. Treat .unlock / .lock as a pair. Fix
    requirements files pair(s).

    :param loader: Contains some paths and loaded unparsed mappings
    :type loader: drain_swamp.pep518_venvs.VenvMapLoader
    :param venv_relpath: venv relative path is a key. To choose a tools.venvs.req
    :type venv_relpath: str
    :param is_dry_run:

       Default False. Should be a bool. Do not make changes. Merely
       report what would have been changed

    :type is_dry_run: typing.Any | None
    :returns:

       list contains tuples. venv path, resolves messages, unresolvable
       issues, resolvable3 issues dealing with .shared requirements file

    :rtype: tuple[dict[str, ResolvedMsg], dict[str, UnResolvable], dict[str, tuple[str, drain_swamp.lock_inspect.Resolvable, drain_swamp.lock_inspect.Pin]]]
    :raises:

       - :py:exc:`NotADirectoryError` -- there is no cooresponding venv folder. Create it

       - :py:exc:`ValueError` -- expecting [[tool.venvs]] field reqs should be a
         list of relative path without .in .unlock or .lock suffix

       - :py:exc:`drain_swamp.exceptions.MissingRequirementsFoldersFiles` --
         missing constraints or requirements files or folders

    """
    if is_dry_run is None or not isinstance(is_dry_run, bool):
        is_dry_run = False
    else:
        pass

    d_resolved_msgs = {}
    d_unresolvables = {}
    d_resolvable_shared = {}

    try:
        VenvMap(loader)
    except (NotADirectoryError, ValueError):
        raise

    if is_ok(venv_relpath):
        # One
        venv_relpaths = [venv_relpath]
    else:
        # All
        venv_relpaths = loader.venv_relpaths

    # Do once per venv, not (venv * reqs) times
    """
    set_venv_relpaths = set()
    for venv_req in venv_map:
        venv_relpath = venv_req.venv_relpath
        set_venv_relpaths.add(venv_relpath)
    """
    pass

    for venv_relpath_tmp in venv_relpaths:

        """For a particular venv, get list of resolvable and unresolvable
        dependency conflicts"""
        try:
            t_actionable = get_issues(loader, venv_relpath_tmp)
            lst_resolvable, lst_unresolvable = t_actionable
        except MissingRequirementsFoldersFiles:
            # Missing constraints or requirements files
            raise

        """Resolve the resolvable dependency conflicts. Refrain from attempting to
        fix resolvable conflicts involving .shared requirements files."""
        t_results = fix_resolvables(
            lst_resolvable,
            loader,
            venv_relpath_tmp,
            is_dry_run=is_dry_run,
        )
        fixed_issues, applies_to_shared = t_results

        # group by venv -- resolved_msgs
        d_resolved_msgs[venv_relpath_tmp] = fixed_issues

        # group by venv -- unresolvables
        d_unresolvables[venv_relpath_tmp] = lst_unresolvable

        # group by venv -- resolvable .shared
        #     venv_path, suffix (.unlock or .lock), resolvable, pin
        resolvable_shared_filtered = []
        for t_resolvable_shared in applies_to_shared:
            resolvable_shared_filtered.append(t_resolvable_shared[1:])
        d_resolvable_shared[venv_relpath] = resolvable_shared_filtered

    return d_resolved_msgs, d_unresolvables, d_resolvable_shared


def filter_by_venv_relpath(loader, venv_current_relpath):
    """Facilitate call more than once

    Could do all in one shot by supplying :code:`venv_path=None`

    :param loader: Contains some paths and loaded unparsed mappings
    :type loader: drain_swamp.pep518_venvs.VenvMapLoader
    :param venv_current_relpath:

       A venv relative path. Is a dict key so shouldn't be an absolute path

    :type venv_current_relpath: str | None
    :returns: Container of InFile
    :rtype: tuple[tuple[pathlib.Path], drain_swamp.lock_infile.InFiles]
    :raises:

       - :py:exc:`drain_swamp.exceptions.MissingRequirementsFoldersFiles` --
         Missing requirements files or folders

       - :py:exc:`NotADirectoryError` -- venv base folder not found

       - :py:exc:`ValueError` -- InFiles constructor expecting 2nd arg to be a Sequence

       - :py:exc:`KeyError` -- venv relative path no matches. Check
         pyproject.toml tool.venvs.reqs

    """
    path_cwd = loader.project_base
    try:
        # Implementation specific
        t_abspath_in = get_reqs(loader, venv_path=venv_current_relpath)
        # Generic
        files = InFiles(path_cwd, t_abspath_in)
        files.resolution_loop()
    except MissingRequirementsFoldersFiles:
        raise
    except (NotADirectoryError, ValueError, KeyError):
        raise

    return t_abspath_in, files


def unlock_compile(loader, venv_relpath):
    """``.in`` requirement files can contain ``-r`` and ``-c`` lines.
    Relative path to requirement files and constraint files respectively.

    Originally thought ``-c`` was a :command:`pip-compile` convention,
    not a pip convention. Opps!

    Resolve the ``-r`` and ``-c`` to create ``.unlock`` file

    package dependencies

    - For a package which is an app, lock them.

    - For a normal package, always must be unlocked.

    optional dependencies

    - additional feature --> leave unlocked

    - For develop environment --> lock them

    :param loader: Contains some paths and loaded unparsed mappings
    :type loader: drain_swamp.pep518_venvs.VenvMapLoader
    :param venv_relpath: venv relative path is a key. To choose a tools.venvs.req
    :type venv_relpath: str
    :returns: Generator of abs path to .unlock files
    :rtype: collections.abc.Generator[pathlib.Path, None, None]
    """
    if is_ok(venv_relpath):
        # Only one venv
        _, files = filter_by_venv_relpath(loader, venv_relpath)
        gen = files.write()
        lst_called = list(gen)
        for abspath in lst_called:
            assert abspath.exists() and abspath.is_file()

        yield from lst_called
    else:
        # All venv (w/o filtering)
        for venv_path in loader.venv_relpaths:
            _, files = filter_by_venv_relpath(loader, venv_path)
            gen = files.write()
            lst_called = list(gen)
            for abspath in lst_called:
                assert abspath.exists() and abspath.is_file()

            yield from lst_called

    yield from ()


def _compile_one(
    in_abspath,
    lock_abspath,
    ep_path,
    path_cwd,
    context=None,
    timeout=15,
):
    """Run subprocess to compile ``.in`` --> ``.lock``.

    Serial, it's what's for breakfast

    :param in_abspath: ``.in`` file absolute path
    :type in_abspath: str
    :param lock_abspath: output absolute path. Should have ``.lock`` last suffix
    :type lock_abspath: str
    :param ep_path: Absolute path to binary executable
    :type ep_path: str
    :param path_cwd: package base folder absolute Path
    :type path_cwd: pathlib.Path
    :param context: Venv path context. Which venv compiling .lock for
    :type context: str | None
    :param timeout: Default 15. Give ``pip --timeout`` in seconds
    :type timeout: typing.Any
    :returns:

       On success, Path to ``.lock`` file otherwise None. 2nd is error
       and exception details

    :rtype: tuple[pathlib.Path | None, None | str]
    """
    dotted_path = f"{g_app_name}.lock_inspect._compile_one"

    if timeout is None or not isinstance(timeout, int):
        timeout = 15
    else:  # pragma: no cover
        pass

    cmd = (
        ep_path,
        "--allow-unsafe",
        "--no-header",
        "--resolver",
        "backtracking",
        f"--pip-args '--timeout={timeout!s}'",
        "-o",
        lock_abspath,
        in_abspath,
    )

    if is_module_debug:  # pragma: no cover
        msg_info = f"{dotted_path} ({context}) cmd: {cmd}"
        _logger.info(msg_info)
    else:  # pragma: no cover
        pass

    t_ret = run_cmd(cmd, cwd=path_cwd)
    _, err, exit_code, exc = t_ret

    if exit_code != 0:  # pragma: no cover
        """timeout error message

        WARNING: Retrying (Retry(total=4, connect=None, read=None, redirect=None,
        status=None)) after connection broken by 'NewConnectionError('
        <pip._vendor.urllib3.connection.HTTPSConnection object at 0x7fe86a05d670>:
        Failed to establish a new connection: [Errno -3] Temporary failure
        in name resolution')': /simple/pip-tools/

        Search for ``Failed to establish a new connection`` to detect timeouts
        """
        err = err.lstrip()
        if exit_code == 1 and "Failed to establish a new connection" in err:
            err = "timeout (15s)"
            err_details = err
        else:
            err_details = f"{err}{os.linesep}{exc}"
            msg_warn = (
                f"{dotted_path} ({context}) {cmd!r} exit code "
                f"{exit_code} {err} {exc}"
            )
            _logger.warning(msg_warn)
    else:  # pragma: no cover
        err_details = None

    path_out = Path(lock_abspath)
    is_confirm = path_out.exists() and path_out.is_file()
    if is_confirm:
        if is_module_debug:  # pragma: no cover
            msg_info = f"{dotted_path} ({context}) yield: {path_out!s}"
            _logger.info(msg_info)
        else:  # pragma: no cover
            msg_warn = f"{dotted_path} ({context}) .lock created: {path_out!s}"
            _logger.warning(msg_warn)

        # abspath --> relpath
        _postprocess_abspath_to_relpath(path_out, path_cwd)

        ret = path_out, err_details
    else:
        """File not created. ``.in`` file contained errors that needs
        to be fixed. Log info adds context. Gives explanation about consequences
        """
        if is_module_debug:  # pragma: no cover
            msg_info = (
                f"{dotted_path} ({context}) {in_abspath} malformed. "
                f"pip-compile did not create: {path_out!s}."
            )
            _logger.info(msg_info)
        else:  # pragma: no cover
            pass
        ret = None, err_details

    return ret


@singledispatch
def prepare_pairs(t_ins):
    """Fallback for unsupported data types without implementations

    Do not add type annotations. It's correct as-is.

    :raises:

       - :py:exc:`NotImplementedError` -- No implementation for 1st arg unsupported type

    """
    msg_warn = f"No implemenatation for type {t_ins}"
    raise NotImplementedError(msg_warn)


@prepare_pairs.register(tuple)
def _(t_ins: tuple[Path]):
    """Prepare (.in .lock pairs) of only the direct requirements,
    not the support files.

    :param t_ins: Absolute path of the requirement ``.in`` file(s)
    :type t_ins: tuple[pathlib.Path]
    :returns: Yield .in .lock pairs. Absolute paths.
    :rtype: collections.abc.Generator[tuple[str, str], None, None]
    """
    for abspath_in in t_ins:
        abspath_locked = replace_suffixes_last(abspath_in, SUFFIX_LOCKED)
        yield str(abspath_in), str(abspath_locked)
    yield from ()


@prepare_pairs.register
def _(in_files: InFiles, path_cwd=None):
    """This would prepare (.in .lock pairs), not only for the reqs,
    but also the support files. Compiling the support files is not needed.

    But here is how to do that.

    :param in_files:

       Requirements. After resolution_loop, so contains both reqs and support files

    :type in_files: drain_swamp.lock_infile.InFiles
    :param path_cwd: cwd so can get the requirement file's absolute path
    :type path_cwd: pathlib.Path | None
    :returns: Yield .in .lock pairs. Absolute paths.
    :rtype: collections.abc.Generator[tuple[str, str], None, None]
    """
    assert path_cwd is not None and issubclass(type(path_cwd), PurePath)
    gen = in_files.zeroes
    for in_ in gen:
        abspath_in = in_.abspath(path_cwd)
        abspath_locked = replace_suffixes_last(abspath_in, SUFFIX_LOCKED)

        yield str(abspath_in), str(abspath_locked)
    yield from ()


def lock_compile(loader, venv_relpath, timeout=15):
    """In a subprocess, call :command:`pip-compile` to create ``.lock`` files

    :param loader: Contains some paths and loaded unparsed mappings
    :type loader: drain_swamp.pep518_venvs.VenvMapLoader
    :param venv_relpath: venv relative path is a key. To choose a tools.venvs.req
    :type venv_relpath: str
    :param timeout: Default 15. Give ``pip --timeout`` in seconds
    :type timeout: typing.Any
    :returns: Generator of abs path to .lock files
    :rtype: tuple[tuple[str, ...], tuple[str, ...]]
    :raises:

       - :py:exc:`AssertionError` -- package pip-tools is not installed

    """
    dotted_path = f"{g_app_name}.lock_inspect.lock_compile"
    is_installed = is_package_installed("pip-tools")
    path_ep = resolve_path("pip-compile")
    assert is_installed is True and path_ep is not None
    ep_path = str(path_ep)

    if timeout is None or not isinstance(timeout, int):
        timeout = 15
    else:  # pragma: no cover
        pass

    path_cwd = loader.project_base

    compiled = []
    failures = []

    if is_ok(venv_relpath):
        # One
        venv_relpaths = [venv_relpath]
    else:
        # All
        venv_relpaths = loader.venv_relpaths

    for venv_relpath_tmp in venv_relpaths:
        context = venv_relpath_tmp
        t_ins, files = filter_by_venv_relpath(loader, venv_relpath_tmp)
        gen_pairs = prepare_pairs(t_ins)
        pairs = list(gen_pairs)

        if is_module_debug:  # pragma: no cover
            msg_info = f"{dotted_path} pairs {pairs!r}"
            _logger.info(msg_info)
        else:  # pragma: no cover
            pass

        for in_abspath, lock_abspath in pairs:
            # Conforms to interface?
            assert isinstance(in_abspath, str)
            assert isinstance(lock_abspath, str)
            assert isinstance(ep_path, str)
            assert issubclass(type(path_cwd), PurePath)
            assert context is None or isinstance(context, str)

            if is_module_debug:  # pragma: no cover
                msg_info = (
                    f"{dotted_path} _compile_one (before) cwd {path_cwd} "
                    f"binary {ep_path} {in_abspath} {lock_abspath}"
                )
                _logger.info(msg_info)
            else:  # pragma: no cover
                pass

            optabspath_lock, err_details = _compile_one(
                in_abspath,
                lock_abspath,
                ep_path,
                path_cwd,
                context=context,
                timeout=timeout,
            )
            # if timeout cannot add to compiled. If no timeout, maybe failures empty
            if optabspath_lock is None:  # pragma: no cover
                msg = f"venv {venv_relpath_tmp} {lock_abspath} {err_details}"
                lst_alias = failures
            else:  # pragma: no cover
                # Path
                msg = lock_abspath
                lst_alias = compiled
            lst_alias.append(msg)

    return (tuple(compiled), tuple(failures))


def is_timeout(failures):
    """lock_compile returns both success and failures. Detect
    if the cause of the failure was timeout(s)

    :param failures: Sequence of verbose error message and traceback
    :type failures: tuple[str, ...]
    :returns: True if web (actually SSL) connection timeout occurred
    :rtype: bool
    """
    if len(failures) != 0:  # pragma: no cover
        failure_0 = failures[0]
        is_timeout = re.search("timeout.+s", failure_0)
    else:  # pragma: no cover
        is_timeout = False

    return is_timeout


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
