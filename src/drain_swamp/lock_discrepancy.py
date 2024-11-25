"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

.. py:class:: PkgsWithIssues

.. py:data:: PkgsWithIssues
   :type: dict[str, dict[str, packaging.version.Version | set[packaging.version.Version]]]
   :noindex:

   Packages by a dict containing highest version and other versions

.. py:data:: __all__
   :type: tuple[str, str, str, str, str, str, str]
   :value: ("PkgsWithIssues", "Resolvable", "ResolvedMsg", "UnResolvable", \
   "has_discrepancies_version", "tunnel_blindness_suffer_chooses", \
   "write_to_file_nudge_pin")

   Module exports

.. py:data:: is_module_debug
   :type: bool
   :value: False

   Flag to turn on module level logging. Should be off in production

.. py:data:: _logger
   :type: logging.Logger

   Module level logger

"""

from __future__ import annotations

import io
import logging
import operator
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from pprint import pprint
from typing import (
    TYPE_CHECKING,
    Union,
    cast,
)

from packaging.specifiers import SpecifierSet
from packaging.version import Version

from .constants import g_app_name
from .lock_datum import (
    DatumByPkg,
    Pin,
    PinDatum,
)

if sys.version_info >= (3, 10):  # pragma: no cover py-gte-310-else
    DC_SLOTS = {"slots": True}
else:  # pragma: no cover py-gte-310
    DC_SLOTS = {}

is_module_debug = True
_logger = logging.getLogger(f"{g_app_name}.lock_discrepancy")

__all__ = (
    "PkgsWithIssues",
    "Resolvable",
    "ResolvedMsg",
    "UnResolvable",
    "has_discrepancies_version",
    "tunnel_blindness_suffer_chooses",
    "write_to_file_nudge_pin",
)

PkgsWithIssues = dict[str, dict[str, Union[Version, set[Version]]]]


def has_discrepancies_version(d_by_pkg: DatumByPkg):
    """Across ``.lock`` files, packages with discrepancies.

    Comparison limited to equality

    :param d_by_pkg: Within one venv, all lock packages' ``set[Pin | PinDatum]``
    :type d_by_pkg: drain_swamp.lock_datum.DatumByPkg
    :returns:

       pkg name / highest version. Only packages with discrepancies.
       With the highest version, know which version to *nudge* to.

    :rtype: drain_swamp.lock_discrepancy.PkgsWithIssues
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
                    # Keep lowers to have available versions set
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


def _get_ss_set(set_pindatum):
    """Create a set of all SpecifierSet

    :param set_pindatum: PinDatum for the same package, from all ``.lock`` files
    :type set_pindatum: set[drain_swamp.lock_datum.Pin | drain_swamp.lock_datum.PinDatum]
    :returns: set of SpecifierSet
    :rtype: set[packaging.specifiers.SpecifierSet]
    """
    set_ss = set()
    for pin in set_pindatum:
        # ss_pre = SpecifierSet(",".join(pin.specifiers), prereleases=True)
        ss_release = SpecifierSet(",".join(pin.specifiers))
        set_ss.add(ss_release)

    # An empty SpecifierSet is worthless and annoying cuz throws off count
    ss_empty = SpecifierSet("")
    if ss_empty in set_ss:
        set_ss.discard(ss_empty)

    return set_ss


def _get_specifiers(set_pindatum):
    """Get specifiers from pins

    :param set_pindatum: PinDatum for the same package, from all ``.lock`` files
    :type set_pindatum: set[drain_swamp.lock_datum.Pin | drain_swamp.lock_datum.PinDatum]
    :return: Specifiers lists
    :rtype: list[list[str]]
    """
    lst = []
    for pin in set_pindatum:
        lst.append(pin.specifiers)

    return lst


