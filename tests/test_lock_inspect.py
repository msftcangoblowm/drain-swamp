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
from collections.abc import (
    Generator,
    Mapping,
    Sequence,
)
from contextlib import nullcontext as does_not_raise
from pathlib import (
    Path,
    PurePath,
)
from typing import cast
from unittest.mock import patch

import pytest
from logging_strict.tech_niques import get_locals  # noqa: F401
from pip_requirements_parser import InstallationError

from drain_swamp._package_installed import is_package_installed
from drain_swamp._safe_path import (
    resolve_joinpath,
    resolve_path,
)
from drain_swamp.constants import (
    LOGGING,
    SUFFIX_IN,
    SUFFIX_LOCKED,
    SUFFIX_UNLOCKED,
    g_app_name,
)
from drain_swamp.exceptions import MissingRequirementsFoldersFiles
from drain_swamp.lock_inspect import (
    Pin,
    Pins,
    _compile_one,
    _postprocess_abspath_to_relpath,
    _wrapper_pins_by_pkg,
    filter_by_venv_relpath,
    fix_requirements,
    fix_resolvables,
    get_issues,
    get_reqs,
    is_timeout,
    lock_compile,
    prepare_pairs,
    unlock_compile,
)
from drain_swamp.lock_util import replace_suffixes_last
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

    #    venv folders must exist. This fixture creates files. So .python-version
    venvs_path = (
        ".venv/.python-version",
        ".doc/.venv/.python-version",
    )
    prepare_folders_files(venvs_path, tmp_path)

    loader = VenvMapLoader(path_dest_config.as_posix())

    # Have yet to prepare requirements files. Missing requirements files
    with pytest.raises(MissingRequirementsFoldersFiles):
        Pins.from_loader(
            loader,
            ".doc/.venv",
            suffix=SUFFIX_UNLOCKED,
            filter_by_pin=None,
        )

    #    requirements empty files and folders; no .unlock or .lock files
    seq_rel_paths = ("requirements/pins.shared.in",)
    prepare_folders_files(seq_rel_paths, tmp_path)

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
    suffixes = (SUFFIX_IN, SUFFIX_UNLOCKED, SUFFIX_LOCKED)
    seq_rel_paths = []
    for suffix in suffixes:
        for base_path in bases_path:
            seq_rel_paths.append(f"{base_path}{suffix}")
    prepare_folders_files(seq_rel_paths, tmp_path)

    is_first = True
    for t_paths in seq_reqs:
        src_abspath, dest_relpath = t_paths

        #    overwrite 'requirements/dev.unlock'
        abspath_dest = cast("Path", resolve_joinpath(tmp_path, dest_relpath))
        if is_first:
            is_first = False
            abspath_dest_0 = abspath_dest
        shutil.copy(src_abspath, abspath_dest)

        #    pip-compile -o [file].lock [file].unlock
        #    careful no .shared
        src_abspath_lock = replace_suffixes_last(src_abspath, SUFFIX_LOCKED)
        abspath_dest_lock = replace_suffixes_last(abspath_dest, SUFFIX_LOCKED)
        shutil.copy(src_abspath_lock, abspath_dest_lock)

    # Cause pip_requirements_parser.RequirementsFile.from_file to fail
    with patch(
        "pip_requirements_parser.RequirementsFile.from_file",
        side_effect=InstallationError,
    ):
        with pytest.raises(MissingRequirementsFoldersFiles):
            Pins.from_loader(
                loader,
                ".doc/.venv",
                suffix=SUFFIX_UNLOCKED,
                filter_by_pin=None,
            )

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

    # Absolute path automagically converted to relative path
    path_base_dir = loader.project_base
    path_venv = cast("Path", resolve_joinpath(path_base_dir, venv_path))
    lst_pins_autofixed = Pins.from_loader(
        loader,
        path_venv,
        suffix=SUFFIX_UNLOCKED,
        filter_by_pin=None,
    )
    assert len(lst_pins_autofixed) != 0

    # get_reqs lacks filter_by_pin. Returns requirement files' absolute path
    # Absolute path automagically converted to relative path
    with pytest.raises(KeyError):
        get_reqs(loader, ".dogfood", suffix_last=SUFFIX_UNLOCKED)

    abspath_reqs = get_reqs(loader, path_venv, suffix_last=SUFFIX_UNLOCKED)
    assert len(abspath_reqs) != 0

    #    filter_by_pin None --> True.
    #    If Missing requirements --> MissingRequirementsFoldersFiles
    lst_pins = Pins.from_loader(
        loader,
        venv_path,
        suffix=SUFFIX_UNLOCKED,
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

    # Ensure Pins.from_loader works
    lst_pins_0 = Pins.from_loader(
        loader,
        venv_path,
        suffix=SUFFIX_LOCKED,
        filter_by_pin=True,
    )
    is_there_will_be_pins = len(lst_pins_0) != 0
    assert is_there_will_be_pins is True

    # Failing here under Windows. See what is happening inside the function
    """
    func_path = f"{g_app_name}.lock_inspect._wrapper_pins_by_pkg"
    args = (loader, venv_path)
    kwargs = {"suffix": None, "filter_by_pin": None}
    t_ret = get_locals(func_path, _wrapper_pins_by_pkg, *args, **kwargs)  # noqa: F841
    """

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

    # Missing requirements files --> MissingRequirementsFoldersFiles
    with pytest.raises(MissingRequirementsFoldersFiles):
        get_issues(loader, venv_path)

    # Missing requirements files --> MissingRequirementsFoldersFiles
    with pytest.raises(MissingRequirementsFoldersFiles):
        fix_resolvables((), loader, venv_path, is_dry_run=True)

    #   Create requirements folder, since there are no base_relpaths
    prep_these = ("requirements/junk.deleteme",)
    prepare_folders_files(prep_these, tmp_path)

    #   Copy empties
    prep_these = []
    for suffix in (SUFFIX_IN, SUFFIX_UNLOCKED, SUFFIX_LOCKED):
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
        fix_requirements(loader, venv_path, is_dry_run=True)

    #    venv_path must be a folder. If not or no folder --> NotADirectoryError
    prep_these = (".venv/.python-version",)
    prepare_folders_files(prep_these, tmp_path)

    # missing requirements file(s) --> MissingRequirementsFoldersFiles
    with pytest.raises(MissingRequirementsFoldersFiles):
        fix_requirements(loader, venv_path, is_dry_run=True)

    # All venvs
    with pytest.raises(MissingRequirementsFoldersFiles):
        fix_requirements(loader, None, is_dry_run=True)

    #   Create requirements folder, since there are no base_relpaths
    prep_these = ("requirements/junk.deleteme",)
    prepare_folders_files(prep_these, tmp_path)

    #   Copy empties
    prep_these = []
    for suffix in (SUFFIX_IN, SUFFIX_UNLOCKED, SUFFIX_LOCKED):
        for base_relpath in base_relpaths:
            prep_these.append(f"{base_relpath}{suffix}")
        prepare_folders_files(prep_these, tmp_path)

    #    Copy real .unlock and .lock files
    for abspath_src in to_requirements_dir:
        src_abspath = str(abspath_src)
        abspath_dest = tmp_path / "requirements" / abspath_src.name
        shutil.copy(src_abspath, abspath_dest)

    # Act
    fix_requirements(loader, venv_path, is_dry_run=True)

    # None --> False
    t_results = fix_requirements(loader, venv_path, is_dry_run=None)
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
    fix_requirements(loader, venv_path, is_dry_run=1.12345)


testdata_lock_file_paths_to_relpath = (
    (
        (
            "requirements/prod.shared.in",
            "docs/requirements.in",
        ),
        (
            "#\n"
            "click==8.1.7\n"
            "    # via\n"
            "    #   -c {tmp_path!s}/docs/../requirements/prod.shared.in\n"
            "    #   click-log\n"
            "    #   scriv\n"
            "    #   sphinx-external-toc-strict\n"
            "    #   uvicorn\n"
            "sphobjinv==2.3.1.1\n"
            "    # via -r {tmp_path!s}/docs/requirements.in\n\n"
        ),
        (
            "#\n"
            "click==8.1.7\n"
            "    # via\n"
            "    #   -c docs/../requirements/prod.shared.in\n"
            "    #   click-log\n"
            "    #   scriv\n"
            "    #   sphinx-external-toc-strict\n"
            "    #   uvicorn\n"
            "sphobjinv==2.3.1.1\n"
            "    # via -r docs/requirements.in\n\n"
        ),
        "docs/requirements.lock",
    ),
)
ids_lock_file_paths_to_relpath = ("remove absolute paths from .lock file",)


@pytest.mark.parametrize(
    "seq_reqs_relpath, lock_file_contents, expected_contents, dest_relpath",
    testdata_lock_file_paths_to_relpath,
    ids=ids_lock_file_paths_to_relpath,
)
def test_lock_file_paths_to_relpath(
    seq_reqs_relpath,
    lock_file_contents,
    expected_contents,
    dest_relpath,
    tmp_path,
    prepare_folders_files,
):
    """When creating .lock files post processer abs path --> relative path."""
    # pytest --showlocals --log-level INFO -k "test_lock_file_paths_to_relpath" tests
    # prepare
    #    .in
    prepare_folders_files(seq_reqs_relpath, tmp_path)

    #    .lock create with contents
    path_doc_lock = cast("Path", resolve_joinpath(tmp_path, dest_relpath))
    path_doc_lock.write_text(lock_file_contents.format(**{"tmp_path": tmp_path}))

    # act
    _postprocess_abspath_to_relpath(path_doc_lock, tmp_path)

    # verify
    #    Within file contents, absolute path of parent folder is absent
    actual_contents = path_doc_lock.read_text()
    is_not_occur_once = str(tmp_path) not in actual_contents
    assert is_not_occur_once is True
    assert actual_contents == expected_contents


testdata_compile_one = (
    pytest.param(
        (
            Path(__file__).parent.parent.joinpath("requirements/pins.shared.in"),
            Path(__file__).parent.parent.joinpath("requirements/pip.in"),
            Path(__file__).parent.parent.joinpath("requirements/pip-tools.in"),
        ),
        "requirements/pip-tools.in",
        "requirements/pip-tools.out",
    ),
)
ids_compile_one = ("pip-tools.in --> pip-tools.lock",)


@pytest.mark.xfail(
    not is_package_installed("pip-tools"),
    reason="dependency package pip-tools is required",
)
@pytest.mark.parametrize(
    "seq_copy_these, in_relpath, out_relpath",
    testdata_compile_one,
    ids=ids_compile_one,
)
def test_compile_one(
    seq_copy_these,
    in_relpath,
    out_relpath,
    tmp_path,
):
    """Lock a .in file."""
    # pytest -vv --showlocals --log-level INFO -k "test_compile_one" tests
    path_ep = resolve_path("pip-compile")
    ep_path = str(path_ep)
    path_cwd = tmp_path
    context = ".venv"

    # prepare
    #    dest folders
    path_dir = cast("Path", resolve_joinpath(tmp_path, "requirements"))
    path_dir.mkdir(parents=True, exist_ok=True)

    #    Copy real .in files
    for abspath_src in seq_copy_these:
        src_abspath = str(abspath_src)
        abspath_dest = tmp_path / "requirements" / abspath_src.name
        shutil.copy2(src_abspath, abspath_dest)
    abspath_in = cast("Path", resolve_joinpath(tmp_path, in_relpath))
    abspath_out = cast("Path", resolve_joinpath(tmp_path, out_relpath))
    in_abspath = abspath_in.as_posix()
    out_abspath = abspath_out.as_posix()

    # Conforms to interface?
    assert isinstance(in_abspath, str)
    assert isinstance(out_abspath, str)
    assert isinstance(ep_path, str)
    assert issubclass(type(path_cwd), PurePath)
    assert context is None or isinstance(context, str)

    # act
    optabspath_out, err_details = _compile_one(
        in_abspath,
        out_abspath,
        ep_path,
        path_cwd,
        context=context,
        timeout=PurePath,
    )
    # verify
    t_failures = (err_details,)
    if err_details is not None and is_timeout(t_failures):
        pytest.skip("lock_compile requires a web connection")
    else:
        assert optabspath_out is not None
        assert issubclass(type(optabspath_out), PurePath)
        assert optabspath_out.exists() and optabspath_out.is_file()


testdata_lock_compile_live = (
    pytest.param(
        Path(__file__).parent.joinpath("_req_files", "venvs_minimal.pyproject_toml"),
        ".tools",
        (
            "requirements/pins.shared.in",
            "requirements/pip.in",
            "requirements/pip-tools.in",
            "docs/pip-tools.in",
        ),
        "docs/pip-tools.in",
        "docs/pip-tools.out",
        does_not_raise(),
    ),
    pytest.param(
        Path(__file__).parent.joinpath("_req_files", "venvs_minimal.pyproject_toml"),
        ".venv",
        (
            "requirements/pins.shared.in",
            "requirements/pip.in",
            "requirements/pip-tools.in",
            "docs/pip-tools.in",
        ),
        "requirements/pip-tools.in",
        "requirements/pip-tools.out",
        does_not_raise(),
    ),
)
ids_lock_compile_live = (
    "recipe for docs/pip-tools.in --> docs/pip-tools.lock",
    "recipe for requirements/pip-tools.in --> requirements/pip-tools.lock",
)


@pytest.mark.xfail(
    not is_package_installed("pip-tools"),
    reason="dependency package pip-tools is required",
)
@pytest.mark.parametrize(
    "path_config, venv_relpath, seq_reqs_relpath, in_relpath, out_relpath, expectation",
    testdata_lock_compile_live,
    ids=ids_lock_compile_live,
)
def test_lock_compile_live(
    path_config,
    venv_relpath,
    seq_reqs_relpath,
    in_relpath,
    out_relpath,
    expectation,
    tmp_path,
    path_project_base,
    prep_pyproject_toml,
    prepare_folders_files,
    caplog,
    has_logging_occurred,
):
    """Test lock compile"""
    # pytest -vv --showlocals --log-level INFO -k "test_lock_compile_live" tests
    LOGGING["loggers"][g_app_name]["propagate"] = True
    logging.config.dictConfig(LOGGING)
    logger = logging.getLogger(name=g_app_name)
    logger.addHandler(hdlr=caplog.handler)
    caplog.handler.level = logger.level

    path_cwd = path_project_base()
    # prepare
    #    pyproject.toml
    path_f = prep_pyproject_toml(path_config, tmp_path)

    # Act
    #    Test without copying over support files
    loader = VenvMapLoader(path_f.as_posix())
    with pytest.raises(NotADirectoryError):
        lock_compile(loader, venv_relpath)
    #    Test not filtering by venv relpath
    with pytest.raises(NotADirectoryError):
        lock_compile(loader, None)

    #    create folders (venv and requirements folders)
    venv_relpaths = (
        ".venv",
        ".tools",
        "requirements",
        "docs",
    )
    for create_relpath in venv_relpaths:
        abspath_venv = cast("Path", resolve_joinpath(tmp_path, create_relpath))
        abspath_venv.mkdir(parents=True, exist_ok=True)

    # prepare
    #    copy just the reqs .in --> .lock
    abspath_src = cast("Path", resolve_joinpath(path_cwd, in_relpath))
    abspath_dest = cast("Path", resolve_joinpath(tmp_path, in_relpath))
    shutil.copy2(abspath_src, abspath_dest)

    # Act
    #    Test without copying over support files
    loader = VenvMapLoader(path_f.as_posix())
    with pytest.raises(MissingRequirementsFoldersFiles):
        lock_compile(loader, venv_relpath)

    # prepare
    #    copy (ALL not just one venv) requirements to respective folders
    for relpath_f in seq_reqs_relpath:
        abspath_src = cast("Path", resolve_joinpath(path_cwd, relpath_f))
        abspath_dest = cast("Path", resolve_joinpath(tmp_path, relpath_f))
        shutil.copy2(abspath_src, abspath_dest)

    # Act
    loader = VenvMapLoader(path_f.as_posix())

    # overloaded function prepare_pairs
    with expectation:
        t_ins, files = filter_by_venv_relpath(loader, venv_relpath)
    if isinstance(expectation, does_not_raise):
        gen = prepare_pairs(t_ins)
        assert isinstance(gen, Generator)
        list(gen)  # execute Generator
        gen = prepare_pairs(files, path_cwd=tmp_path)
        assert isinstance(gen, Generator)
        list(gen)  # execute Generator
        # path_cwd must be provided and be a Path
        with pytest.raises(AssertionError):
            gen = prepare_pairs(files, path_cwd=None)
            list(gen)  # execute Generator

        # Fallback
        with pytest.raises(NotImplementedError):
            gen = prepare_pairs(None)
            list(gen)

    with expectation:
        """
        func_path = f"{g_app_name}.lock_inspect.lock_compile"
        args = (loader, venv_relpath)
        kwargs = {}
        t_ret = get_locals(func_path, lock_compile, *args, **kwargs)  # noqa: F841
        t_status, t_locals = t_ret
        """
        t_status = lock_compile(
            loader,
            venv_relpath,
            timeout=PurePath,
        )
    # Verify
    if isinstance(expectation, does_not_raise):
        # assert has_logging_occurred(caplog)
        assert t_status is not None
        assert isinstance(t_status, tuple)
        t_compiled, t_failures = t_status
        assert isinstance(t_failures, tuple)
        assert isinstance(t_compiled, tuple)
        if is_timeout(t_failures):
            pytest.skip("lock_compile requires a web connection")
        else:
            is_no_failures = len(t_failures) == 0
            assert is_no_failures
            compiled_count = len(t_compiled)
            assert compiled_count == 1


@pytest.mark.parametrize(
    "path_config, venv_relpath, seq_reqs_relpath, in_relpath, out_relpath, expectation",
    testdata_lock_compile_live,
    ids=ids_lock_compile_live,
)
def test_unlock_compile_live(
    path_config,
    venv_relpath,
    seq_reqs_relpath,
    in_relpath,
    out_relpath,
    expectation,
    tmp_path,
    path_project_base,
    prep_pyproject_toml,
    prepare_folders_files,
    caplog,
    has_logging_occurred,
):
    """Test lock compile"""
    # pytest -vv --showlocals --log-level INFO -k "test_unlock_compile_live" tests
    LOGGING["loggers"][g_app_name]["propagate"] = True
    logging.config.dictConfig(LOGGING)
    logger = logging.getLogger(name=g_app_name)
    logger.addHandler(hdlr=caplog.handler)
    caplog.handler.level = logger.level

    path_cwd = path_project_base()
    # prepare
    #    pyproject.toml
    path_f = prep_pyproject_toml(path_config, tmp_path)

    # Act
    #    Test without copying over support files
    loader = VenvMapLoader(path_f.as_posix())
    with pytest.raises(NotADirectoryError):
        gen = unlock_compile(loader, venv_relpath)
        list(gen)

    #    create folders (venv and requirements folders)
    venv_relpaths = (
        ".venv",
        ".tools",
        "requirements",
        "docs",
    )
    for create_relpath in venv_relpaths:
        abspath_venv = cast("Path", resolve_joinpath(tmp_path, create_relpath))
        abspath_venv.mkdir(parents=True, exist_ok=True)

    #    Test without copying over support files
    loader = VenvMapLoader(path_f.as_posix())
    with pytest.raises(MissingRequirementsFoldersFiles):
        gen = unlock_compile(loader, venv_relpath)
        list(gen)

    # prepare
    #    copy (ALL not just one venv) requirements to respective folders
    for relpath_f in seq_reqs_relpath:
        abspath_src = cast("Path", resolve_joinpath(path_cwd, relpath_f))
        abspath_dest = cast("Path", resolve_joinpath(tmp_path, relpath_f))
        shutil.copy2(abspath_src, abspath_dest)

    # prepare
    #    copy just the reqs .in --> .lock
    abspath_src = cast("Path", resolve_joinpath(path_cwd, in_relpath))
    abspath_dest = cast("Path", resolve_joinpath(tmp_path, in_relpath))
    shutil.copy2(abspath_src, abspath_dest)

    # Act
    #    Without filtering by venv relpath
    loader = VenvMapLoader(path_f.as_posix())

    with expectation:
        gen = unlock_compile(
            loader,
            venv_relpath,
        )
        abspath_unlocks = list(gen)
    # Verify
    if isinstance(expectation, does_not_raise):
        assert abspath_unlocks is not None
        assert isinstance(abspath_unlocks, Sequence)
        assert len(abspath_unlocks) != 0

    # Act
    #    With filtering by venv relpath
    with expectation:
        gen = unlock_compile(
            loader,
            None,
        )
        abspath_unlocks = list(gen)
    # Verify
    if isinstance(expectation, does_not_raise):
        assert abspath_unlocks is not None
        assert isinstance(abspath_unlocks, Sequence)
        assert len(abspath_unlocks) != 0
