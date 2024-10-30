"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

Unit test -- Module

.. code-block:: shell

   python -m coverage run --source='drain_swamp.lock_inspect' -m pytest \
   --showlocals tests/test_lock_inspect.py && coverage report \
   --data-file=.coverage --include="**/lock_inspect.py"

"""

import logging
import logging.config
import os
import shutil
from collections.abc import Mapping
from contextlib import nullcontext as does_not_raise
from pathlib import Path

import pytest
from logging_strict.tech_niques import get_locals  # noqa: F401

from drain_swamp._safe_path import replace_suffixes
from drain_swamp.constants import (
    LOGGING,
    g_app_name,
)
from drain_swamp.lock_inspect import (
    Pin,
    Pins,
    _wrapper_pins_by_pkg,
    fix_requirements,
    fix_resolvables,
    get_issues,
)
from drain_swamp.lock_util import is_shared
from drain_swamp.pep518_venvs import VenvMapLoader

from .testdata_lock_inspect import (
    ids_resolve_resolvable_conflicts,
    testdata_resolve_resolvable_conflicts,
)

testdata_pin_is_pin = (
    (
        "typing-extensions",
        '''typing-extensions; python_version<"3.10"''',
        [],
        '''; python_version<"3.10"''',
        does_not_raise(),
        False,
    ),
    (
        "tomli",
        '''tomli>=2.0.2; python_version<"3.11"''',
        [">=2.0.2"],
        '''; python_version<"3.11"''',
        does_not_raise(),
        True,
    ),
    (
        "pip",
        "pip>=24.2",
        [">=24.2"],
        None,
        does_not_raise(),
        True,
    ),
    (
        "isort",
        "isort",
        [],
        None,
        does_not_raise(),
        False,
    ),
)
ids_pin_is_pin = (
    "Not a pin, but has qualifiers",
    "pin and has qualifiers",
    "nudge pin",
    "just a normal package. No package version nor qualifiers",
)


@pytest.mark.parametrize(
    "pkg_name, line, specifiers, qualifiers_expected, expectation, expected_is_pin",
    testdata_pin_is_pin,
    ids=ids_pin_is_pin,
)
def test_pin_is_pin(
    pkg_name,
    line,
    specifiers,
    qualifiers_expected,
    expectation,
    expected_is_pin,
):
    """Defines whats a pin and whats not. Qualifiers is not enough."""
    # pytest --showlocals --log-level INFO -k "test_pin_is_pin" tests
    # act
    file_abspath = Path(__file__).parent.joinpath(
        "_req_files",
        "constraints-various.unlock",
    )

    with expectation:
        pin = Pin(file_abspath, pkg_name)

    if isinstance(expectation, does_not_raise):
        # verify
        actual_is_pin = Pin.is_pin(pin.specifiers)
        assert actual_is_pin is expected_is_pin


testdata_pin_exceptions = (
    (
        Path(__file__).parent.joinpath(
            "_req_files",
            "empty.unlock",
        ),
        "isort",
        pytest.raises(KeyError),
    ),
)
ids_pin_exceptions = ("nonexistant package",)


@pytest.mark.parametrize(
    "file_abspath, pkg_name, expectation",
    testdata_pin_exceptions,
    ids=ids_pin_exceptions,
)
def test_pin_exceptions(file_abspath, pkg_name, expectation):
    """Normally requirements are loaded from file, not randomly requested."""
    # pytest --showlocals --log-level INFO -k "test_pin_exceptions" tests
    # literally an empty file
    with expectation:
        Pin(file_abspath, pkg_name)


testdata_pins_realistic = (
    (
        Path(__file__).parent.joinpath(
            "_req_files",
            "venvs.pyproject_toml",
        ),
        ".venv",
        (
            (
                Path(__file__).parent.joinpath(
                    "_req_files",
                    "constraints-various.unlock",
                ),
                "requirements/dev.unlock",
            ),
            (
                Path(__file__).parent.joinpath(
                    "_req_files",
                    "prod.shared.unlock",
                ),
                "requirements/prod.shared.unlock",
            ),
        ),
        10,
        5,
    ),
)
ids_pins_realistic = ("Parse venv requirements files into Pins",)


@pytest.mark.parametrize(
    "path_config, venv_path, seq_reqs, pkg_count_expected, pkg_pin_count_expected",
    testdata_pins_realistic,
    ids=ids_pins_realistic,
)
def test_pins_realistic(
    path_config,
    venv_path,
    seq_reqs,
    pkg_count_expected,
    pkg_pin_count_expected,
    tmp_path,
    prep_pyproject_toml,
    prepare_folders_files,
    caplog,
    has_logging_occurred,
):
    """test Pins class."""
    # pytest -vv --showlocals --log-level INFO -k "test_pins_realistic" tests
    LOGGING["loggers"][g_app_name]["propagate"] = True
    logging.config.dictConfig(LOGGING)
    logger = logging.getLogger(name=g_app_name)
    logger.addHandler(hdlr=caplog.handler)
    caplog.handler.level = logger.level

    # prepare
    #    pyproject.toml or [something].pyproject_toml
    path_dest_config = prep_pyproject_toml(path_config, tmp_path)

    #    requirements empty files and folders; no .unlock or .lock files
    seq_rel_paths = ("requirements/pins.shared.in",)
    prepare_folders_files(seq_rel_paths, tmp_path)

    #    venv folders must exist. This fixture creates files. So .python-version
    venvs_path = (
        ".venv/.python-version",
        ".doc/.venv/.python-version",
    )
    prepare_folders_files(venvs_path, tmp_path)

    #    requirements empty files and folders
    bases_path = (
        "docs/pip-tools",
        "docs/requirements",
        "requirements/pip-tools",
        "requirements/pip",
        "requirements/prod.shared",
        "requirements/kit",
        "requirements/tox",
        "requirements/mypy",
        "requirements/manage",
        "requirements/dev",
    )
    suffixes = (".in", ".unlock", ".lock")
    seq_rel_paths = []
    for suffix in suffixes:
        for base_path in bases_path:
            seq_rel_paths.append(f"{base_path}{suffix}")
    prepare_folders_files(seq_rel_paths, tmp_path)

    is_first_1 = True
    for t_paths in seq_reqs:
        src_abspath, dest_relpath = t_paths

        #    overwrite 'requirements/dev.unlock'
        abspath_dest = tmp_path / dest_relpath
        if is_first_1:
            is_first_1 = False
            abspath_dest_0 = abspath_dest
        shutil.copy(src_abspath, abspath_dest)

        #    pip-compile -o [file].lock [file].unlock
        #    careful no .shared
        if is_shared(abspath_dest.name):
            str_shared = ".shared"
        else:
            str_shared = ""
        src_abspath_lock = replace_suffixes(src_abspath, f"{str_shared}.lock")
        abspath_dest_lock = replace_suffixes(abspath_dest, f"{str_shared}.lock")
        shutil.copy(src_abspath_lock, abspath_dest_lock)

    # Add package pip to Pins. Can pass into Pins a Sequence or a set
    pins_empty = Pins([])
    pin_pip = Pin(abspath_dest_0, "pip")
    pins_empty.add(pin_pip)
    assert len(pins_empty) == 1

    # repr -- empty set
    repr_pins = repr(pins_empty)
    assert isinstance(repr_pins, str)
    pins_empty.discard(pin_pip)
    assert len(pins_empty) == 0
    del pins_empty

    # Identify pins from .unlock files
    #    Careful path must be a str
    loader = VenvMapLoader(path_dest_config.as_posix())

    #    filter_by_pin None --> True.
    #    If Missing requirements --> FileNotFoundError
    lst_pins = Pins.from_loader(
        loader,
        venv_path,
        suffix=".unlock",
        filter_by_pin=None,
    )
    pins = Pins(lst_pins)

    # repr -- non-empty set
    repr_pins = repr(pins)
    assert isinstance(repr_pins, str)

    # Other (empty) requirements files exist, BUT do not contain pins
    pkg_pin_count_actual = len(pins)
    assert pkg_pin_count_actual == pkg_pin_count_expected

    # Not a sequence or set
    invalids = (
        None,
        loader,
    )
    for invalid in invalids:
        with pytest.raises(TypeError):
            Pins(invalid)
    # Pins.add will ignore unsupported items
    invalids = (
        "",
        "abcde",
        (3,),
    )
    for invalid in invalids:
        Pins(invalid)

    # __contains__
    pin_pip = Pin(abspath_dest_0, "pip")
    assert pin_pip in pins
    assert 3 not in pins

    # Loop Iterator
    for pin_found in pins:
        assert isinstance(pin_found, Pin)

    # Loop Iterator again; the magic reusable Iterator!
    for pin_found in pins:
        assert isinstance(pin_found, Pin)

    # Failing here under Windows. See what is happening inside the function
    func_path = f"{g_app_name}.lock_inspect._wrapper_pins_by_pkg"
    args = (loader, venv_path)
    kwargs = {"suffix": None, "filter_by_pin": None}
    t_ret = get_locals(func_path, _wrapper_pins_by_pkg, *args, **kwargs)  # noqa: F841

    # Reorganize Pin by pkgname. Need to prepare .lock file
    #    suffix None --> .lock, filter_by_pin None --> True
    pins_by_pkg = Pins.by_pkg(loader, venv_path, suffix=None, filter_by_pin=None)

    pkg_names = pins_by_pkg.keys()
    pkg_count_actual = len(pkg_names)
    assert pkg_count_actual == pkg_count_expected
    for pkg_name, pins_same_pkg in pins_by_pkg.items():
        assert isinstance(pins_same_pkg, set)
        assert isinstance(list(pins_same_pkg)[0], Pin)
        assert len(pins_same_pkg) == 1

    # assert has_logging_occurred(caplog)


@pytest.mark.parametrize(
    "path_pyproject_toml, venv_path, base_relpaths, to_requirements_dir, expected_resolvable_count, expected_unresolvable_count,",
    testdata_resolve_resolvable_conflicts,
    ids=ids_resolve_resolvable_conflicts,
)
def test_resolve_resolvable_conflicts(
    path_pyproject_toml,
    venv_path,
    base_relpaths,
    to_requirements_dir,
    expected_resolvable_count,
    expected_unresolvable_count,
    tmp_path,
    caplog,
    has_logging_occurred,
    prepare_folders_files,
    prep_pyproject_toml,
):
    """Test identify conflicts, resolve conflicts or issue warnings."""
    # pytest -vv --showlocals --log-level INFO -k "test_resolve_resolvable_conflicts" tests
    LOGGING["loggers"][g_app_name]["propagate"] = True
    logging.config.dictConfig(LOGGING)
    logger = logging.getLogger(name=g_app_name)
    logger.addHandler(hdlr=caplog.handler)
    caplog.handler.level = logger.level

    # prepare
    #    Copy to base dir
    path_dest_pyproject_toml = prep_pyproject_toml(path_pyproject_toml, tmp_path)

    #    venv_path must be a folder. If not or no folder --> NotADirectoryError
    prep_these = (".venv/.python-version",)
    prepare_folders_files(prep_these, tmp_path)

    loader = VenvMapLoader(path_dest_pyproject_toml.as_posix())

    # Missing requirements files --> FileNotFoundError
    with pytest.raises(FileNotFoundError):
        get_issues(loader, venv_path)

    # Missing requirements files --> FileNotFoundError
    with pytest.raises(FileNotFoundError):
        fix_resolvables((), loader, venv_path, is_dry_run=True)

    #   Create requirements folder, since there are no base_relpaths
    prep_these = ("requirements/junk.deleteme",)
    prepare_folders_files(prep_these, tmp_path)

    #   Copy empties
    prep_these = []
    for suffix in (".in", ".unlock", ".lock"):
        for base_relpath in base_relpaths:
            prep_these.append(f"{base_relpath}{suffix}")
        prepare_folders_files(prep_these, tmp_path)

    #    Copy real .unlock and .lock files
    for abspath_src in to_requirements_dir:
        src_abspath = str(abspath_src)
        abspath_dest = tmp_path / "requirements" / abspath_src.name
        shutil.copy(src_abspath, abspath_dest)

    locks_by_pkg = Pins.by_pkg(loader, venv_path)

    # Failing here under Windows. See what is happening inside the function
    func_path = f"{g_app_name}.lock_inspect._wrapper_pins_by_pkg"
    args = (loader, venv_path)
    kwargs = {}
    t_ret = get_locals(func_path, _wrapper_pins_by_pkg, *args, **kwargs)  # noqa: F841

    t_out = Pins.by_pkg_with_issues(loader, venv_path)
    locks_by_pkg_w_issues, locks_pkg_by_versions = t_out

    # One pkg filtered out. Right side only contains packages WITH discrepencies
    # **No qualifiers support**
    pkgs_count = len(locks_by_pkg)
    pkgs_w_issues_count = len(locks_by_pkg_w_issues)
    assert pkgs_count != pkgs_w_issues_count

    t_actionable = get_issues(loader, venv_path)
    assert isinstance(t_actionable, tuple)
    lst_resolvable, lst_unresolvable = t_actionable
    assert isinstance(lst_resolvable, list)
    assert isinstance(lst_unresolvable, list)
    unresolvable = lst_unresolvable[0]
    repr_unresolvable = repr(unresolvable)
    assert isinstance(repr_unresolvable, str)

    actual_resolvable_count = len(lst_resolvable)
    actual_unresolvable_count = len(lst_unresolvable)
    assert actual_resolvable_count == expected_resolvable_count
    assert actual_unresolvable_count == expected_unresolvable_count

    # 1.12345 --> False
    t_results = fix_resolvables(lst_resolvable, loader, venv_path, is_dry_run=1.12345)
    fixed_issues, applies_to_shared = t_results
    assert isinstance(fixed_issues, list)
    assert isinstance(applies_to_shared, list)
    actual_applies_to_shared_count = len(applies_to_shared)
    assert actual_applies_to_shared_count != 0

    # has_logging_occurred(caplog)
    # assert False is True


@pytest.mark.parametrize(
    "path_pyproject_toml, venv_path, base_relpaths, to_requirements_dir, expected_resolvable_count, expected_unresolvable_count,",
    testdata_resolve_resolvable_conflicts,
    ids=ids_resolve_resolvable_conflicts,
)
def test_fix_requirements(
    path_pyproject_toml,
    venv_path,
    base_relpaths,
    to_requirements_dir,
    expected_resolvable_count,
    expected_unresolvable_count,
    tmp_path,
    caplog,
    has_logging_occurred,
    prepare_folders_files,
    prep_pyproject_toml,
):
    """Same as resolve_resolvable_conflicts, but all venv requirements are fixed."""
    # pytest -vv --showlocals --log-level INFO -k "test_fix_requirements" tests
    LOGGING["loggers"][g_app_name]["propagate"] = True
    logging.config.dictConfig(LOGGING)
    logger = logging.getLogger(name=g_app_name)
    logger.addHandler(hdlr=caplog.handler)
    caplog.handler.level = logger.level

    # no prep. Cannot find pyproject.toml
    with pytest.raises(FileNotFoundError):
        VenvMapLoader(tmp_path.as_posix())

    # prepare
    #    Copy to base dir
    path_dest_pyproject_toml = prep_pyproject_toml(path_pyproject_toml, tmp_path)

    loader = VenvMapLoader(path_dest_pyproject_toml.as_posix())

    #    No venv path folder --> NotADirectoryError
    with pytest.raises(NotADirectoryError):
        fix_requirements(loader, is_dry_run=True)

    #    venv_path must be a folder. If not or no folder --> NotADirectoryError
    prep_these = (".venv/.python-version",)
    prepare_folders_files(prep_these, tmp_path)

    # missing requirements file(s) --> FileNotFoundError
    with pytest.raises(FileNotFoundError):
        fix_requirements(loader, is_dry_run=True)

    #   Create requirements folder, since there are no base_relpaths
    prep_these = ("requirements/junk.deleteme",)
    prepare_folders_files(prep_these, tmp_path)

    #   Copy empties
    prep_these = []
    for suffix in (".in", ".unlock", ".lock"):
        for base_relpath in base_relpaths:
            prep_these.append(f"{base_relpath}{suffix}")
        prepare_folders_files(prep_these, tmp_path)

    #    Copy real .unlock and .lock files
    for abspath_src in to_requirements_dir:
        src_abspath = str(abspath_src)
        abspath_dest = tmp_path / "requirements" / abspath_src.name
        shutil.copy(src_abspath, abspath_dest)

    # Act
    fix_requirements(loader, is_dry_run=True)

    # None --> False
    t_results = fix_requirements(loader, is_dry_run=None)
    assert isinstance(t_results, tuple)
    d_resolved_msgs, d_unresolvables, d_applies_to_shared = t_results
    assert isinstance(d_resolved_msgs, Mapping)
    assert isinstance(d_unresolvables, Mapping)
    assert isinstance(d_applies_to_shared, Mapping)

    """Present the results. UX matters. Issues must be presented in
    human readable format(s). Could also group by venv_path"""
    if len(d_unresolvables.keys()) != 0:
        zzz_unresolvables = f"Unresolvables:{os.linesep}{os.linesep}"
        zzz_unresolvables += repr(d_unresolvables)

    if len(d_applies_to_shared.keys()) != 0:
        zzz_resolvables_shared = (
            f".shared resolvable (manually):{os.linesep}{os.linesep}"
        )
        zzz_resolvables_shared += repr(d_applies_to_shared)

    if len(d_resolved_msgs.keys()) != 0:
        zzz_fixed = f"Fixed:{os.linesep}{os.linesep}"
        zzz_fixed += repr(d_resolved_msgs)

    # ignore results of another run
    fix_requirements(loader, is_dry_run=1.12345)
