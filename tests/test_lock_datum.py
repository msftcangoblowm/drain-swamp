"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

Unit test -- Module

.. code-block:: shell

   python -m coverage run --source='drain_swamp.lock_datum' -m pytest \
   --showlocals tests/test_lock_datum.py && coverage report \
   --data-file=.coverage --include="**/lock_datum.py"

"""

from __future__ import annotations

import shutil
from contextlib import nullcontext as does_not_raise
from pathlib import Path
from typing import cast

import pytest

from drain_swamp._safe_path import resolve_joinpath
from drain_swamp.exceptions import MissingPackageBaseFolder
from drain_swamp.lock_collections import Ins
from drain_swamp.lock_datum import (
    InFileType,
    Pin,
    PinDatum,
    _hash_pindatum,
    _parse_qualifiers,
    has_qualifiers,
    in_generic,
    is_pin,
)
from drain_swamp.lock_filepins import FilePins
from drain_swamp.pep518_venvs import VenvMapLoader

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


testdata_pin_methods = (
    (
        Path(__file__).parent.joinpath(
            "_req_files",
            "constraints-various.unlock",
        ),
        "requirements/constraints-various.in",
        "pip",
        0,
        True,
    ),
    (
        Path(__file__).parent.joinpath(
            "_req_files",
            "constraints-various.unlock",
        ),
        "requirements/constraints-various.in",
        "tomli",
        1,
        True,
    ),
    (
        Path(__file__).parent.joinpath(
            "_req_files",
            "constraints-various.unlock",
        ),
        "requirements/constraints-various.in",
        "isort",
        0,
        False,
    ),
    (
        Path(__file__).parent.joinpath(
            "_req_files",
            "constraints-conflicts.unlock",
        ),
        "requirements/constraints-conflicts.in",
        "colorama",
        1,
        False,
    ),
)
ids_pin_methods = (
    "various constraints pip",
    "various constraints tomli",
    "various constraints isort",
    "constraints conflicts normalize qualifer",
)


@pytest.mark.parametrize(
    (
        "abspath_req_src, dest_relpath, pkg_name, "
        "qualifiers_expected_count, has_specifiers"
    ),
    testdata_pin_methods,
    ids=ids_pin_methods,
)
def test_pin_methods(
    abspath_req_src,
    dest_relpath,
    pkg_name,
    qualifiers_expected_count,
    has_specifiers,
    tmp_path,
    prepare_folders_files,
):
    """Pin class interface"""
    # pytest --showlocals --log-level INFO -k "test_pin_methods" tests
    # prepare
    #    empty folders
    seqs_reqs = ("requirements/.python-version",)
    prepare_folders_files(seqs_reqs, tmp_path)

    #    copy a .in file
    src_abspath = str(abspath_req_src)
    abspath_dest = cast("Path", resolve_joinpath(tmp_path, dest_relpath))
    shutil.copy(src_abspath, abspath_dest)

    pin_pip = Pin(abspath_dest, pkg_name)
    # __repr__
    repr(pin_pip)
    # __hash__
    assert isinstance(hash(pin_pip), int)
    # Pin is not PinDatum
    assert _hash_pindatum(abspath_dest, pkg_name, pin_pip.qualifiers) != hash(pin_pip)
    # Pin.qualifiers
    assert len(pin_pip.qualifiers) == qualifiers_expected_count
    quals = _parse_qualifiers(pin_pip.line)
    assert len(quals) == qualifiers_expected_count
    # Pin.is_pin
    is_spec = Pin.is_pin(pin_pip.specifiers)
    assert is_spec is has_specifiers
    # is_pin
    is_spec = is_pin(pin_pip.specifiers)
    assert is_spec is has_specifiers

    # has_qualifiers
    qualifiers_expected = qualifiers_expected_count != 0
    assert has_qualifiers(pin_pip.qualifiers) is qualifiers_expected


@pytest.mark.parametrize(
    (
        "abspath_req_src, dest_relpath, pkg_name, "
        "qualifiers_expected_count, has_specifiers"
    ),
    testdata_pin_methods,
    ids=ids_pin_methods,
)
def test_pindatum(
    abspath_req_src,
    dest_relpath,
    pkg_name,
    qualifiers_expected_count,
    has_specifiers,
    tmp_path,
    prepare_folders_files,
    path_project_base,
):
    """Test PinDatum"""
    # pytest --showlocals --log-level INFO -k "test_pindatum" tests
    path_cwd = path_project_base()
    # prepare
    #    empty folders
    seqs_reqs = ("requirements/.python-version",)
    prepare_folders_files(seqs_reqs, tmp_path)

    #    copy a .in file
    src_abspath = str(abspath_req_src)
    abspath_dest = cast("Path", resolve_joinpath(tmp_path, dest_relpath))
    shutil.copy(src_abspath, abspath_dest)

    fp = FilePins(abspath_dest)
    lst_pins_pip = fp.by_pkg(pkg_name)
    pin_pip = lst_pins_pip[0]
    assert isinstance(pin_pip, PinDatum)

    # PinDatum.__hash__
    assert hash(pin_pip) == _hash_pindatum(abspath_dest, pkg_name, pin_pip.qualifiers)
    # __eq__
    assert pin_pip != 7

    # PinDatum.__lt__
    lst = fp._pins
    assert isinstance(sorted(lst), list)

    with pytest.raises(TypeError):
        lst.insert(0, 1.2)
        lst.append(7)
        sorted(lst)

    # PinDatum from different files
    abspath_file_left = cast(
        "Path",
        resolve_joinpath(
            path_cwd,
            "tests/_req_files/constraints-conflicts.unlock",
        ),
    )
    left_pkg_name = "tomli"
    abspath_file_right = cast(
        "Path",
        resolve_joinpath(
            path_cwd,
            "tests/_req_files/constraints-various.unlock",
        ),
    )
    right_pkg_name = "colorama"
    with pytest.raises(TypeError):
        fp_left = FilePins(abspath_file_left)
        fp_right = FilePins(abspath_file_right)
        assert isinstance(fp_left, FilePins)
        assert isinstance(fp_right, FilePins)
        PinDatum_left = fp_left.by_pkg(left_pkg_name)[0]
        PinDatum_right = fp_right.by_pkg(right_pkg_name)[0]
        assert isinstance(PinDatum_left, PinDatum)
        assert isinstance(PinDatum_right, PinDatum)

        PinDatum_left < PinDatum_right

    # For purposes of sorting -- pkg_name same, qualifiers same
    pin_left = PinDatum(
        abspath_file_left,
        "colorama",
        'colorama;os_name == "nt"',
        [],
        ['platform_system=="Windows"'],
    )
    pin_right_0 = PinDatum(
        abspath_file_left,
        "colorama",
        'colorama;os_name == "nt"',
        [],
        ['platform_system=="Windows"'],
    )
    is_same_pkg_and_qualifiers = pin_left < pin_right_0
    assert is_same_pkg_and_qualifiers is False

    # For purposes of sorting -- pkg_name same, qualifiers different
    pin_right_1 = PinDatum(
        abspath_file_left,
        "colorama",
        'colorama;os_name == "nt"',
        [],
        ['python_version<"3.11"'],
    )
    is_same_pkg_qualifiers_differ = pin_left < pin_right_1
    assert isinstance(is_same_pkg_qualifiers_differ, bool)
    # '; platform_system=="Windows"' < '; python_version<"3.11"'
    assert is_same_pkg_qualifiers_differ is True


def test_in_generic(
    tmp_path,
    path_project_base,
    prepare_folders_files,
    prep_pyproject_toml,
):
    """Generic __contains__ implementation"""
    # pytest --showlocals --log-level INFO -k "test_in_generic" tests
    path_cwd = path_project_base()
    venv_path = ".venv"
    dest_relpath = "requirements/pip-tools.in"
    abspath_file_src = cast(
        "Path", resolve_joinpath(path_cwd, "requirements/pip-tools.in")
    )
    path_pyproject_toml = Path(__file__).parent.joinpath(
        "_req_files",
        "venvs_minimal.pyproject_toml",
    )

    loader = None
    with pytest.raises(MissingPackageBaseFolder):
        Ins(loader, venv_path)

    # prepare
    #    pyproject.toml
    path_dest_pyproject_toml = prep_pyproject_toml(path_pyproject_toml, tmp_path)
    loader = VenvMapLoader(path_dest_pyproject_toml.as_posix())

    #    venv and requirements folders
    prep_these = (
        ".venv/.python-version",
        ".tools/.python-version",
        "requirements/deleteme.txt",
        "docs/deleteme.txt",
    )
    prepare_folders_files(prep_these, tmp_path)

    # requirements
    abspath_dest = cast("Path", resolve_joinpath(tmp_path, dest_relpath))
    shutil.copy(abspath_file_src, abspath_dest)

    fpins_0 = FilePins(abspath_dest)
    ins_0 = Ins(loader, venv_path)
    ins_0._file_pins = list()
    ins_0.files = fpins_0

    # InFileType.__eq__
    assert InFileType.FILES != InFileType.ZEROES
    is_files_type = InFileType.FILES
    assert InFileType.FILES == is_files_type

    # Ins.file_abspath
    is_in = in_generic(
        ins_0,
        abspath_dest,
        "file_abspath",
        set_name=InFileType.FILES,
        is_abspath_ok=True,
    )
    assert is_in is True

    is_in = in_generic(
        ins_0,
        abspath_dest,
        "file_abspath",
        set_name=InFileType.ZEROES,
        is_abspath_ok=True,
    )
    assert is_in is False

    # set_name is nonsense. Default InFileType.FILES
    invalids = (
        None,
        1.234,
    )
    for invalid in invalids:
        is_in = in_generic(
            ins_0,
            abspath_dest,
            "file_abspath",
            set_name=invalid,
            is_abspath_ok=True,
        )
        assert is_in is True

    """is_abspath_ok is nonsense --> False. This is not normal usage
    passing in relative path instead of absolute path"""
    invalids = (
        None,
        1.234,
    )
    for invalid in invalids:
        is_in = in_generic(
            ins_0,
            dest_relpath,
            "file_abspath",
            set_name=invalid,
            is_abspath_ok=invalid,
        )
        assert is_in is False
