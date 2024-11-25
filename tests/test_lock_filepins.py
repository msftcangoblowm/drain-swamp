"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

Unit test -- Module

.. code-block:: shell

   python -m coverage run --source='drain_swamp.lock_filepins' -m pytest \
   --showlocals tests/test_lock_filepins.py && coverage report \
   --data-file=.coverage --include="**/lock_filepins.py"

"""

import logging
import logging.config
import operator
import shutil
from collections.abc import Sequence
from contextlib import nullcontext as does_not_raise
from pathlib import (
    Path,
    PurePath,
)
from typing import cast
from unittest.mock import patch

import pytest
from pip_requirements_parser import InstallationError

from drain_swamp._safe_path import resolve_joinpath
from drain_swamp.constants import (
    LOGGING,
    SUFFIX_IN,
    SUFFIX_LOCKED,
    SUFFIX_UNLOCKED,
    g_app_name,
)
from drain_swamp.exceptions import (
    MissingPackageBaseFolder,
    MissingRequirementsFoldersFiles,
)
from drain_swamp.lock_datum import PinDatum
from drain_swamp.lock_filepins import (
    FilePins,
    get_path_cwd,
)
from drain_swamp.lock_loader import LoaderPinDatum
from drain_swamp.lock_util import replace_suffixes_last
from drain_swamp.pep518_venvs import VenvMapLoader

testdata_get_path_cwd_exception = (
    (
        None,
        pytest.raises(MissingPackageBaseFolder),
    ),
    (
        1.234,
        pytest.raises(MissingPackageBaseFolder),
    ),
)
ids_get_path_cwd_exception = (
    "unsupported type None",
    "unsupported type float",
)


@pytest.mark.parametrize(
    "loader, expectation",
    testdata_get_path_cwd_exception,
    ids=ids_get_path_cwd_exception,
)
def test_get_path_cwd_exception(
    loader,
    expectation,
):
    """Real loader not supplied. Test of bad input."""
    # pytest -vv --showlocals --log-level INFO -k "test_get_path_cwd_exception" tests
    with expectation:
        get_path_cwd(loader)


def test_get_path_cwd_normal(
    path_project_base,
):
    """Demonstrate drain_swamp package pyproject.toml is not cwd."""
    # pytest -vv --showlocals --log-level INFO -k "test_get_path_cwd_normal" tests
    path_cwd_actual = path_project_base()

    # reverse search for the pyproject.toml file
    # possible exceptions FileNotFoundError LookupError
    cwd_abspath = str(path_cwd_actual)
    loader = VenvMapLoader(cwd_abspath)
    venvs_relpath = loader.venv_relpaths
    assert isinstance(venvs_relpath, Sequence)
    assert len(venvs_relpath) != 0

    # prepare
    """    using drain_swamp pyproject.toml which definitely exists and
    contains [[tool.venvs]] sections. No need to copy a pyproject.toml
    into tmp_path"""
    pass

    expectation = does_not_raise()
    with expectation:
        path_package_base_folder = get_path_cwd(loader)
    if isinstance(expectation, does_not_raise):
        assert issubclass(type(path_package_base_folder), PurePath)
        assert path_cwd_actual == path_package_base_folder


testdata_pindatum_realistic = (
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
                "requirements/dev.in",
            ),
            (
                Path(__file__).parent.joinpath(
                    "_req_files",
                    "prod.shared.unlock",
                ),
                "requirements/prod.shared.in",
            ),
        ),
        (
            "requirements/pip-tools",
            "requirements/pip",
            "requirements/prod.shared",
            "requirements/kit",
            "requirements/tox",
            "requirements/mypy",
            "requirements/manage",
            "requirements/dev",
        ),
    ),
    (
        Path(__file__).parent.joinpath(
            "_req_files",
            "venvs.pyproject_toml",
        ),
        ".venv",
        (
            (
                Path(__file__).parent.parent.joinpath(
                    "requirements",
                    "dev.in",
                ),
                "requirements/dev.in",
            ),
            (
                Path(__file__).parent.joinpath(
                    "_req_files",
                    "prod.shared.unlock",
                ),
                "requirements/prod.shared.in",
            ),
        ),
        (
            "requirements/pip-tools",
            "requirements/pip",
            "requirements/prod.shared",
            "requirements/kit",
            "requirements/tox",
            "requirements/mypy",
            "requirements/manage",
            "requirements/dev",
        ),
    ),
)
ids_pindatum_realistic = (
    "Parse venv requirements files into Pins",
    "has two constraints and a requirement",
)


@pytest.mark.parametrize(
    "path_config, venv_path, seq_reqs, bases_relpath",
    testdata_pindatum_realistic,
    ids=ids_pindatum_realistic,
)
def test_pindatum_realistic(
    path_config,
    venv_path,
    seq_reqs,
    bases_relpath,
    tmp_path,
    prep_pyproject_toml,
    prepare_folders_files,
    caplog,
):
    """test FilePins."""
    # pytest -vv --showlocals --log-level INFO -k "test_pindatum_realistic" tests
    LOGGING["loggers"][g_app_name]["propagate"] = True
    logging.config.dictConfig(LOGGING)
    logger = logging.getLogger(name=g_app_name)
    logger.addHandler(hdlr=caplog.handler)
    caplog.handler.level = logger.level

    # prepare
    #    pyproject.toml or [something].pyproject_toml
    path_dest_config = prep_pyproject_toml(path_config, tmp_path)
    #    Careful path must be a str
    loader = VenvMapLoader(path_dest_config.as_posix())
    path_base_dir = loader.project_base

    #    venv folder must exist. other [[tool.venvs]] venv folders need not exist
    venvs_path = (Path(venv_path).joinpath(".python-version"),)
    prepare_folders_files(venvs_path, tmp_path)

    # Other venv, requirement files not prepared
    with pytest.raises(NotADirectoryError):
        LoaderPinDatum()(
            loader,
            ".doc/.venv",
            suffix=SUFFIX_UNLOCKED,
            filter_by_pin=None,
        )

    #    requirements empty files and folders; no .unlock or .lock files
    seq_rel_paths = (
        ".doc/.venv/.python-version",
        ".venv/.python-version",
        "requirements/pins.shared.in",
        "docs/requirements.in",
    )
    prepare_folders_files(seq_rel_paths, tmp_path)

    # Other venv, requirement files not prepared
    with pytest.raises(MissingRequirementsFoldersFiles):
        LoaderPinDatum()(
            loader,
            ".doc/.venv",
            suffix=SUFFIX_UNLOCKED,
            filter_by_pin=None,
        )

    #    requirements empty files and folders
    suffixes = (SUFFIX_IN, SUFFIX_UNLOCKED, SUFFIX_LOCKED)
    seq_rel_paths = []
    for suffix in suffixes:
        for base_path in bases_relpath:
            seq_rel_paths.append(f"{base_path}{suffix}")
    prepare_folders_files(seq_rel_paths, tmp_path)

    for t_paths in seq_reqs:
        src_abspath, dest_relpath = t_paths

        #    overwrite 'requirements/dev.unlock'
        abspath_dest = cast("Path", resolve_joinpath(tmp_path, dest_relpath))
        abspath_dest_in = replace_suffixes_last(abspath_dest, suffix_last=SUFFIX_IN)
        shutil.copy(src_abspath, abspath_dest_in)

        #    pip-compile -o [file].lock [file].unlock
        #    careful no .shared
        src_abspath_lock = replace_suffixes_last(src_abspath, SUFFIX_LOCKED)
        abspath_dest_lock = replace_suffixes_last(abspath_dest_in, SUFFIX_LOCKED)
        shutil.copy(src_abspath_lock, abspath_dest_lock)

    # Cause pip_requirements_parser.RequirementsFile.from_file to fail
    with patch(
        "pip_requirements_parser.RequirementsFile.from_file",
        side_effect=InstallationError,
    ):
        with pytest.raises(MissingRequirementsFoldersFiles):
            LoaderPinDatum()(
                loader,
                ".doc/.venv",
                suffix=SUFFIX_UNLOCKED,
                filter_by_pin=None,
            )

    # Unsupported file extension. Not in (.in, .lock, .unlock)
    abspath_pins_shared_in = cast("Path", resolve_joinpath(tmp_path, seq_rel_paths[0]))
    abspath_pins_shared_nonsense = replace_suffixes_last(
        abspath_pins_shared_in, ".nonsense"
    )
    with pytest.raises(ValueError):
        FilePins(abspath_pins_shared_nonsense)
    abspath_dogfood_in = cast(
        "Path",
        resolve_joinpath(
            tmp_path,
            f"requirements/dogfood{SUFFIX_IN}",
        ),
    )
    with pytest.raises(MissingRequirementsFoldersFiles):
        FilePins(abspath_dogfood_in)

    # FilePins append a PinDatum (package pip)
    #    dest [abspath]/requirements/pins.shared.in
    fpins = FilePins(abspath_pins_shared_in)
    fpins_before_actual = len(fpins)
    pindatum_pip = PinDatum(
        abspath_pins_shared_in,
        "pip",
        '"pip<24.2; python_version < "3.10"',
        ["<24.2"],
        ['python_version < "3.10"'],
    )
    pins = fpins._pins
    pins.append(pindatum_pip)
    fpins._pins = pins
    fpins._iter = iter(fpins._pins)
    fpins_after_actual = len(fpins)
    assert fpins_after_actual == fpins_before_actual + 1

    # FilePins.__repr__
    repr_fpins = repr(fpins)
    assert isinstance(repr_fpins, str)

    # FilePins.__hash__ and FilePins.__eq__
    int_hash_left = hash(fpins)
    assert isinstance(int_hash_left, int)
    right = fpins.file_abspath
    int_hash_right = hash((right,))
    assert int_hash_left == int_hash_right

    #    Path abspath
    assert issubclass(type(right), PurePath)
    assert operator.eq(fpins, right) is True
    assert fpins.__eq__(right)
    assert fpins == right
    #    str abspath
    assert fpins == str(right)
    #    None
    assert fpins is not None
    #    unsupported type
    assert fpins != 4
    #    same type
    fpins_right_0 = FilePins(abspath_dest_in)
    assert fpins != fpins_right_0

    # FilePins.__lt__ (to support sorted)
    #    unsupported types
    invalids = (
        None,
        1.234,
    )
    for invalid in invalids:
        with pytest.raises(TypeError):
            operator.lt(fpins, invalid)
    #    Same folder
    assert fpins < fpins_right_0
    #    different folder
    abspath_pins_docs_requirements_in = cast(
        "Path",
        resolve_joinpath(
            tmp_path,
            "docs/requirements.in",
        ),
    )
    fpins_right_1 = FilePins(abspath_pins_docs_requirements_in)
    is_left_greater = fpins > fpins_right_1
    assert is_left_greater

    # FilePins.__contains__
    assert pindatum_pip in fpins
    assert None not in fpins
    assert 3 not in fpins

    # FilePins.depth property
    assert fpins.depth == 0

    # FilePins.relpath
    with pytest.raises(MissingPackageBaseFolder):
        fpins.relpath(None)
    fpins.relpath(loader).as_posix() == "requirements/pins.shared.in"

    # FilePins.by_pkg
    lst_out = fpins.by_pkg(None)
    assert isinstance(lst_out, list)
    assert len(lst_out) == 0
    lst_out = fpins.by_pkg("pip")
    assert isinstance(lst_out, list)
    assert len(lst_out) == 1

    # FilePins.by_pin_or_qualifier
    gen = fpins.by_pin_or_qualifier()
    lst_pins_notable = list(gen)
    lst_pins_notable_count = len(lst_pins_notable)
    assert lst_pins_notable_count != 0

    # Loop Iterator
    for pin_found in fpins:
        assert isinstance(pin_found, PinDatum)

    # Loop Iterator again; the magic reusable Iterator!
    for pin_found in fpins:
        assert isinstance(pin_found, PinDatum)

    # Identify pins from .in files
    #    Absolute path automagically converted to relative path
    path_venv = cast("Path", resolve_joinpath(path_base_dir, venv_path))
    set_pins_autofixed = LoaderPinDatum()(
        loader,
        path_venv,
        suffix=SUFFIX_IN,
        filter_by_pin=None,
    )
    assert isinstance(set_pins_autofixed, set)
    assert len(set_pins_autofixed) != 0

    # filter by pin and .lock file
    set_pindatum_0 = LoaderPinDatum()(
        loader,
        venv_path,
        suffix=SUFFIX_LOCKED,
        filter_by_pin=True,
    )
    is_there_will_be_pins = len(set_pindatum_0) != 0
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
    pindatum_by_pkg = fpins.by_pkg("pip")
    assert isinstance(pindatum_by_pkg, list)
    assert isinstance(list(pindatum_by_pkg)[0], PinDatum)


testdata_filepins_resolve = (
    (
        Path(__file__).parent.parent.joinpath(
            "docs",
            "pip-tools.in",
        ),
        "../requirements/pins.shared.in",
    ),
)
ids_filepins_resolve = ("Resolve",)


@pytest.mark.parametrize(
    "abspath_f, constraint_relpath",
    testdata_filepins_resolve,
    ids=ids_filepins_resolve,
)
def test_filepins_resolve(
    abspath_f,
    constraint_relpath,
):
    """Read a FilePins. Resolve, from a set, discards a constraint."""
    # pytest -vv --showlocals --log-level INFO -k "test_filepins_resolve" tests
    fpins_0 = FilePins(abspath_f)
    # nonexistant FilePins attribute, plural --> AssertionError
    with pytest.raises(AssertionError):
        fpins_0.resolve(constraint_relpath, plural="dogfood")

    # nonsense singular --> 'constaint'
    fpins_0.resolve(constraint_relpath, singular="dogfood")
