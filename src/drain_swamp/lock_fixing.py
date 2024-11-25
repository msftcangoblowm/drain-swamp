"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

.. py:data:: is_module_debug
   :type: bool
   :value: False

   Switch on/off module level debugging

.. py:data:: _logger
   :type: logging.Logger

   Module level logger

"""

import logging
import os
from pprint import pprint
from typing import TYPE_CHECKING

from .check_type import is_ok
from .constants import (
    SUFFIX_LOCKED,
    SUFFIX_UNLOCKED,
    g_app_name,
)
from .exceptions import MissingRequirementsFoldersFiles
from .lock_collections import Ins
from .lock_datum import (
    Pin,
    PinDatum,
)
from .lock_discrepancy import (
    Resolvable,
    ResolvedMsg,
    UnResolvable,
    has_discrepancies_version,
    tunnel_blindness_suffer_chooses,
    write_to_file_nudge_pin,
)
from .lock_util import (
    is_shared,
    replace_suffixes_last,
)
from .pep518_venvs import (
    VenvMap,
    VenvMapLoader,
    check_loader,
)

if TYPE_CHECKING:
    from .lock_datum import DatumByPkg
    from .lock_discrepancy import PkgsWithIssues

is_module_debug = True
_logger = logging.getLogger(f"{g_app_name}.lock_fixing")


def _get_qualifiers(d_subset):
    """Given package name, choose qualifiers

    :param d_subset: key is package name value is set of datum
    :type d_subset: drain_swamp.lock_datum.DatumByPkg
    :returns: dict of package name and qualifiers joined into one str
    :rtype: dict[str, str]
    """
    d_pkg_qualifiers = {}
    for pkg_name, pindatum_in in d_subset.items():
        for pin in pindatum_in:
            # Does this pin have qualifiers?
            quals = pin.qualifiers
            has_quals = len(quals) != 0
            if pkg_name not in d_pkg_qualifiers.keys() and has_quals:
                str_pkg_qualifiers = "; ".join(quals)
                str_pkg_qualifiers = f"; {str_pkg_qualifiers}"
                d_pkg_qualifiers[pkg_name] = str_pkg_qualifiers
            else:  # pragma: no cover
                pass

        # empty str for a package without qualifiers
        if pkg_name not in d_pkg_qualifiers.keys():
            d_pkg_qualifiers[pkg_name] = ""
        else:  # pragma: no cover
            pass

    return d_pkg_qualifiers


def _load_once(
    ins,
    locks,
    venv_relpath,
):
    """Cache .in and .lock files

    :param ins: Collection of FilePins. ``.in`` files
    :type ins: drain_swamp.lock_collections.Ins
    :param locks: Collection of FilePins.  ``.lock`` files
    :type locks: drain_swamp.lock_collections.Ins
    :param venv_relpath: venv relative path
    :type venv_relpath: str
    :returns: list of resolvables and list of unresolvables
    :rtype: tuple[list[Resolvable], list[UnResolvable]]
    """
    if TYPE_CHECKING:
        d_subset_notables: DatumByPkg
        d_subset_all_in: DatumByPkg
        d_subset_all_lock: DatumByPkg
        locks_pkg_by_versions: PkgsWithIssues
        locks_by_pkg_w_issues: DatumByPkg
        d_qualifiers_in: dict[str, str]
        d_qualifiers_lock: dict[str, str]
        set_datum: set[Pin | PinDatum]

    # dotted_path = f"{g_app_name}.lock_fixing._load_once"
    """REMOVE duplicates from same requirements file.
    Use ``dict[str, set[PinDatum]]``, not a ``dict[str, list[PinDatum]]``
    Mimics lock_inspect.Pins._wrapper_pins_by_pkg
    """
    # Group notable locks (PinDatum) by pkg_name --> PinsByPkg
    d_subset_notables = {}
    gen_fpins_zeroes = ins.zeroes
    for fpin_zero in gen_fpins_zeroes:
        for pindatum_lock_notable in fpin_zero.by_pin_or_qualifier():
            pkg_name = pindatum_lock_notable.pkg_name
            is_not_in = pkg_name not in d_subset_notables.keys()
            if is_not_in:
                # add first PinDatum
                set_new = set()
                set_new.add(pindatum_lock_notable)
                d_subset_notables.update({pkg_name: set_new})
            else:
                set_pindatums = d_subset_notables[pkg_name]
                set_pindatums.add(pindatum_lock_notable)
                d_subset_notables.update({pkg_name: set_pindatums})

    # Group all ins (PinDatum) by pkg_name
    d_subset_all_in = {}
    gen_fpins_zeroes = ins.zeroes
    for fpin_zero in gen_fpins_zeroes:
        # From FilePins --> list[PinDatum]
        for pindatum_lock in fpin_zero._pins:
            pkg_name = pindatum_lock.pkg_name
            is_not_in = pkg_name not in d_subset_all_in.keys()
            if is_not_in:
                # add first PinDatum
                set_new = set()
                set_new.add(pindatum_lock)
                d_subset_all_in.update({pkg_name: set_new})
            else:
                set_pindatums = d_subset_all_in[pkg_name]
                set_pindatums.add(pindatum_lock)
                d_subset_all_in.update({pkg_name: set_pindatums})

    """ Group all locks (PinDatum) by pkg_name
    ONLY LOCK CAN CORRECTLY IDENTIFY ALL PACKAGES
    """
    d_subset_all_lock = {}
    gen_fpins_zeroes = locks._file_pins
    for fpin_zero in gen_fpins_zeroes:
        # From FilePins --> list[PinDatum]
        for pindatum_lock in fpin_zero._pins:
            pkg_name = pindatum_lock.pkg_name
            is_not_in = pkg_name not in d_subset_all_lock.keys()
            if is_not_in:
                # add first PinDatum
                set_new = set()
                set_new.add(pindatum_lock)
                d_subset_all_lock.update({pkg_name: set_new})
            else:
                set_pindatums = d_subset_all_lock[pkg_name]
                set_pindatums.add(pindatum_lock)
                d_subset_all_lock.update({pkg_name: set_pindatums})

    """In .lock files search for version discrepencies
    See lock_inspect.Pins.by_pkg_with_issues
    """
    locks_pkg_by_versions = has_discrepancies_version(d_subset_all_lock)

    """filter out packages without issues

    locks_pkg_by_versions contains all .lock package issues
    Search thru the resolved .in, but still will contain less packages"""
    locks_by_pkg_w_issues = {
        k: v for k, v in d_subset_notables.items() if k in locks_pkg_by_versions.keys()
    }

    """Pure ``.lock`` version discrepancies. Dependency not found
    in ``.in``. Need to be fix in ``.lock`` files"""
    locks_by_pkg_w_issues_remaining = {
        k: v
        for k, v in d_subset_all_lock.items()
        if k in locks_pkg_by_versions.keys() and k not in locks_by_pkg_w_issues.keys()
    }

    # lock_inspect.get_issues --> lock_inspect.Pins.qualifiers_by_pkg
    #    From d_subset_notables (filtered .in files)
    d_qualifiers_in = _get_qualifiers(d_subset_notables)

    # from .lock file, get package qualifiers (dict key, pkg_name)
    d_qualifiers_lock = _get_qualifiers(d_subset_all_lock)

    unresolvables = []
    resolvables = []

    # get_issues -- no corresponding pin in .in file
    # Pure .lock package dependency conflict
    for pkg_name, set_datum in locks_by_pkg_w_issues_remaining.items():
        str_pkg_qualifiers = d_qualifiers_lock[pkg_name]

        # Choose highest
        highest = locks_pkg_by_versions[pkg_name]["highest"]
        #    N/A only dealing with .lock files
        nudge_pin_unlock = None
        nudge_pin_lock = f"{pkg_name}=={highest!s}"

        resolvables.append(
            Resolvable(
                venv_relpath,
                pkg_name,
                str_pkg_qualifiers,
                nudge_pin_unlock,
                nudge_pin_lock,
            )
        )

    # get_issues -- corresponding pin in .in file
    for pkg_name, set_datum in locks_by_pkg_w_issues.items():
        # Without filtering, get qualifiers from .in files
        str_pkg_qualifiers = d_qualifiers_in.get(pkg_name, "")
        # Pins.filter_pins_of_pkg
        #     nudge_pins must come from .in
        set_pindatum = d_subset_all_in[pkg_name]
        highest = locks_pkg_by_versions[pkg_name]["highest"]
        others = locks_pkg_by_versions[pkg_name]["others"]

        t_chosen = tunnel_blindness_suffer_chooses(
            set_pindatum,
            highest,
            others,
        )
        assert isinstance(t_chosen, tuple)
        set_ss, str_operator, found = t_chosen

        if found is None:
            # unresolvable conflict --> warning
            unresolvables.append(
                UnResolvable(
                    venv_relpath,
                    pkg_name,
                    str_pkg_qualifiers,
                    set_ss,
                    highest,
                    others,
                    set_pindatum,
                )
            )
        else:
            # resolvable
            nudge_pin_unlock = f"{pkg_name}{str_operator}{found!s}"
            nudge_pin_lock = f"{pkg_name}=={found!s}"
            resolvables.append(
                Resolvable(
                    venv_relpath,
                    pkg_name,
                    str_pkg_qualifiers,
                    nudge_pin_unlock,
                    nudge_pin_lock,
                )
            )

    t_ret = resolvables, unresolvables

    return t_ret


def _fix_resolvables(
    resolvables,
    locks: Ins,
    venv_relpath,
    is_dry_run=False,
    suffixes=(SUFFIX_LOCKED,),
):
    """Go thru resolvables and fix affected ``.unlock`` and ``.lock`` files

    Assumes target requirements file exists and is a file. This is a post processor. After
    .in, .unlock, and .lock files have been created.

    :param resolvables:

       Unordered list of Resolvable. Use to fix ``.unlock`` and ``.lock`` files

    :type resolvables: collections.abc.Sequence[drain_swamp.lock_inspect.Resolvable]
    :param locks: .lock file PinDatum collection
    :type locks: drain_swamp.lock_collections.Ins
    :param venv_relpath: venv relative path
    :type venv_relpath: str
    :param is_dry_run:

       Default False. Should be a bool. Do not make changes. Merely
       report what would have been changed

    :type is_dry_run: typing.Any | None
    :param suffixes:

       Default ``(".lock",)``. Suffixes to process, in order

    :type suffixes: tuple[typing.Literal[drain_swamp.constants.SUFFIX_LOCKED] | typing.Literal[drain_swamp.constants.SUFFIX_UNLOCKED]]
    :returns:

       Wrote messages. For shared, tuple of suffix, resolvable, and Pin (of .lock file).
       This is why the suffix is provided and first within the tuple

    :rtype: tuple[list[drain_swamp.lock_inspect.ResolvedMsg], list[tuple[str, str, drain_swamp.lock_inspect.Resolvable, drain_swamp.lock_datum.Pin]]]
    :raises:

       - :py:exc:`drain_swamp.exceptions.MissingRequirementsFoldersFiles` --
         one or more requirements files is missing

    """
    if TYPE_CHECKING:
        fixed_issues: list[ResolvedMsg]
        applies_to_shared: list[tuple[str, str, Resolvable, Pin]]

    is_dry_run_ng = is_dry_run is None or not isinstance(is_dry_run, bool)
    if is_dry_run_ng:
        is_dry_run = False
    else:  # pragma: no cover
        pass

    if suffixes is None or not (
        SUFFIX_LOCKED in suffixes or SUFFIX_UNLOCKED in suffixes
    ):
        # Query all requirements . Do both, but first, ``.lock``
        suffixes = (SUFFIX_LOCKED,)
    else:  # pragma: no cover
        pass

    fixed_issues = []
    applies_to_shared = []

    gen_fpins_zeroes = locks._file_pins
    for fpin_zero in gen_fpins_zeroes:
        # From FilePins --> list[PinDatum]
        for pindatum_lock in fpin_zero._pins:
            pkg_name = pindatum_lock.pkg_name
            is_shared_type = is_shared(pindatum_lock.file_abspath.name)
            for resolvable in resolvables:
                is_match = pkg_name == resolvable.pkg_name
                if not is_match:  # pragma: no cover
                    pass
                else:
                    for suffix in suffixes:
                        # In ``suffixes`` tuple, lock is first entry
                        is_lock = suffix == SUFFIX_LOCKED
                        if is_lock:
                            path_f = pindatum_lock.file_abspath
                        else:
                            path_f = replace_suffixes_last(
                                pindatum_lock.file_abspath,
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
                                    (venv_relpath, suffix, resolvable, pindatum_lock)
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

                            nudge_pin_line = (
                                f"{nudge}{resolvable.qualifiers}{os.linesep}"
                            )

                            if not is_dry_run:
                                write_to_file_nudge_pin(
                                    path_f, pindatum_lock.pkg_name, nudge_pin_line
                                )
                            else:
                                pass

                            # Report resolved dependency conflict
                            msg_fixed = ResolvedMsg(
                                venv_relpath, path_f, nudge_pin_line.rstrip()
                            )
                            fixed_issues.append(msg_fixed)

    return fixed_issues, applies_to_shared


class Fixing:
    """Fix ``.lock`` files using only ``.in`` files. Assume ``.unlock``
    do not exist or are wrong.

    :raises:

       - :py:exc:`TypeError` -- unsupported type for venv_relpath expects str

       - :py:exc:`NotADirectoryError` -- there is no cooresponding venv folder. Create it

       - :py:exc:`ValueError` -- expecting [[tool.venvs]] field reqs should be a
         list of relative path without .in .unlock or .lock suffix

       - :py:exc:`drain_swamp.exceptions.MissingRequirementsFoldersFiles` --
         there are unresolvable constraint(s)

    """

    _ins: Ins
    _locks: Ins
    _venv_relpath: str
    _loader: VenvMapLoader

    def __init__(self, loader, venv_relpath):
        """Class constructor"""
        meth_dotted_path = f"{g_app_name}.lock_fixing.Fixing.__init__"

        # may raise MissingPackageBaseFolder
        check_loader(loader)

        if not is_ok(venv_relpath):
            msg_warn = (
                f"{meth_dotted_path} unsupported type for venv_relpath expects str"
            )
            raise TypeError(msg_warn)
        else:  # pragma: no cover
            pass

        try:
            VenvMap(loader)
        except (NotADirectoryError, ValueError):
            raise

        self._loader = loader
        self._venv_relpath = venv_relpath

        if is_module_debug:  # pragma: no cover
            msg_info = f"{meth_dotted_path} loader.project_base {loader.project_base}"
            _logger.info(msg_info)
        else:  # pragma: no cover
            pass

        # Store ``.in`` files ONCE. Auto resolution loop occurs
        try:
            ins = Ins(loader, venv_relpath)
            ins.load()
            self._ins = ins

            # Store ``.lock`` files ONCE
            locks = Ins(loader, venv_relpath)
            locks.load(suffix_last=SUFFIX_LOCKED)
            self._locks = locks
        except MissingRequirementsFoldersFiles:
            raise

        if is_module_debug:  # pragma: no cover
            msg_info = (
                f"{meth_dotted_path} ins {pprint(ins)}{os.linesep}"
                f"locks {pprint(locks)}"
            )
            _logger.info(msg_info)
        else:  # pragma: no cover
            pass

    def get_issues(self):
        """Identify resolvable and unresolvable issues.

        :returns: lists of resolvable and unresolvable issues
        :rtype: tuple[list[Resolvable], list[UnResolvable]]
        """
        ret = _load_once(self._ins, self._locks, self._venv_relpath)
        self._resolvables = ret[0]
        self._unresolvables = ret[1]

    def fix_resolvables(self, is_dry_run=False):
        """Resolve the resolvable dependency conflicts. Refrain from attempting to
        fix resolvable conflicts involving .shared requirements files.

        :param is_dry_run: Default False. True to avoid writing to file
        :type is_dry_run: bool
        """
        is_dry_run_ng = is_dry_run is None or not isinstance(is_dry_run, bool)
        if is_dry_run_ng:
            is_dry_run = False
        else:  # pragma: no cover
            pass

        t_results = _fix_resolvables(
            self._resolvables,
            self._locks,
            self._venv_relpath,
            is_dry_run=is_dry_run,
        )
        fixed_issues, applies_to_shared = t_results
        self._fixed_issues = fixed_issues
        # group by venv -- resolved_msgs
        # d_resolved_msgs[self._venv_relpath] = fixed_issues
        pass

        # group by venv -- unresolvables
        # d_unresolvables[self._venv_relpath] = lst_unresolvable
        pass

        # group by venv -- resolvable .shared
        #     venv_path, suffix (.unlock or .lock), resolvable, pin
        resolvable_shared_filtered = []
        for t_resolvable_shared in applies_to_shared:
            resolvable_shared_filtered.append(t_resolvable_shared[1:])
        # d_resolvable_shared[venv_relpath] = resolvable_shared_filtered
        self._resolvable_shared = resolvable_shared_filtered

    @property
    def resolvables(self):
        """Get resolvable issues

        :returns: list of Resolvable issues
        :rtype: list[drain_swamp.lock_discrepancy.Resolvable]
        """
        ret = self._resolvables

        return ret

    @property
    def resolvable_shared(self):
        """``.shared.in`` do not try to resolve.

        :returns: list of Resolvable issues
        :rtype: list[drain_swamp.lock_discrepancy.ResolvedMsg]
        """
        ret = self._resolvable_shared

        return ret

    @property
    def unresolvables(self):
        """Get unresolvable issues

        :returns: list of unresolvable issues
        :rtype: list[drain_swamp.lock_discrepancy.UnResolvable]
        """
        ret = self._unresolvables

        return ret

    @property
    def fixed_issues(self):
        """Get fixed issue messages

        :returns: list of fixed issues
        :rtype: list[drain_swamp.lock_discrepancy.ResolvedMsg]
        """
        ret = self._fixed_issues

        return ret


def fix_requirements_lock(loader, venv_relpath, is_dry_run=False):
    """Iterate thru venv. ``.unlock`` may not yet exist. For each
    ``.in`` file, resolution loop once

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

    :rtype: tuple[list[drain_swamp.lock_discrepancy.ResolvedMsg], list[drain_swamp.lock_discrepancy.UnResolvable], list[tuple[str, drain_swamp.lock_discrepancy.Resolvable, drain_swamp.lock_datum.Pin | drain_swamp.lock_datum.PinDatum]]]
    :raises:

       - :py:exc:`NotADirectoryError` -- there is no cooresponding venv folder. Create it

       - :py:exc:`ValueError` -- expecting [[tool.venvs]] field reqs should be a
         list of relative path without .in .unlock or .lock suffix

       - :py:exc:`drain_swamp.exceptions.MissingRequirementsFoldersFiles` --
         missing constraints or requirements files or folders

       - :py:exc:`drain_swamp.exceptions.MissingPackageBaseFolder` --
         Invalid loader. Does not provide package base folder

    """
    # may raise MissingPackageBaseFolder
    check_loader(loader)

    if is_dry_run is None or not isinstance(is_dry_run, bool):
        is_dry_run = False
    else:
        pass

    try:
        t_fixing = Fixing(loader, venv_relpath)
    except (NotADirectoryError, ValueError, MissingRequirementsFoldersFiles):
        raise

    t_fixing.get_issues()
    t_fixing.fix_resolvables(is_dry_run=is_dry_run)
    t_fixing.resolvables
    lst_unresolvables = t_fixing.unresolvables
    msgs_fixed = t_fixing.fixed_issues
    msgs_shared = t_fixing.resolvable_shared

    return msgs_fixed, lst_unresolvables, msgs_shared
