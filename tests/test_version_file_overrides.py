"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

Integration test

.. code-block:: shell

   make coverage
   pytest --showlocals --cov="drain_swamp" --cov-report=term-missing \
   --cov-config=pyproject.toml tests

"""

import os
from unittest.mock import patch

import pytest

from drain_swamp.version_file._overrides import (
    _scm_key,
    normalize_dist_name,
    read_named_env,
)


@pytest.mark.parametrize(
    "dist_name, expected",
    (
        pytest.param(
            "awesome.special_project",
            "AWESOME_SPECIAL_PROJECT",
            id="period-and-underline",
        ),
        pytest.param(
            "awesome.special-project-",
            "AWESOME_SPECIAL_PROJECT_",
            id="period-and-hyphens.-Trailing-hyphen",
        ),
    ),
)
def test_normalize_dist_name(dist_name: str, expected: str) -> None:
    """Test normalizing dist name."""
    actual = normalize_dist_name(dist_name)
    assert actual == expected


def test_read_named_env() -> None:
    """Test read_named_env."""
    env_0 = os.environ.copy()
    dist_name = "AWESOME_SPECIAL_PROJECT"
    scm_ver = "0.0.1"

    # PRETEND_VERSION -- env variable exists
    key = _scm_key(dist_name)
    env_0[key] = scm_ver
    with patch("os.environ.get", wraps=env_0.get):
        actual_val = read_named_env(name="PRETEND_VERSION", dist_name=dist_name)
    assert actual_val == scm_ver

    # OVERRIDES -- no dist_name
    dist_name = None
    env_1 = os.environ.copy()
    key = "SETUPTOOLS_SCM_PRETEND_VERSION"
    env_1[key] = scm_ver
    with patch("os.environ.get", wraps=env_1.get):
        actual_val = read_named_env(name="PRETEND_VERSION", dist_name=None)
    assert actual_val == scm_ver
