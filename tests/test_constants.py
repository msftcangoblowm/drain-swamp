"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

Unittest for module, drain_swamp.backend_abc

Unit test -- Module

.. code-block:: shell

   python -m coverage run --source='drain_swamp.constants' -m pytest \
   --showlocals tests/test_constants.py && coverage report \
   --data-file=.coverage --include="**/constants.py"

"""

from collections.abc import Mapping
from unittest.mock import patch

import coverage
import pytest

import drain_swamp.constants as ds_constants

test_data_constants_logging = (
    (
        True,
        "verbose_with_color",
    ),
    (
        False,
        "simple",
    ),
)
ids_logger_propagate = (
    "pytest and DEBUG both on",
    "pytest and DEBUG both off",
)


@pytest.mark.parametrize(
    "propagation_expected, formatter_expected",
    test_data_constants_logging,
    ids=ids_logger_propagate,
)
def test_logger_propagate(propagation_expected, formatter_expected):
    """Turn on/off testing mode."""
    # pytest -vv --showlocals --log-level INFO -k "test_logger_propagate" tests
    coverage.process_startup()
    assert isinstance(ds_constants.LOGGING, Mapping)

    d = {"loggers": {"drain_swamp": {"propagate": propagation_expected}}}
    with patch.dict(ds_constants.LOGGING, d) as patched_foo:
        assert (
            patched_foo["loggers"]["drain_swamp"]["propagate"] is propagation_expected
        )
