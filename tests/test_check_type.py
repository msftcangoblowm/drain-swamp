"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

Unittest for module, check_type

Unit test -- Module

.. code-block:: shell

   python -m coverage run --source='drain_swamp.check_type' -m pytest \
   --showlocals tests/test_check_type.py && coverage report \
   --data-file=.coverage --include="**/check_type.py"

Integration test

.. code-block:: shell

   make coverage
   pytest --showlocals --cov="drain_swamp" --cov-report=term-missing \
   --cov-config=pyproject.toml tests

"""

from contextlib import nullcontext as does_not_raise
from pathlib import Path

import pytest

from drain_swamp.check_type import (
    click_bool,
    is_ok,
    is_relative_required,
)
from drain_swamp.constants import SUFFIX_IN

testdata_is_ok = (
    (None, False),
    ("", False),
    (0.123, False),
    ("    ", False),
    ("Hello World!", True),
)
ids_is_ok = (
    "not str",
    "empty string",
    "not str",
    "contains only whitespace",
    "non-empty string",
)


@pytest.mark.parametrize(
    "mystr, expected",
    testdata_is_ok,
    ids=ids_is_ok,
)
def test_is_ok(mystr, expected):
    """Test is_ok check."""
    # pytest --showlocals --log-level INFO -k "test_is_ok" tests
    actual = is_ok(mystr)
    assert actual == expected


testdata_is_relative_required = (
    (None, None, pytest.raises(TypeError), False),
    (None, 1.12345, pytest.raises(TypeError), False),
    (None, 1, pytest.raises(TypeError), False),
    (None, "Hello world!", pytest.raises(TypeError), False),
    (None, (), pytest.raises(ValueError), False),
    (None, [], pytest.raises(ValueError), False),
    (None, (None, 1.12345, 1), pytest.raises(ValueError), False),
    (None, (SUFFIX_IN,), does_not_raise(), False),
    ("requirements/horse.in", (SUFFIX_IN,), does_not_raise(), False),
    (Path("requirements/horse.in"), (SUFFIX_IN,), does_not_raise(), True),
    (Path("requirements/horse.in"), ("in",), does_not_raise(), True),
    (Path("requirements/horse.in"), (".pip",), does_not_raise(), False),
    (
        Path("requirements/horse.pip"),
        (SUFFIX_IN,),
        does_not_raise(),
        False,
    ),
    (Path("requirements/horse.in"), (".tar", ".gz"), does_not_raise(), False),
)
ids_is_relative_required = (
    "ext unsupported type None",
    "ext unsupported type float",
    "ext unsupported type int",
    "ext unsupported type str disallowed sequence",
    "ext empty sequence tuple",
    "ext empty sequence list",
    "ext sequence containing only unsupported types",
    "Path | None",
    "must be a Path, got str. matching extensions",
    "Path provided matching extensions",
    "autofix missing period",
    "exts different has .in expect .pip",
    "exts different has .pip expect .in",
    "exts different has .in expect .tar or .gz",
)


@pytest.mark.parametrize(
    "relative_path, exts, expectation, expected",
    testdata_is_relative_required,
    ids=ids_is_relative_required,
)
def test_is_relative_required(relative_path, exts, expectation, expected):
    """Test is_relative_required."""
    # pytest --showlocals --log-level INFO -k "test_is_relative_required" tests
    with expectation:
        actual = is_relative_required(path_relative=relative_path, extensions=exts)
    if isinstance(expectation, does_not_raise):
        assert actual == expected


testdata_click_bool = (
    (None, None),
    ("George", None),
    ("0", False),
    ("off", False),
    ("1", True),
    ("on", True),
)
ids_click_bool = (
    "None",
    "Unknown str",
    "str number indicating a bool value False",
    "off means False",
    "str number indicating a bool value True",
    "off means True",
)


@pytest.mark.parametrize(
    "val, expected",
    testdata_click_bool,
    ids=ids_click_bool,
)
def test_click_bool(val, expected):
    """Test click.Bool check."""
    # pytest --showlocals --log-level INFO -k "test_click_bool" tests
    actual = click_bool(val=val)
    assert actual is expected
