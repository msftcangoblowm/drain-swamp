"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

Unit test -- Module

.. code-block:: shell

   python -m coverage run --source='drain_swamp.monkey.patch_strftime' -m pytest \
   --showlocals tests/test_patch_strftime.py && coverage report \
   --data-file=.coverage --include="**/monkey/patch_strftime.py"

Integration test

.. code-block:: shell

   make coverage
   pytest --showlocals --cov="drain_swamp" --cov-report=term-missing \
   --cov-config=pyproject.toml tests

"""

from contextlib import nullcontext as does_not_raise
from datetime import datetime as dt
from unittest.mock import patch

import pytest

from drain_swamp.monkey.patch_strftime import (
    PatchAggregateD,
    PatchAggregateT,
    PatchLeadingDay,
    StrFTime,
)

testdata_patches = (
    pytest.param(
        PatchLeadingDay,
        ",%-d,",
        does_not_raise(),
        marks=pytest.mark.skipif(
            not PatchLeadingDay.AFFECTS, reason="does not apply to this platform"
        ),
    ),
    pytest.param(
        PatchAggregateD,
        ",%D,",
        does_not_raise(),
        marks=pytest.mark.skipif(
            not PatchAggregateD.AFFECTS, reason="does not apply to this platform"
        ),
    ),
    pytest.param(
        PatchAggregateT,
        ",%T,",
        does_not_raise(),
        marks=pytest.mark.skipif(
            not PatchAggregateT.AFFECTS, reason="does not apply to this platform"
        ),
    ),
)
ids_patches = (
    "PatchLeadingDay linux feature",
    "PatchAggregateD MacOS issue",
    "PatchAggregateT Windows issue",
)


@pytest.mark.parametrize(
    "cls_patch, format_str, expectation",
    testdata_patches,
    ids=ids_patches,
)
def test_patch_leading_day(cls_patch, format_str, expectation):
    """Run patch if an affected platform."""
    # pytest --showlocals --log-level INFO -k "test_patch_leading_day" tests
    dt_now = dt.now()
    with expectation:
        actual = cls_patch()(dt_now, format_str)
    if isinstance(expectation, does_not_raise):
        assert actual is not None
        assert isinstance(actual, str)
        assert actual != format_str


testdata_unpatched_strftime = (
    (
        None,
        pytest.raises(TypeError),
    ),
    (
        1.2345,
        pytest.raises(TypeError),
    ),
    (
        "%T",
        pytest.raises(ValueError) if PatchAggregateT.AFFECTS else does_not_raise(),
    ),
    (
        "%D",
        pytest.raises(ValueError) if PatchAggregateD.AFFECTS else does_not_raise(),
    ),
    (
        "%-d",
        pytest.raises(ValueError) if PatchLeadingDay.AFFECTS else does_not_raise(),
    ),
)
ids_unpatched_strftime = (
    "None",
    "float",
    "Windows issue. Aggregate equivalent to %H:%M:%S",
    "MacOS issue. Aggregate equivalent to %m/%d/%Y",
    "Linux flavor only. Day without leading zero",
)


@pytest.mark.parametrize(
    "format_str, expectation",
    testdata_unpatched_strftime,
    ids=ids_unpatched_strftime,
)
def test_unpatched_strftime(format_str, expectation):
    """Should prove strftime has issues with format str on certain platforms."""
    # pytest --showlocals --log-level INFO -k "test_unpatched_strftime" tests
    dt_now = dt.now()
    with expectation:
        dt_now.strftime(format_str)


testdata_patched_strftime = (
    (
        "%T",
        does_not_raise(),
    ),
    (
        "%D",
        does_not_raise(),
    ),
    (
        "%-d",
        does_not_raise(),
    ),
    (
        None,
        pytest.raises(TypeError),
    ),
    (
        1.2345,
        pytest.raises(TypeError),
    ),
)
ids_patched_strftime = (
    "Windows issue. Aggregate equivalent to %H:%M:%S",
    "MacOS issue. Aggregate equivalent to %m/%d/%Y",
    "Linux flavor only. Day without leading zero",
    "Unsupported type None",
    "Unsupported type float",
)


@pytest.mark.parametrize(
    "format_str, expectation",
    testdata_patched_strftime,
    ids=ids_patched_strftime,
)
def test_patched_strftime(format_str, expectation):
    """Patch datetime.datetime.strftime. Prove doesn't fail."""
    # pytest --showlocals --log-level INFO -k "test_patched_strftime" tests
    dt_now = dt.now()
    sft = StrFTime(dt_now)

    with expectation:
        sft.strftime(format_str)


testdata_strftime_exception = (
    (
        -999,
        pytest.raises(ValueError),
    ),
)
ids_strftime_exception = ("Ancient times",)


@pytest.mark.parametrize(
    "year, expectation",
    testdata_strftime_exception,
    ids=ids_strftime_exception,
)
def test_strftime_exception(year, expectation):
    """Try to cause the elusive ValueError."""
    # pytest --showlocals --log-level INFO -k "test_strftime_exception" tests
    # https://github.com/python/cpython/blob/01748b75de54c7ec70e345f704c886457f113fc8/Lib/_pydatetime.py#L1564
    # The year must be >= 1000 else Python's strftime implementation
    # can raise a bogus exception
    format_str = "%m/%d/%Y"
    expectation = pytest.raises(ValueError)
    with expectation:
        dt_ancient_times = dt(year, 7, 14, 12, 30)
        sft = StrFTime(dt_ancient_times)
        sft.strftime(format_str)


def test_patch_linux():
    """Linux Python interpretor is too perfect, so break it."""
    # pytest --showlocals --log-level INFO -k "test_patch_linux" tests
    dt_now = dt.now()
    klasses = [kls for kls in StrFTime.patches]
    for kls_patch in klasses:
        with patch.object(
            kls_patch,
            "AFFECTS",
            True,
        ):
            format_str = f",{kls_patch.AFFECTED_TOKEN},"
            sft = StrFTime(dt_now)
            sft.strftime(format_str)
