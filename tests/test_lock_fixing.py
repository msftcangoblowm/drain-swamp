"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

Unit test -- Module

.. code-block:: shell

   python -m coverage run --source='drain_swamp.lock_fixing' -m pytest \
   --showlocals tests/test_lock_fixing.py && coverage report \
   --data-file=.coverage --include="**/lock_fixing.py"

"""

import logging
import logging.config
import shutil

import pytest
from logging_strict.tech_niques import get_locals  # noqa: F401

from drain_swamp.constants import (
    LOGGING,
    SUFFIX_IN,
    SUFFIX_LOCKED,
    g_app_name,
)
from drain_swamp.exceptions import MissingRequirementsFoldersFiles
from drain_swamp.lock_fixing import (  # noqa: F401
    Fixing,
    _fix_resolvables,
    _load_once,
    fix_requirements_lock,
)
from drain_swamp.lock_util import replace_suffixes_last
from drain_swamp.pep518_venvs import VenvMapLoader

from .testdata_lock_inspect import (
    ids_resolve_resolvable_conflicts,
    testdata_resolve_resolvable_conflicts,
)


@pytest.mark.parametrize(
    "path_pyproject_toml, venv_path, base_relpaths, to_requirements_dir, expected_resolvable_count, expected_unresolvable_count,",
    testdata_resolve_resolvable_conflicts,
    ids=ids_resolve_resolvable_conflicts,
)
def test_locks_before_fix(
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
    """Fix .locks only."""
    # pytest -vv --showlocals --log-level INFO -k "test_locks_before_fix" tests
    LOGGING["loggers"][g_app_name]["propagate"] = True
    logging.config.dictConfig(LOGGING)
    logger = logging.getLogger(name=g_app_name)
    logger.addHandler(hdlr=caplog.handler)
    caplog.handler.level = logger.level

    # prepare
    #    Copy to base dir
    path_dest_pyproject_toml = prep_pyproject_toml(path_pyproject_toml, tmp_path)

    loader = VenvMapLoader(path_dest_pyproject_toml.as_posix())

    with pytest.raises(NotADirectoryError):
        Fixing(loader, venv_path)

    invalids = (
        None,
        1.234,
    )
    for invalid in invalids:
        with pytest.raises(TypeError):
            Fixing(loader, invalid)

    #    venv_path must be a folder. If not or no folder --> NotADirectoryError
    prep_these = (".venv/.python-version",)
    prepare_folders_files(prep_these, tmp_path)

    with pytest.raises(MissingRequirementsFoldersFiles):
        Fixing(loader, venv_path)

    prep_these = ("requirements/junk.deleteme",)
    prepare_folders_files(prep_these, tmp_path)

    #   Copy empties
    prep_these = []
    for suffix in (SUFFIX_IN, SUFFIX_LOCKED):
        for base_relpath in base_relpaths:
            prep_these.append(f"{base_relpath}{suffix}")
        prepare_folders_files(prep_these, tmp_path)

    #    Copy real .unlock --> .in files
    for abspath_src in to_requirements_dir:
        if abspath_src.suffix == ".unlock":
            src_abspath = str(abspath_src)
            abspath_dest = tmp_path / "requirements" / abspath_src.name
            abspath_dest_in = replace_suffixes_last(abspath_dest, SUFFIX_IN)
            shutil.copy(src_abspath, abspath_dest_in)

    #    Copy real .lock files
    for abspath_src in to_requirements_dir:
        if abspath_src.suffix == ".lock":
            src_abspath = str(abspath_src)
            abspath_dest = tmp_path / "requirements" / abspath_src.name
            shutil.copy(src_abspath, abspath_dest)

    # Act
    t_fixing = Fixing(loader, venv_path)
    t_fixing.get_issues()
    lst_resolvables = t_fixing.resolvables
    lst_unresolvables = t_fixing.unresolvables

    """
    func_path = f"{g_app_name}.lock_fixing._load_once"
    args = (t_fixing._ins, t_fixing._locks, t_fixing._venv_relpath)
    kwargs = {}
    t_ret = get_locals(func_path, _load_once, *args, **kwargs)  # noqa: F841
    assert isinstance(t_ret, Sequence)
    assert len(t_ret) == 2
    t_out, t_locals = t_ret
    """
    pass

    actual_unresolvables_count = len(lst_unresolvables)
    actual_resolvables_count = len(lst_resolvables)
    assert actual_resolvables_count == expected_resolvable_count
    assert actual_unresolvables_count == expected_unresolvable_count

    t_fixing.fix_resolvables(is_dry_run=None)
    msgs_issue = t_fixing.fixed_issues
    msgs_shared = t_fixing.resolvable_shared
    msgs_issue_count = len(msgs_issue)  # noqa: F841
    msgs_shared_count = len(msgs_shared)
    # assert actual_resolvables_count == msgs_issue_count
    assert msgs_shared_count == 1

    _fix_resolvables(
        t_fixing._resolvables,
        t_fixing._locks,
        t_fixing._venv_relpath,
        is_dry_run=True,
        suffixes=None,
    )

    # assert has_logging_occurred(caplog)
    # assert False is True
    pass


@pytest.mark.parametrize(
    "path_pyproject_toml, venv_path, base_relpaths, to_requirements_dir, expected_resolvable_count, expected_unresolvable_count,",
    testdata_resolve_resolvable_conflicts,
    ids=ids_resolve_resolvable_conflicts,
)
def test_fix_requirements_lock(
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
    """Test fix_requirements_lock"""
    # pytest -vv --showlocals --log-level INFO -k "test_fix_requirements_lock" tests
    LOGGING["loggers"][g_app_name]["propagate"] = True
    logging.config.dictConfig(LOGGING)
    logger = logging.getLogger(name=g_app_name)
    logger.addHandler(hdlr=caplog.handler)
    caplog.handler.level = logger.level

    # prepare
    #    Copy to base dir
    path_dest_pyproject_toml = prep_pyproject_toml(path_pyproject_toml, tmp_path)

    loader = VenvMapLoader(path_dest_pyproject_toml.as_posix())

    with pytest.raises(NotADirectoryError):
        fix_requirements_lock(loader, venv_path, is_dry_run=1.234)
        Fixing(loader, venv_path)

    invalids = (
        None,
        1.234,
    )
    for invalid in invalids:
        with pytest.raises(TypeError):
            fix_requirements_lock(loader, invalid, is_dry_run=None)

    #    venv_path must be a folder. If not or no folder --> NotADirectoryError
    prep_these = (".venv/.python-version",)
    prepare_folders_files(prep_these, tmp_path)

    with pytest.raises(MissingRequirementsFoldersFiles):
        fix_requirements_lock(loader, venv_path, is_dry_run=True)

    prep_these = ("requirements/junk.deleteme",)
    prepare_folders_files(prep_these, tmp_path)

    #   Copy empties
    prep_these = []
    for suffix in (SUFFIX_IN, SUFFIX_LOCKED):
        for base_relpath in base_relpaths:
            prep_these.append(f"{base_relpath}{suffix}")
        prepare_folders_files(prep_these, tmp_path)

    #    Copy real .unlock --> .in files
    for abspath_src in to_requirements_dir:
        if abspath_src.suffix == ".unlock":
            src_abspath = str(abspath_src)
            abspath_dest = tmp_path / "requirements" / abspath_src.name
            abspath_dest_in = replace_suffixes_last(abspath_dest, SUFFIX_IN)
            shutil.copy(src_abspath, abspath_dest_in)

    #    Copy real .lock files
    for abspath_src in to_requirements_dir:
        if abspath_src.suffix == ".lock":
            src_abspath = str(abspath_src)
            abspath_dest = tmp_path / "requirements" / abspath_src.name
            shutil.copy(src_abspath, abspath_dest)

    t_ret = fix_requirements_lock(loader, venv_path)
    msgs_fixed, lst_unresolvables, msgs_shared = t_ret
    assert isinstance(msgs_fixed, list)
    assert isinstance(lst_unresolvables, list)
    assert isinstance(msgs_shared, list)
