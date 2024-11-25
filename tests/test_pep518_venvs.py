"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

Unit test -- Module

.. code-block:: shell

   python -m coverage run --source='drain_swamp.pep518_venvs' -m pytest \
   --showlocals tests/test_pep518_venvs.py && coverage report \
   --data-file=.coverage --include="**/pep518_venvs.py"

"""

import shutil
from contextlib import nullcontext as does_not_raise
from pathlib import Path
from typing import cast

import pytest

from drain_swamp._safe_path import resolve_joinpath
from drain_swamp.constants import SUFFIX_IN
from drain_swamp.exceptions import (
    MissingPackageBaseFolder,
    MissingRequirementsFoldersFiles,
)
from drain_swamp.pep518_venvs import (
    VenvMap,
    VenvMapLoader,
    VenvReq,
    get_reqs,
)


def test_venvmaploader(tmp_path, prep_pyproject_toml, prepare_folders_files):
    """Test VenvMapLoader."""
    # pytest --showlocals --log-level INFO -k "test_venvmaploader" tests
    # Chaos monkey says, 'Lets be uncareful'
    with pytest.raises(FileNotFoundError):
        VenvMapLoader(3)

    # No pyproject.toml or .pyproject_toml found --> TypeError
    with pytest.raises(FileNotFoundError):
        VenvMapLoader(tmp_path)

    # Finds an empty file --> LookupError
    path_dest_pyproject_toml = tmp_path / "pyproject.toml"
    path_dest_pyproject_toml.touch()
    dest_pyproject_toml_path = str(path_dest_pyproject_toml)
    with pytest.raises(LookupError):
        VenvMapLoader(dest_pyproject_toml_path)

    # Fail during parsing
    prep_these = (
        ".venv/crap.txt",
        ".doc/.venv/crap.txt",
    )
    prepare_folders_files(prep_these, tmp_path)

    # no reqs files --> missing
    path_pyproject_toml = Path(__file__).parent.joinpath(
        "_req_files",
        "venvs.pyproject_toml",
    )
    path_dest_pyproject_toml = prep_pyproject_toml(path_pyproject_toml, tmp_path)
    loader = VenvMapLoader(path_dest_pyproject_toml.as_posix())
    venv_reqs, lst_missing = loader.parse_data()
    assert len(lst_missing) != 0
    assert len(lst_missing) == len(venv_reqs)

    # Prepare some, not all
    base_relpaths = (
        "requirements/pip-tools",
        "requirements/pip",
        "requirements/prod.shared",
        "requirements/kit",
    )
    prep_these = []
    for suffix in (".in", ".unlock", ".lock"):
        for base_relpath in base_relpaths:
            prep_these.append(f"{base_relpath}{suffix}")
    prepare_folders_files(prep_these, tmp_path)
    loader = VenvMapLoader(path_dest_pyproject_toml.as_posix())
    venv_reqs, lst_missing = loader.parse_data()
    assert len(lst_missing) != 0
    assert len(lst_missing) != len(venv_reqs)

    venv_map = VenvMap(loader)
    assert venv_map.missing != 0
    assert venv_map.project_base == tmp_path
    repr_venv_map = repr(venv_map)
    assert isinstance(repr_venv_map, str)
    assert len(venv_map) != 0
    # iterate over map
    for venvreq in venv_map:
        pass
    # __contains__
    venv_relpath = ".venv"
    assert venv_relpath in venv_map
    is_nonsense_in_venv_map = 3 in venv_map
    assert is_nonsense_in_venv_map is False

    # __getitem__
    venv_map[0:1]
    venv_map[1]
    with pytest.raises(TypeError):
        venv_map["1"]
    venv_map[-1]
    with pytest.raises(IndexError):
        venv_map[20000]

    with pytest.raises(KeyError):
        venv_map.reqs("nonexistant-file.in")

    # ensure_abspath unsupported type. Expects str or Path
    with pytest.raises(TypeError):
        loader.ensure_abspath(5)

    # ensure_abspath with abspath
    path_actual = loader.ensure_abspath(path_dest_pyproject_toml)
    assert path_actual == path_dest_pyproject_toml

    base_relpaths = (
        "requirements/pip-tools",
        "requirements/pip",
        "requirements/prod.shared",
        "requirements/kit",
        "requirements/tox",
        "requirements/mypy",
        "requirements/manage",
        "requirements/dev",
    )
    prep_these = []
    for suffix in (".in", ".unlock", ".lock"):
        for base_relpath in base_relpaths:
            prep_these.append(f"{base_relpath}{suffix}")
    prepare_folders_files(prep_these, tmp_path)

    venvreqs = venv_map.reqs(venv_relpath)
    assert isinstance(venvreqs, list)
    assert len(venvreqs) == len(base_relpaths)

    path_pyproject_toml = Path(__file__).parent.joinpath(
        "_req_files",
        "venvs-not-folder.pyproject_toml",
    )
    path_dest_pyproject_toml = prep_pyproject_toml(path_pyproject_toml, tmp_path)

    loader = VenvMapLoader(path_dest_pyproject_toml.as_posix())
    with pytest.raises(NotADirectoryError):
        loader.parse_data()

    path_pyproject_toml = Path(__file__).parent.joinpath(
        "_req_files",
        "venvs-reqs-not-sequence.pyproject_toml",
    )
    path_dest_pyproject_toml = prep_pyproject_toml(path_pyproject_toml, tmp_path)
    loader = VenvMapLoader(path_dest_pyproject_toml.as_posix())
    with pytest.raises(ValueError):
        loader.parse_data()


testdata_venvreq = (
    (
        ".venv",
        "requirements/dev",
        ("requirements",),
        does_not_raise(),
    ),
    (
        ".venv/crap.txt",
        "requirements/dev",
        ("requirements",),
        does_not_raise(),
    ),
)
ids_venvreq = (
    "in .venv, a dev requirement",
    "will raise NotADirectoryError during parsing, not during load",
)


@pytest.mark.parametrize(
    "venv_relpath, req_relpath, t_folders_relpath, expectation",
    testdata_venvreq,
    ids=ids_venvreq,
)
def test_venvreq(
    venv_relpath,
    req_relpath,
    t_folders_relpath,
    expectation,
    tmp_path,
    prepare_folders_files,
):
    """Test VenvReq."""
    # pytest --showlocals --log-level INFO -k "test_venvreq" tests
    # prepare
    #    venv folder
    prepare_folders_files((venv_relpath,), tmp_path)
    venv_relpath_tmp = venv_relpath
    if not resolve_joinpath(tmp_path, venv_relpath).exists():
        venv_relpath_tmp += "/.python_version"
        prepare_folders_files((venv_relpath_tmp,), tmp_path)

    #    requirements
    seq_relpath = []
    suffix_types = (".in", ".unlock", ".lock")
    for suffix in suffix_types:
        seq_relpath.append(f"{req_relpath}{suffix}")
    prepare_folders_files(seq_relpath, tmp_path)

    with expectation:
        vr = VenvReq(tmp_path, venv_relpath, req_relpath, t_folders_relpath)
    if isinstance(expectation, does_not_raise):
        repr_vr = repr(vr)
        assert isinstance(repr_vr, str)

        # Is not shared between venvs. Those requirement files should have suffix, .shared
        assert not vr.is_req_shared

        assert vr.venv_abspath.relative_to(tmp_path) == Path(venv_relpath)
        assert vr.req_abspath.relative_to(tmp_path) == Path(f"{req_relpath}.in")

        abspath_in_files = list(vr.reqs_all(".in"))
        assert len(abspath_in_files) == len(seq_relpath) / len(suffix_types)


testdata_venv_get_reqs = (
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
        ),
        8,
    ),
    (
        Path(__file__).parent.joinpath(
            "_req_files",
            "venvs.pyproject_toml",
        ),
        ".doc/.venv",
        (
            (
                Path(__file__).parent.parent.joinpath(
                    "docs",
                    "pip-tools.in",
                ),
                "docs/pip-tools.in",
            ),
            (
                Path(__file__).parent.parent.joinpath(
                    "requirements",
                    "pins.shared.in",
                ),
                "requirements/pins.shared.in",
            ),
        ),
        (
            "docs/pip-tools",
            "docs/requirements",
        ),
        2,
    ),
)
ids_venv_get_reqs = (
    "venvs.pyproject_toml .venv",
    "venvs.pyproject_toml .doc/.venv",
)


@pytest.mark.parametrize(
    "path_pyproject_toml, venv_relpath, seq_reqs, base_relpaths, expected_req_file_count",
    testdata_venv_get_reqs,
    ids=ids_venv_get_reqs,
)
def test_venv_get_reqs(
    path_pyproject_toml,
    venv_relpath,
    seq_reqs,
    base_relpaths,
    expected_req_file_count,
    tmp_path,
    prep_pyproject_toml,
    prepare_folders_files,
):
    """Test get_reqs"""
    # pytest --showlocals --log-level INFO -k "test_venv_get_reqs" tests
    # prepare
    #    pyproject.toml
    path_dest_pyproject_toml = prep_pyproject_toml(path_pyproject_toml, tmp_path)

    #    empty folders
    seq_folders = (
        ".venv/.python-version",
        ".doc/.venv/.python-version",
        "docs/empty.txt",
        "requirements/empty.txt",
    )
    prepare_folders_files(seq_folders, tmp_path)

    loader = VenvMapLoader(path_dest_pyproject_toml.as_posix())

    # loader invalid --> MissingPackageBaseFolder
    with pytest.raises(MissingPackageBaseFolder):
        get_reqs(None, venv_path=venv_relpath, suffix_last=SUFFIX_IN)

    # missing .in files
    with pytest.raises(MissingRequirementsFoldersFiles):
        get_reqs(loader, venv_path=venv_relpath, suffix_last=SUFFIX_IN)

    #    requirements empty files and folders
    suffixes = (SUFFIX_IN,)
    seq_rel_paths = []
    for base_relpath in base_relpaths:
        for suffix in suffixes:
            seq_rel_paths.append(f"{base_relpath}{suffix}")
    prepare_folders_files(seq_rel_paths, tmp_path)

    #    overwrite some req relpath src --> dest e.g. 'requirements/dev.unlock'
    for t_paths in seq_reqs:
        src_abspath, dest_relpath = t_paths
        abspath_dest = cast("Path", resolve_joinpath(tmp_path, dest_relpath))
        shutil.copy(src_abspath, abspath_dest)

    # No such venv
    with pytest.raises(KeyError):
        get_reqs(loader, ".dogfood", suffix_last=SUFFIX_IN)

    # venv_relpath is relative path
    abspath_reqs_a = get_reqs(loader, venv_relpath, suffix_last=SUFFIX_IN)
    actual_req_file_count_a = len(abspath_reqs_a)
    assert actual_req_file_count_a == expected_req_file_count

    # venv_relpath is absolute path
    abspath_venv_b = cast("Path", resolve_joinpath(tmp_path, venv_relpath))
    abspath_reqs_b = get_reqs(loader, abspath_venv_b, suffix_last=SUFFIX_IN)
    actual_req_file_count_b = len(abspath_reqs_b)
    assert actual_req_file_count_a == actual_req_file_count_b
