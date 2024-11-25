"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

Unit test -- Module

.. code-block:: shell

   python -m coverage run --source='drain_swamp.lock_discrepancy' -m pytest \
   --showlocals tests/test_lock_discrepancy.py && coverage report \
   --data-file=.coverage --include="**/lock_discrepancy.py"

"""

import logging
import logging.config
from contextlib import nullcontext as does_not_raise
from unittest.mock import patch

import pytest
from logging_strict.tech_niques import get_locals  # noqa: F401
from packaging.version import Version

from drain_swamp._safe_path import resolve_joinpath
from drain_swamp.constants import (
    LOGGING,
    g_app_name,
)
from drain_swamp.lock_datum import PinDatum
from drain_swamp.lock_discrepancy import (
    _parse_specifiers,
    extract_full_package_name,
    tunnel_blindness_suffer_chooses,
)

testdata_extract_full_package_name = (
    (
        'colorama ;platform_system=="Windows"',
        "colorama",
        "colorama",
    ),
    (
        'tomli; python_version<"3.11"',
        "tomli",
        "tomli",
    ),
    (
        "pip @ remote",
        "pip",
        "pip",
    ),
    (
        "pip@ remote",
        "pip",
        "pip",
    ),
    (
        "pip @remote",
        "pip",
        "pip",
    ),
    (
        "tox>=1.1.0",
        "tox",
        "tox",
    ),
    (
        "tox-gh-action>=1.1.0",
        "tox",
        None,
    ),
)
ids_extract_full_package_name = (
    "space semicolon",
    "semicolon space",
    "space at space",
    "at space",
    "space at",
    "exact pkg name operator ge",
    "not a match",
)


@pytest.mark.parametrize(
    "line, search_for, expected_pkg_name",
    testdata_extract_full_package_name,
    ids=ids_extract_full_package_name,
)
def test_extract_full_package_name(
    line,
    search_for,
    expected_pkg_name,
    caplog,
):
    """For a particular package, check line is an exact match."""
    # pytest -vv --showlocals --log-level INFO -k "test_extract_full_package_name" tests
    LOGGING["loggers"][g_app_name]["propagate"] = True
    logging.config.dictConfig(LOGGING)
    logger = logging.getLogger(name=g_app_name)
    logger.addHandler(hdlr=caplog.handler)
    caplog.handler.level = logger.level

    func_path = f"{g_app_name}.lock_discrepancy.extract_full_package_name"
    args = (line, search_for)
    kwargs = {}
    t_ret = get_locals(  # noqa: F841
        func_path,
        extract_full_package_name,
        *args,
        **kwargs,
    )

    pkg_name_actual = extract_full_package_name(line, search_for)
    if expected_pkg_name is None:
        assert pkg_name_actual is None
    else:
        assert pkg_name_actual == expected_pkg_name

    # Couldn't figure out how to make re.match fail
    with patch("re.match", return_value=None):
        pkg_name_actual = extract_full_package_name(line, "%%")
        assert pkg_name_actual is None


testdata_choose_version_order_mixed_up = (
    (
        "pip",
        (
            "file_0.in",
            '"pip>=24.2; python_version <= "3.10"',
            [">=24.2"],
            ['python_version <= "3.10"'],
        ),
        (
            "file_1.in",
            "pip",
            [],
            [],
        ),
        Version("23.0"),
        {Version("25.0"), Version("24.8"), Version("25.3")},
        does_not_raise(),
        ">=",
        Version("25.3"),
    ),
    (
        "pip",
        (
            "file_0.in",
            '"pip; python_version <= "3.10"',
            [],
            ['python_version <= "3.10"'],
        ),
        (
            "file_1.in",
            "pip",
            [],
            [],
        ),
        Version("25.3"),
        {Version("25.0"), Version("23.0"), Version("24.8")},
        does_not_raise(),
        ">=",
        Version("25.3"),
    ),
    (
        "pip",
        (
            "file_0.in",
            '"pip != 25.3; python_version <= "3.10"',
            ["!=25.3"],
            ['python_version <= "3.10"'],
        ),
        (
            "file_1.in",
            "pip",
            [],
            [],
        ),
        Version("25.3"),
        {Version("25.0"), Version("23.0"), Version("24.8")},
        does_not_raise(),
        "==",
        Version("25.0"),
    ),
    (
        "pip",
        (
            "file_0.in",
            '"pip; python_version <= "3.10"',
            [],
            ['python_version <= "3.10"'],
        ),
        (
            "file_1.in",
            "pip",
            [],
            [],
        ),
        Version("25.3"),
        {Version("25.0"), Version("23.0"), Version("24.8")},
        does_not_raise(),
        ">=",
        Version("25.3"),
    ),
    (
        "pip",
        (
            "file_0.in",
            '"pip==25.0; python_version <= "3.10"',
            ["==25.0"],
            ['python_version <= "3.10"'],
        ),
        (
            "file_1.in",
            "pip<=25.3",
            ["<=25.3"],
            [],
        ),
        Version("25.3"),
        {Version("25.0"), Version("23.0"), Version("24.8")},
        does_not_raise(),
        "==",
        Version("25.0"),
    ),
    (
        "pip",
        (
            "file_0.in",
            '"pip~=25.0; python_version <= "3.10"',
            ["~=25.0"],
            ['python_version <= "3.10"'],
        ),
        (
            "file_1.in",
            "pip<=25.3",
            ["<=25.3"],
            [],
        ),
        Version("25.3"),
        {Version("25.0"), Version("23.0"), Version("24.8")},
        pytest.raises(NotImplementedError),
        "==",
        Version("25.0"),
    ),
    (
        "pip",
        (
            "file_0.in",
            '"pip>=23.0, <25.3; python_version <= "3.10"',
            [">=23.0", "<25.3"],
            ['python_version <= "3.10"'],
        ),
        (
            "file_1.in",
            "pip",
            [],
            [],
        ),
        Version("25.3"),
        {Version("25.0"), Version("23.0"), Version("24.8")},
        does_not_raise(),
        ">=",
        Version("25.0"),
    ),
    (
        "pip",
        (
            "file_0.in",
            '"pip>=23.0, <25.3, !=25.2; python_version <= "3.10"',
            [">=23.0", "<25.3", "!=25.2"],
            ['python_version <= "3.10"'],
        ),
        (
            "file_1.in",
            "pip",
            [],
            [],
        ),
        Version("25.3"),
        {Version("25.0"), Version("23.0"), Version("24.8")},
        pytest.raises(NotImplementedError),
        ">=",
        Version("25.0"),
    ),
)
ids_choose_version_order_mixed_up = (
    ">=24.2 out of order others set",
    "No specifiers provided. Version chosen solely from version in .lock files",
    "!=25.3 --> next best choice ==25.0",
    "package twice without specifiers",
    "==25.0 all other package version become unacceptable",
    "~= not yet supported",
    "two specifiers",
    "three specifiers",
)


@pytest.mark.parametrize(
    (
        "pkg_name, seq_file_0, seq_file_1, highest, others, expectation, "
        "unlock_operator_expected, found_expected"
    ),
    testdata_choose_version_order_mixed_up,
    ids=ids_choose_version_order_mixed_up,
)
def test_choose_version_order_mixed_up(
    pkg_name,
    seq_file_0,
    seq_file_1,
    highest,
    others,
    expectation,
    unlock_operator_expected,
    found_expected,
    tmp_path,
    caplog,
):
    """Have versions in others out of order."""
    # pytest -vv --showlocals --log-level INFO -k "test_choose_version_order_mixed_up" tests
    LOGGING["loggers"][g_app_name]["propagate"] = True
    logging.config.dictConfig(LOGGING)
    logger = logging.getLogger(name=g_app_name)
    logger.addHandler(hdlr=caplog.handler)
    caplog.handler.level = logger.level

    f_relpath_0, line_0, specifiers_0, qualifiers_0 = seq_file_0
    f_relpath_1, line_1, specifiers_1, qualifiers_1 = seq_file_1
    file_abspath_0 = resolve_joinpath(tmp_path, f_relpath_0)
    file_abspath_1 = resolve_joinpath(tmp_path, f_relpath_1)

    pind_0 = PinDatum(
        file_abspath_0,
        pkg_name,
        line_0,
        specifiers_0,
        qualifiers_0,
    )
    pind_1 = PinDatum(
        file_abspath_1,
        pkg_name,
        line_1,
        specifiers_1,
        qualifiers_1,
    )
    set_pindatum = set()
    set_pindatum.add(pind_0)
    set_pindatum.add(pind_1)

    """
    func_path = f"{g_app_name}.lock_discrepancy.tunnel_blindness_suffer_chooses"
    args = (set_pindatum, highest, others)
    kwargs = {}
    t_out = get_locals(  # noqa: F841
        func_path,
        tunnel_blindness_suffer_chooses,
        *args,
        **kwargs,
    )
    t_ret, t_locals = t_out
    """
    with expectation:
        t_ret = tunnel_blindness_suffer_chooses(
            set_pindatum,
            highest,
            others,
        )
    if isinstance(expectation, does_not_raise):
        assert isinstance(t_ret, tuple)
        _, unlock_operator_actual, ver_found_actual = t_ret
        assert unlock_operator_actual == unlock_operator_expected
        assert ver_found_actual is not None
        assert ver_found_actual == found_expected


testdata_parse_specifiers = (
    (
        [">=24.2"],
        [(">=", "24.2")],
    ),
    (
        ["<=24.2"],
        [("<=", "24.2")],
    ),
    (
        ["<24.2"],
        [("<", "24.2")],
    ),
    (
        [">24.2"],
        [(">", "24.2")],
    ),
    (
        ["!=24.2"],
        [("!=", "24.2")],
    ),
    (
        ["==24.2"],
        [("==", "24.2")],
    ),
    (
        ["~=24.2"],
        [("~=", "24.2")],
    ),
)
ids_parse_specifiers = (
    "ge 24.2",
    "le 24.2",
    "lt 24.2",
    "gt 24.2",
    "ne 24.2",
    "eq 24.2",
    "shortcut for between version and next major release",
)


@pytest.mark.parametrize(
    "specifiers, lst_expected",
    testdata_parse_specifiers,
    ids=ids_parse_specifiers,
)
def test_parse_specifiers(
    specifiers,
    lst_expected,
):
    """Just parse each specifier from str to tuple"""
    # pytest -vv --showlocals --log-level INFO -k "test_parse_specifiers" tests
    # Specifiers produced by pip_requirements_parser.RequirementsFile
    """
    func_path = f"{g_app_name}.lock_discrepancy._parse_specifiers"
    args = (specifiers,)
    kwargs = {}
    t_out = get_locals(  # noqa: F841
        func_path,
        _parse_specifiers,
        *args,
        **kwargs,
    )
    lst, t_locals = t_out
    """
    lst = _parse_specifiers(specifiers)

    for idx, t_datum in enumerate(lst):
        assert lst_expected[idx] == t_datum
