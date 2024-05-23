"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

..

Unittest for module, check_type

Without coverage

.. code-block:: shell

   pytest --showlocals --log-level INFO tests/test_check_type.py

With coverage

Needs a config file to specify exact files to include / omit from report.
Will fail with exit code 1 even with 100% coverage

.. code-block:: shell

   pytest --showlocals --cov="drain_swamp" --cov-report=term-missing tests/test_check_type.py

.. seealso::

   https://github.com/pytest-dev/pytest-cov/issues/373#issuecomment-1472861775

"""

from pathlib import Path

import pytest

from drain_swamp.check_type import (
    is_ok,
    is_relative_required,
)
from drain_swamp.constants import SUFFIX_UNLOCKED

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
    # pytest --showlocals --log-level INFO -k "test_is_ok" tests
    actual = is_ok(mystr)
    assert actual == expected


testdata_is_relative_required = (
    pytest.param(None, None, False, marks=pytest.mark.xfail(raises=TypeError)),
    pytest.param(None, 1.12345, False, marks=pytest.mark.xfail(raises=TypeError)),
    pytest.param(None, 1, False, marks=pytest.mark.xfail(raises=TypeError)),
    pytest.param(
        None, "Hello world!", False, marks=pytest.mark.xfail(raises=TypeError)
    ),
    pytest.param(None, (), False, marks=pytest.mark.xfail(raises=ValueError)),
    pytest.param(None, [], False, marks=pytest.mark.xfail(raises=ValueError)),
    pytest.param(
        None, (None, 1.12345, 1), False, marks=pytest.mark.xfail(raises=ValueError)
    ),
    (None, (SUFFIX_UNLOCKED,), False),
    ("requirements/horse.in", (SUFFIX_UNLOCKED,), False),
    (Path("requirements/horse.in"), (SUFFIX_UNLOCKED,), True),
    (Path("requirements/horse.in"), ("in",), True),
    (Path("requirements/horse.in"), (".pip",), False),
    (
        Path("requirements/horse.pip"),
        (SUFFIX_UNLOCKED,),
        False,
    ),
    (Path("requirements/horse.in"), (".tar", ".gz"), False),
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
    "relative_path, exts, expected",
    testdata_is_relative_required,
    ids=ids_is_relative_required,
)
def test_is_relative_required(relative_path, exts, expected):
    # pytest --showlocals --log-level INFO -k "test_is_relative_required" tests
    actual = is_relative_required(path_relative=relative_path, extensions=exts)
    assert actual == expected
