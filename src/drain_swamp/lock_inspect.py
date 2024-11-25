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
   :type: dict[str, set[drain_swamp.lock_datum.Pin]]
   :noindex:

   dict of package name by set of Pins or locks. ``.unlock`` contains pin.
   ``.lock`` contain locks. Both are stored as Pin

"""

from __future__ import annotations

import logging
import os
import sys
from collections.abc import (
    Iterator,
    MutableSet,
    Sequence,
)
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    TypeVar,
)

from .check_type import is_ok
from .constants import (
    SUFFIX_LOCKED,
    SUFFIX_UNLOCKED,
    g_app_name,
)
from .exceptions import MissingRequirementsFoldersFiles
from .lock_datum import (  # noqa: F401
    DATUM,
    Pin,
)
from .lock_discrepancy import (
    PkgsWithIssues,
    Resolvable,
    ResolvedMsg,
    UnResolvable,
    has_discrepancies_version,
    tunnel_blindness_suffer_chooses,
    write_to_file_nudge_pin,
)
from .lock_infile import InFiles
from .lock_loader import LoaderPinDatum
from .lock_util import (
    is_shared,
    replace_suffixes_last,
)
from .pep518_venvs import (
    VenvMap,
    get_reqs,
)

# Use dataclasses slots True for reduced memory usage and performance gain
if sys.version_info >= (3, 10):  # pragma: no cover py-gte-310-else
    DC_SLOTS = {"slots": True}
else:  # pragma: no cover py-gte-310
    DC_SLOTS = {}

is_module_debug = False
_logger = logging.getLogger(f"{g_app_name}.lock_inspect")


PinsByPkg = dict[str, list[Pin]]

_T = TypeVar("_T", bound=Pin)


class Pins(MutableSet[_T]):
    """Pin container.

    Call execution map (LoaderPinDatum):

    get_issues --> Pins.by_pkg --> _wrapper_pins_by_pkg (calls LoaderPinDatum[SUFFIX_LOCKED]) --> Pins.subset_req
               --> by_pkg_with_issues
                   --> Pins.by_pkg (SUFFIX_LOCKED)
                   --> Pins.has_discrepancies (across one venv .lock files)
               --> qualifiers_by_pkg --> Pins.by_pkg[SUFFIX_UNLOCKED]
               --> Pins.filter_pins_of_pkg
               --> (calls LoaderPinDatum[SUFFIX_UNLOCKED])

    fix_requirements --> get_issues (calls LoaderPinDatum[SUFFIX_UNLOCKED])
                     --> fix_resolvables (
                         calls LoaderPinDatum[SUFFIX_LOCKED];
                         does fixing of .lock;
                         calls write_to_file_nudge_pin)

    unlock_compile
    lock_compile --> filter_by_venv_relpath (resolution loop) --> get_reqs (suffix_last=SUFFIX_IN)
                 --> _compile_one (create lock file)

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

        :rtype: tuple[drain_swamp.lock_inspect.PinsByPkg, drain_swamp.lock_discrepancy.PkgsWithIssues]
        """
        # Organize pins by package name
        locks_by_pkg = Pins.by_pkg(loader, venv_path)

        # Search thru ``.lock`` files for discrepancies
        d_pkg_by_vers = has_discrepancies_version(locks_by_pkg)

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
    def filter_pins_of_pkg(pins_current, pkg_name):
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
        set_pins = LoaderPinDatum()(
            loader,
            venv_path,
            suffix=suffix,
            filter_by_pin=filter_by_pin,
        )
        pins_locks = Pins(set_pins)
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


def get_issues(loader, venv_path):
    """Look thru all the packages with discrepanies. Which have existing
    nudge(s). Find where those nudges are in the ``.in`` files.

    Replace or add as appropriate

    :param loader: Contains some paths and loaded unparsed mappings
    :type loader: drain_swamp.pep518_venvs.VenvMapLoader
    :param venv_path: venv relative or absolute path
    :type venv_path: str
    :returns: Resolvable and unresolvable issues lists
    :rtype: tuple[list[drain_swamp.lock_discrepancy.Resolvable], list[drain_swamp.lock_discrepancy.UnResolvable]]
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
        set_pins = LoaderPinDatum()(
            loader,
            venv_path,
            suffix=SUFFIX_UNLOCKED,
        )
        pins_current = Pins(set_pins)
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

        t_chosen = tunnel_blindness_suffer_chooses(
            nudge_pins,
            highest,
            others,
        )
        assert isinstance(t_chosen, tuple)
        set_ss, str_operator, found = t_chosen

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


