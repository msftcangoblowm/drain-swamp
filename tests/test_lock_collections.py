"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

Unit test -- Module

.. code-block:: shell

   python -m coverage run --source='drain_swamp.lock_collections' -m pytest \
   --showlocals tests/test_lock_collections.py && coverage report \
   --data-file=.coverage --include="**/lock_collections.py"

"""

import logging
import logging.config
import shutil
from contextlib import nullcontext as does_not_raise
from pathlib import Path
from typing import cast

import pytest

from drain_swamp._safe_path import resolve_joinpath
from drain_swamp.constants import (
    LOGGING,
    SUFFIX_IN,
    SUFFIX_LOCKED,
    g_app_name,
)
from drain_swamp.exceptions import MissingRequirementsFoldersFiles
from drain_swamp.lock_collections import Ins
from drain_swamp.lock_datum import InFileType
from drain_swamp.lock_filepins import FilePins
from drain_swamp.lock_util import replace_suffixes_last
from drain_swamp.pep518_venvs import VenvMapLoader

testdata_why_did_you_do_that = (
    (
        Path(__file__).parent.joinpath("_req_files", "venvs_minimal.pyproject_toml"),
        ".tools",
        ("docs/pip-tools",),
        pytest.raises(MissingRequirementsFoldersFiles),
    ),
    (
        Path(__file__).parent.joinpath("_req_files", "venvs_minimal.pyproject_toml"),
        ".dogfood",
        ("docs/pip-tools",),
        pytest.raises(KeyError),
    ),
)
ids_why_did_you_do_that = (
    "missing support requirement files",
    "no such venv",
)


@pytest.mark.parametrize(
    "path_config, venv_relpath, req_files, expectation",
    testdata_why_did_you_do_that,
    ids=ids_why_did_you_do_that,
)
def test_why_did_you_do_that(
    path_config,
    venv_relpath,
    req_files,
    expectation,
    tmp_path,
    path_project_base,
    prepare_folders_files,
    prep_pyproject_toml,
):
    """venv relpath is not supposed to be an absolute path."""
    # pytest --showlocals --log-level INFO -k "test_why_did_you_do_that" tests
    path_cwd = path_project_base()
    abspath_venv = cast("Path", resolve_joinpath(tmp_path, venv_relpath))
    seq_base_dir = (
        str(Path(venv_relpath).joinpath(".python-version")),
        str(Path("requirements").joinpath("empty.txt")),
        str(Path("docs").joinpath("empty.txt")),
    )

    # prepare
    #    pyproject.toml
    abspath_config_dest = prep_pyproject_toml(path_config, tmp_path)
    config_dest_abspath = str(abspath_config_dest)

    #    folders
    prepare_folders_files(seq_base_dir, tmp_path)

    #    requirements files -- direct and maybe support files
    for req_relpath_src in req_files:
        abspath_src = cast("Path", resolve_joinpath(path_cwd, req_relpath_src))
        abspath_src_in = cast(
            "Path",
            resolve_joinpath(
                abspath_src.parent,
                f"{abspath_src.name}{SUFFIX_IN}",
            ),
        )
        src_in_abspath = str(abspath_src_in)
        abspath_dest = cast("Path", resolve_joinpath(tmp_path, req_relpath_src))
        abspath_dest_in = cast(
            "Path",
            resolve_joinpath(
                abspath_dest.parent,
                f"{abspath_dest.name}{SUFFIX_IN}",
            ),
        )
        shutil.copy(src_in_abspath, abspath_dest_in)

    loader = VenvMapLoader(config_dest_abspath)
    #    Will convert abspath_venv --> venv_relpath
    ins = Ins(loader, abspath_venv)
    #    __len__ and __iter__
    assert len(iter(ins)) == 0
    #    __contains__
    assert None not in ins
    assert 7.23 not in ins

    # act
    #    suffix_last .dogfood --> .in then
    #    Did not prepare the requirements files --> MissingRequirementsFoldersFiles
    with expectation:
        ins.load(suffix_last=".dogfood")


testdata_ins_realistic = (
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
        ),
        (
            (
                Path(__file__).parent.parent.joinpath(
                    "requirements",
                    "prod.shared.in",
                ),
                "requirements/prod.shared.in",
            ),
            (
                Path(__file__).parent.parent.joinpath(
                    "requirements",
                    "pins.shared.in",
                ),
                "requirements/pins.shared.in",
            ),
            (
                Path(__file__).parent.parent.joinpath(
                    "requirements",
                    "pins-cffi.in",
                ),
                "requirements/pins-cffi.in",
            ),
        ),
        does_not_raise(),
        8,
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
        ),
        (
            (
                Path(__file__).parent.parent.joinpath(
                    "requirements",
                    "prod.shared.in",
                ),
                "requirements/prod.shared.in",
            ),
            (
                Path(__file__).parent.parent.joinpath(
                    "requirements",
                    "pins.shared.in",
                ),
                "requirements/pins.shared.in",
            ),
        ),
        pytest.raises(MissingRequirementsFoldersFiles),
        8,
    ),
)
ids_ins_realistic = (
    "Has both requirements and constraints",
    "missing a support file",
)


@pytest.mark.parametrize(
    (
        "path_config, venv_path, seq_reqs_primary, seq_reqs_support, "
        "expectation, pkg_pin_count_expected"
    ),
    testdata_ins_realistic,
    ids=ids_ins_realistic,
)
def test_ins_realistic(
    path_config,
    venv_path,
    seq_reqs_primary,
    seq_reqs_support,
    expectation,
    pkg_pin_count_expected,
    tmp_path,
    prep_pyproject_toml,
    prepare_folders_files,
    caplog,
    has_logging_occurred,
):
    """test drain_swamp.lock_collections.Ins"""
    # pytest -vv --showlocals --log-level INFO -k "test_ins_realistic" tests
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
    suffixes = (SUFFIX_IN, SUFFIX_LOCKED)
    seq_rel_paths = []
    for suffix in suffixes:
        for base_path in bases_path:
            seq_rel_paths.append(f"{base_path}{suffix}")
    prepare_folders_files(seq_rel_paths, tmp_path)

    for t_paths in seq_reqs_primary:
        src_abspath, dest_relpath = t_paths

        #    overwrite 'requirements/dev.in'
        abspath_dest = cast("Path", resolve_joinpath(tmp_path, dest_relpath))

        shutil.copy(src_abspath, abspath_dest)

        #    pip-compile -o [file].lock [file].in
        #    careful no .shared
        src_abspath_lock = replace_suffixes_last(src_abspath, SUFFIX_LOCKED)
        abspath_dest_lock = replace_suffixes_last(abspath_dest, SUFFIX_LOCKED)
        shutil.copy(src_abspath_lock, abspath_dest_lock)

    is_first = True
    for t_paths in seq_reqs_support:
        src_abspath, dest_relpath = t_paths

        #    overwrite 'requirements/dev.in'
        abspath_dest = cast("Path", resolve_joinpath(tmp_path, dest_relpath))

        if is_first:
            is_first = False
            abspath_dest_0 = abspath_dest

        shutil.copy(src_abspath, abspath_dest)

    with expectation:
        ins = Ins(loader, venv_path)
        ins.load(suffix_last=None)
    if isinstance(expectation, does_not_raise):
        repr_ins = repr(ins)
        assert isinstance(repr_ins, str)

        pkg_ins_count_actual = len(ins)
        fpins_abspath = [fpin.file_abspath for fpin in ins._file_pins]
        msg_mismatch = f"expected count doesn't match filepins {fpins_abspath}"
        assert pkg_ins_count_actual == pkg_pin_count_expected, msg_mismatch

        # Loop Iterator
        for fpins in ins:
            assert isinstance(fpins, FilePins)

        # Loop Iterator again; the magic reusable Iterator!
        for fpins in ins:
            assert isinstance(fpins, FilePins)

        fpin_maybe = ins.get_by_abspath(abspath_dest_0, set_name=InFileType.ZEROES)
        assert fpin_maybe is not None
        assert isinstance(fpin_maybe, FilePins)
        #    __contains__
        assert fpin_maybe in ins

        invalids = (
            None,
            1.234,
        )
        for invalid in invalids:
            # not a InFileType
            fpin_maybe = ins.get_by_abspath(abspath_dest_0, set_name=invalid)
            assert fpin_maybe is None
            # invalid abspath_dest_0 --> ValueError
            with pytest.raises(ValueError):
                ins.get_by_abspath(invalid, set_name=InFileType.ZEROES)

        """write .unlock files. Should confirm contains own and ancestors
        packages.

        These files are skipped and will not produce a .unlock file

        - ``.shared.in`` files starting with ``pin``

        """
        gen = ins.write()
        list(gen)