def _parse_specifiers(specifiers: list[str]):
    """Extract specifers, operator and version ignore ``!=`` specifiers.

    :param specifiers:

       .unlock or .lock file line. Has package name, but might not be exact

    :type specifiers: list[str]
    :returns: original specifiers list replace str with a tuple of it's parts
    :rtype: str | None

    .. seealso::

       `pep044 <https://peps.python.org/pep-0440>`_
       `escape characters <https://docs.python.org/3/library/re.html#re.escape>`_

    """
    dotted_path = f"{g_app_name}.lock_discrepancy._parse_specifiers"
    # Assume does not contain comma separators
    pattern = r"^(\s)*(==|<=|>=|<|>|~=|!=)(\S+)"

    lst = []
    for spec in specifiers:
        m = re.match(pattern, spec)
        if m is None:  # pragma: no cover
            if is_module_debug:
                msg_info = f"{dotted_path} failed to parse pkg from spec: {spec!r}"
                _logger.info(msg_info)
            else:
                pass
            continue
        else:
            groups = m.groups(default=None)  # noqa: F841
            oper = groups[1]
            oper = oper.strip()
            ver = groups[2]
            ver = ver.strip()
            t_parsed = (oper, ver)
            lst.append(t_parsed)

    return lst


def tunnel_blindness_suffer_chooses(
    set_pindatum,
    highest,
    others,
):
    """When a ``.lock`` file is created, it is built from:

    - one ``.in`` file
    - recursively resolved constraints and requirements files

    But not all. Therein lies the rub. Trying to choose based on the
    limited info at hand.

    This algo will fail when there is an unnoticed pin that limits
    the version.

    :param set_pindatum: PinDatum for the same package, from all ``.lock`` files
    :type set_pindatum: set[drain_swamp.lock_datum.Pin | drain_swamp.lock_datum.PinDatum]
    :param highest: Highest Version amongst the choices
    :type highest: packaging.version.Version
    :param others: Other known Version detected within (same venv) ``.lock`` files
    :type others: set[packaging.version.Version]
    :returns:

       set[SpecifierSet] and operator str, and
       whether an acceptable version was found

       Operator str is only applicable for unlock nudge pins, not for
       .lock package version fixes.

    :rtype: tuple[set[packaging.specifiers.SpecifierSet], str, str]
    """
    dotted_path = f"{g_app_name}.lock_discrepancy.tunnel_blindness_suffer_chooses"
    # Create a set of all SpecifierSet. Discarded empty {SpecifierSet('')}
    set_ss = _get_ss_set(set_pindatum)

    def acceptable_version(set_ss: set[SpecifierSet], v_test: Version) -> bool:
        """Satisfies all SpecifierSet"""
        ret = all([v_test in ss for ss in set_ss])
        return ret

    # Discard unacceptable versions (from .lock)
    set_highest = set()
    set_highest.add(highest)
    set_all = others.union(set_highest)
    set_acceptable = set()
    for ver in set_all:
        if acceptable_version(set_ss, ver):
            set_acceptable.add(ver)
        else:  # pragma: no cover
            pass

    # By pkg_name, from ``.in`` files
    lsts_specifiers = _get_specifiers(set_pindatum)

    if is_module_debug:  # pragma: no cover
        msg_info = f"{dotted_path} lsts_specifiers (before) {lsts_specifiers!r}"
        _logger.info(msg_info)
    else:  # pragma: no cover
        pass

    # Remove empty list(s)
    empty_idx = []
    for idx, lst_specifiers in enumerate(lsts_specifiers):
        if len(lst_specifiers) == 0:
            empty_idx.append(idx)
        else:  # pragma: no cover
            pass
    #    reversed so higher idx removed first
    for idx in reversed(empty_idx):
        del lsts_specifiers[idx]

    if is_module_debug:  # pragma: no cover
        msg_info = f"{dotted_path} lsts_specifiers (after) {lsts_specifiers!r}"
        _logger.info(msg_info)
    else:  # pragma: no cover
        pass

    # remove from set_acceptable any '!='
    # '==' exclude all other versions
    is_eq_affinity = False
    for idx, lst_specifiers in enumerate(lsts_specifiers):
        specifiers = _parse_specifiers(lst_specifiers)
        if is_module_debug:  # pragma: no cover
            msg_info = f"{dotted_path} specifiers {specifiers!r}"
            _logger.info(msg_info)
        else:  # pragma: no cover
            pass
        for t_spec in specifiers:
            oper, ver = t_spec
            ver_version = Version(ver)
            if oper == "!=":
                if is_module_debug:  # pragma: no cover
                    msg_info = f"{dotted_path} {oper!s} {ver_version!r}"
                    _logger.info(msg_info)
                else:  # pragma: no cover
                    pass
                set_acceptable.discard(ver_version)
            elif oper == "==":
                # Discard all except ver
                is_eq_affinity = True
                unlock_ver = ver_version
                set_remove_these = set()
                for ver_acceptable in set_acceptable:
                    if is_module_debug:  # pragma: no cover
                        msg_info = (
                            f"{dotted_path} ver_acceptable {ver_acceptable!r} "
                            f"ver_version {ver_version!r}"
                        )
                        _logger.info(msg_info)
                    else:  # pragma: no cover
                        pass
                    # Won't be in set_acceptable
                    if ver_acceptable != ver_version:  # pragma: no cover
                        set_remove_these.add(ver_acceptable)
                    else:  # pragma: no cover
                        pass
                # Remove all elements of set B from this set A
                set_acceptable.difference_update(set_remove_these)
                if is_module_debug:  # pragma: no cover
                    msg_info = (
                        f"{dotted_path} {oper!s} {ver_version!r} "
                        f"is_eq_affinity {is_eq_affinity!r} "
                        f"set_acceptable {set_acceptable!r}"
                    )
                    _logger.info(msg_info)
                else:  # pragma: no cover
                    pass
            else:  # pragma: no cover
                pass

    if is_module_debug:  # pragma: no cover
        msg_info = f"{dotted_path} set_acceptable {set_acceptable!r}"
        _logger.info(msg_info)
    else:  # pragma: no cover
        pass

    # Test highest
    is_ss_count_zero = len(set_ss) == 0
    if is_eq_affinity is True:
        # A specifier explicitly limits to only one version
        found = unlock_ver
        unlock_operator = "=="
    elif is_ss_count_zero:
        # No specifiers limiting versions. Choose highest
        found = highest
        unlock_operator = ">="
        t_ret = (set_ss, unlock_operator, found)
    else:
        # Trying to find affinity tuple (operator, ver)
        #    Default unlock operator is "=="
        unlock_operator = "=="
        unlock_ver = None

        for idx, lst_specifiers in enumerate(lsts_specifiers):
            if len(lst_specifiers) == 1:
                specifiers = _parse_specifiers(lst_specifiers)
                if is_module_debug:  # pragma: no cover
                    msg_info = (
                        f"{dotted_path} {idx!s} {specifiers!r} {lst_specifiers!r}"
                    )
                    _logger.info(msg_info)
                else:  # pragma: no cover
                    pass
                has_specifiers = len(specifiers) != 0
                if has_specifiers:
                    t_spec = specifiers[0]
                    oper, ver = t_spec

                    if oper == "~=":
                        msg_warn = "~= operator is not yet implemented"
                        raise NotImplementedError(msg_warn)
                    else:  # pragma: no cover
                        pass

                    if oper in ("!=", "=="):
                        # ``!=`` -- acceptable_version filtered out {ver}
                        # ``==`` -- default unlock operator
                        continue
                    else:
                        unlock_operator = oper
                        unlock_ver = ver
                        continue
                else:  # pragma: no cover
                    pass
            elif len(lst_specifiers) == 2:
                specifiers = _parse_specifiers(lst_specifiers)
                t_spec_0 = specifiers[0]
                t_spec_1 = specifiers[1]
                oper_0, ver_0 = t_spec_0
                oper_1, ver_1 = t_spec_1

                # ``~=`` operator --> NotImplementedError
                two_opers = (oper_0, oper_1)
                if "~=" in two_opers:
                    msg_warn = (
                        f"~= operator is not yet implemented {t_spec_0!r} {t_spec_1!r}"
                    )
                    raise NotImplementedError(msg_warn)
                else:  # pragma: no cover
                    pass

                is_excluded_0 = Version(ver_0) not in set_acceptable
                is_excluded_1 = Version(ver_1) not in set_acceptable
                if is_excluded_0 and is_excluded_1:
                    # Both of these already filtered out, but affects unlock_operator
                    continue
                elif is_excluded_0:
                    if oper_1 in ("=="):
                        # ``==`` -- default unlock operator
                        continue
                    else:
                        unlock_operator = oper_1
                        unlock_ver = ver_1
                elif is_excluded_1:
                    if oper_0 in ("=="):
                        # ``==`` -- default unlock operator
                        continue
                    else:
                        unlock_operator = oper_0
                        unlock_ver = ver_0
                else:
                    """Take 1st specifier [">=24.1", "<25"]. ver 25 most
                    likely doesn't exist
                    """
                    if oper_0 in ("=="):
                        # ``!=`` -- acceptable_version will filtered out
                        # ``==`` -- default unlock operator
                        continue
                    else:
                        unlock_operator = oper_0
                        unlock_ver = ver_0
            else:
                msg_warn = "A pin containing >= 2 specifiers is not supported"
                raise NotImplementedError(msg_warn)

        if unlock_ver is None:
            # Take highest from amongst the acceptable versions
            lst_sorted = sorted(list(set_acceptable))
            found = lst_sorted[-1]
        else:
            if unlock_operator in "==":
                func = None
                idx_from_list = None
                found = unlock_ver
            if unlock_operator in "<=":
                # version le and closest to
                # remove versions > unlock_ver. Then take lowest
                func = operator.le
                idx_from_list = 0
            elif unlock_operator in "<":
                # version lt unlock_ver and closest to unlock_ver
                # remove versions >= unlock_ver. Then take lowest
                func = operator.lt
                idx_from_list = 0
            elif unlock_operator in ">=":
                # version ge and closest to unlock_ver
                # remove versions < unlock_ver. Then take highest
                func = operator.ge
                idx_from_list = -1
            elif unlock_operator in ">":
                # version gt unlock_ver and closest to unlock_ver
                # remove versions <= unlock_ver. Then take highest
                func = operator.gt
                idx_from_list = -1
            else:
                if is_module_debug:  # pragma: no cover
                    msg_info = (
                        f"{dotted_path} unexpected unlock operator {unlock_operator}"
                    )
                    _logger.info(msg_info)
                else:  # pragma: no cover
                    pass
                raise AssertionError(msg_info)

            if func is not None:
                lst = [
                    ver_test
                    for ver_test in set_acceptable
                    if func(ver_test, Version(unlock_ver))
                ]
                if len(lst) != 0:
                    lst_sorted = sorted(lst)
                    found = lst_sorted[idx_from_list]
                else:
                    found = None
            else:  # pragma: no cover
                pass

    t_ret = (set_ss, unlock_operator, found)

    return t_ret


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

    :vartype pins: drain_swamp.lock_inspect.Pins[drain_swamp.lock_datum.Pin]
    """

    venv_path: str
    pkg_name: str
    qualifiers: str
    sss: set[SpecifierSet]
    v_highest: Version
    v_others: set[Version]
    pins: set[Pin] | set[PinDatum]

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


def extract_full_package_name(line, pkg_name_desired):
    """Extract first occurrence of exact package name

    :param line:

       .unlock or .lock file line. Has package name, but might not be exact

    :type line: str
    :param pkg_name_desired: pkg name would like an exact match
    :type pkg_name_desired: str
    :returns: pkg name If line contains exact match for package otherwise None
    :rtype: str | None

    .. seealso::

       `pep044 <https://peps.python.org/pep-0440>`_
       `escape characters <https://docs.python.org/3/library/re.html#re.escape>`_

    """
    mod_path = f"{g_app_name}.lock_discrepancy.extract_full_package_name"
    pattern = r"^(\S+)(?=(==|<=|>=|<|>|~=|!=|===|@| @|@ | @ | ;|; |;| ; ))"
    m = re.match(pattern, line)

    if m is None:
        if is_module_debug:  # pragma: no cover
            msg_info = (
                f"{mod_path} failed to parse pkg from line: {line}{os.linesep}"
                f"pkg_name_desired {pkg_name_desired}"
            )
            _logger.info(msg_info)
        else:  # pragma: no cover
            pass
        ret = None
    else:
        """for debugging results of re.match. Use along with
        logging_strict.tech_niques.get_locals"""
        groups = m.groups(default=None)  # noqa: F841
        group_0 = m.group(0)
        if group_0.rstrip() == pkg_name_desired:
            ret = group_0.rstrip()
        else:
            # e.g. desired ``tox`` line contains ``tox-gh-action``
            ret = None

    return ret


def write_to_file_nudge_pin(path_f, pkg_name, nudge_pin_line):
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
                is_empty_line = len(line.strip()) == 0
                is_comment = line.startswith("#")

                # This would match e.g. tox and tox-gh-actions
                # Need an exact match
                is_pkg_startswith = line.startswith(pkg_name)

                if is_pkg_startswith:
                    pkg_actual = extract_full_package_name(line, pkg_name)
                    if pkg_actual is None:
                        is_pkg_not = True
                    else:
                        is_pkg_not = False
                else:
                    is_pkg_not = True

                if is_empty_line or is_comment or is_pkg_not:
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