def fix_resolvables(
    resolvables,
    loader,
    venv_path,
    is_dry_run=False,
):
    """Go thru resolvables and fix affected ``.unlock`` and ``.lock`` files

    Assumes target requirements file exists and is a file. This is a post processor. After
    .in, .unlock, and .lock files have been created.

    :param resolvables:

       Unordered list of Resolvable. Use to fix ``.unlock`` and ``.lock`` files

    :type resolvables: collections.abc.Sequence[drain_swamp.lock_discrepancy.Resolvable]
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

    :rtype: tuple[list[drain_swamp.lock_discrepancy.ResolvedMsg], list[tuple[str, str, drain_swamp.lock_discrepancy.Resolvable, drain_swamp.lock_datum.Pin]]]
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
        set_pins = LoaderPinDatum()(
            loader,
            venv_path,
            suffix=SUFFIX_LOCKED,
            filter_by_pin=False,
        )
        pins_lock = Pins(set_pins)
    except MissingRequirementsFoldersFiles:
        raise

    """
    if is_module_debug:  # pragma: no cover
        msg_info = f"{mod_path} pins_lock: {pins_lock}"
        _logger.info(msg_info)
    else:  # pragma: no cover
        pass
    """
    pass

    # Limit resolvables to a single venv
    resolvables_one_venv = [
        resolvable for resolvable in resolvables if resolvable.venv_path == venv_path
    ]

    # Query all requirements . Do both, but first, ``.lock``
    suffixes = (SUFFIX_LOCKED, SUFFIX_UNLOCKED)
    for resolvable in resolvables_one_venv:
        # Potential affected files
        for pin in pins_lock:
            is_shared_type = is_shared(pin.file_abspath.name)
            is_match = pin.pkg_name == resolvable.pkg_name
            if not is_match:  # pragma: no cover
                pass
            else:
                for suffix in suffixes:
                    # In ``suffixes`` tuple, lock is first entry
                    is_lock = suffix == SUFFIX_LOCKED
                    if is_lock:
                        path_f = pin.file_abspath
                    else:
                        path_f = replace_suffixes_last(
                            pin.file_abspath,
                            SUFFIX_UNLOCKED,
                        )

                    if is_shared_type:
                        """``.shared.*`` files affect multiple venv.
                        Nudge pin takes into account one venv. Inform
                        the human"""
                        if is_lock:
                            # One entry rather than two.
                            # Implied affects both .unlock and .lock
                            applies_to_shared.append(
                                (venv_path, suffix, resolvable, pin)
                            )
                        else:  # pragma: no cover
                            pass
                    else:
                        # remove any line dealing with this package
                        # append resolvable.nudge_unlock
                        if is_lock:
                            nudge = resolvable.nudge_lock
                        else:
                            nudge = resolvable.nudge_unlock

                        nudge_pin_line = f"{nudge}{resolvable.qualifiers}{os.linesep}"

                        if not is_dry_run:
                            write_to_file_nudge_pin(
                                path_f, pin.pkg_name, nudge_pin_line
                            )
                        else:  # pragma: no cover
                            pass

                        # Report resolved dependency conflict
                        msg_fixed = ResolvedMsg(
                            venv_path, path_f, nudge_pin_line.rstrip()
                        )
                        fixed_issues.append(msg_fixed)

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

    :rtype: tuple[dict[str, drain_swamp.lock_discrepancy.ResolvedMsg], dict[str, drain_swamp.lock_discrepancy.UnResolvable], dict[str, tuple[str, drain_swamp.lock_discrepancy.Resolvable, drain_swamp.lock_datum.Pin]]]
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
