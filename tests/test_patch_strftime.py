"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

With coverage

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
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

from drain_swamp.monkey.patch_strftime import (
    PatchAggregateD,
    PatchAggregateT,
    PatchLeadingDay,
    StrFTime,
)

if TYPE_CHECKING:
    from .typing_only import DOES_NOT_OR_DOES


@pytest.mark.parametrize(
    "cls_patch, format_str, expectation",
    (
        pytest.param(
            PatchLeadingDay,
            ",%-d,",
            does_not_raise(),
            marks=pytest.mark.skipif(
                not PatchLeadingDay.AFFECTS, reason="does not apply to this platform"
            ),
            id="PatchLeadingDay-linux-feature",
        ),
        pytest.param(
            PatchAggregateD,
            ",%D,",
            does_not_raise(),
            marks=pytest.mark.skipif(
                not PatchAggregateD.AFFECTS, reason="does not apply to this platform"
            ),
            id="PatchAggregateD-MacOS-issue",
        ),
        pytest.param(
            PatchAggregateT,
            ",%T,",
            does_not_raise(),
            marks=pytest.mark.skipif(
                not PatchAggregateT.AFFECTS, reason="does not apply to this platform"
            ),
            id="PatchAggregateT-Windows-issue",
        ),
    ),
)
def test_patch_leading_day(
    cls_patch: type,
    format_str: str,
    expectation: "DOES_NOT_OR_DOES",
) -> None:
    """Run patch if an affected platform."""
    # pytest --showlocals --log-level INFO -k "test_patch_leading_day" tests
    dt_now = dt.now()
    with expectation:
        actual = cls_patch()(dt_now, format_str)
    if isinstance(expectation, does_not_raise):
        assert actual is not None
        assert isinstance(actual, str)
        assert actual != format_str


@pytest.mark.parametrize(
    "format_str, expectation",
    (
        pytest.param(
            None,
            pytest.raises(TypeError),
            id="None",
        ),
        pytest.param(
            1.2345,
            pytest.raises(TypeError),
            id="float",
        ),
        pytest.param(
            "%T",
            pytest.raises(ValueError) if PatchAggregateT.AFFECTS else does_not_raise(),
            id="Windows-issue.-Aggregate-equivalent-to-%H:%M:%S",
        ),
        pytest.param(
            "%D",
            pytest.raises(ValueError) if PatchAggregateD.AFFECTS else does_not_raise(),
            id="MacOS-issue.-Aggregate-equivalent-to-%m/%d/%Y",
        ),
        pytest.param(
            "%-d",
            pytest.raises(ValueError) if PatchLeadingDay.AFFECTS else does_not_raise(),
            id="Linux-flavor-only.-Day-without-leading-zero",
        ),
    ),
)
def test_unpatched_strftime(
    format_str: str | float | None,
    expectation: "DOES_NOT_OR_DOES",
) -> None:
    """Should prove strftime has issues with format str on certain platforms."""
    # pytest --showlocals --log-level INFO -k "test_unpatched_strftime" tests
    dt_now = dt.now()
    with expectation:
        dt_now.strftime(format_str)


@pytest.mark.parametrize(
    "format_str, expectation",
    (
        pytest.param(
            "%T",
            does_not_raise(),
            id="Windows-issue.-Aggregate-equivalent-to-%H:%M:%S",
        ),
        pytest.param(
            "%D",
            does_not_raise(),
            id="MacOS-issue.-Aggregate-equivalent-to-%m/%d/%Y",
        ),
        pytest.param(
            "%-d",
            does_not_raise(),
            id="Linux-flavor-only.-Day-without-leading-zero",
        ),
        pytest.param(
            None,
            pytest.raises(TypeError),
            id="Unsupported-type-None",
        ),
        pytest.param(
            1.2345,
            pytest.raises(TypeError),
            id="Unsupported-type-float",
        ),
    ),
)
def test_patched_strftime(format_str: str, expectation: "DOES_NOT_OR_DOES") -> None:
    """Patch datetime.datetime.strftime. Prove doesn't fail."""
    # pytest --showlocals --log-level INFO -k "test_patched_strftime" tests
    dt_now = dt.now()
    sft = StrFTime(dt_now)

    with expectation:
        sft.strftime(format_str)


@pytest.mark.parametrize(
    "format_str, year, expectation",
    (
        pytest.param(
            "%m/%d/%Y",
            -999,
            pytest.raises(ValueError),
            id="Ancient-times",
        ),
    ),
)
def test_strftime_exception(
    format_str: str,
    year: int,
    expectation: "DOES_NOT_OR_DOES",
) -> None:
    """Try to cause the elusive ValueError."""
    # pytest --showlocals --log-level INFO -k "test_strftime_exception" tests
    # https://github.com/python/cpython/blob/01748b75de54c7ec70e345f704c886457f113fc8/Lib/_pydatetime.py#L1564
    # The year must be >= 1000 else Python's strftime implementation
    # can raise a bogus Exception
    with expectation:
        dt_ancient_times = dt(year, 7, 14, 12, 30)
        sft = StrFTime(dt_ancient_times)
        sft.strftime(format_str)


def test_patch_linux() -> None:
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
