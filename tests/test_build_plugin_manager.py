"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

Unittest for build plugins manager

With coverage

.. code-block:: shell

   python -m coverage run --source='drain_swamp.monkey.hooks.manager' -m pytest \
   --showlocals tests/test_build_plugin_manager.py && coverage report \
   --data-file=.coverage --include="**/monkey/hooks/manager.py"

Integration test

.. code-block:: shell

   make coverage
   pytest --showlocals --cov="drain_swamp" --cov-report=term-missing \
   --cov-config=pyproject.toml tests

"""

from contextlib import nullcontext as does_not_raise
from typing import TYPE_CHECKING

import pytest
from pluggy import PluginManager

import drain_swamp.monkey.plugins as package_plugins
from drain_swamp.monkey.hooks.manager import (
    get_plugin_manager,
    lazy_dotted_path,
    lazy_package,
)

if TYPE_CHECKING:
    from types import ModuleType

    from .typing_only import DOES_NOT_OR_DOES


@pytest.mark.parametrize(
    "mod_pkg, kwargs, expectation",
    (
        pytest.param(
            None,
            {},
            pytest.raises(TypeError),
            id="module-is-None",
        ),
        pytest.param(
            1.2,
            {},
            pytest.raises(TypeError),
            id="module-unsupported-type",
        ),
        pytest.param(
            package_plugins,
            {"namespace": None},
            does_not_raise(),
            id="namespace-None",
        ),
        pytest.param(
            package_plugins,
            {"specs_dotted_path": None},
            does_not_raise(),
            id="specs_dotted_path-None",
        ),
        pytest.param(
            package_plugins,
            {"entrypoint_plugins": None},
            does_not_raise(),
            id="entrypoint_plugins-None",
        ),
    ),
)
def test_get_plugin_manager(
    mod_pkg: "ModuleType | float | None",
    kwargs: dict[str, str | None],
    expectation: "DOES_NOT_OR_DOES",
) -> None:
    """Test get_plugin_manager."""
    # pytest --showlocals --log-level INFO -k "test_get_plugin_manager" tests
    with expectation:
        pm = get_plugin_manager(mod_pkg, **kwargs)
    if isinstance(expectation, does_not_raise):
        assert isinstance(pm, PluginManager)


@pytest.mark.parametrize(
    "mod_pkg, expectation",
    (
        pytest.param(
            None,
            pytest.raises(TypeError),
            id="None-is-not-a-module",
        ),
    ),
)
def test_lazy_package(mod_pkg: str | None, expectation: "DOES_NOT_OR_DOES") -> None:
    """Test lazy_package exceptions."""
    # pytest --showlocals --log-level INFO -k "test_lazy_package" tests
    with expectation:
        lazy_package(mod_pkg)


@pytest.mark.parametrize(
    "dotted_path, expectation",
    (
        pytest.param(
            None,
            pytest.raises(TypeError),
            id="None.-Expected-dotted-path-str",
        ),
        pytest.param(
            1.2345,
            pytest.raises(TypeError),
            id="Unsupported-type.-Expected-dotted-path-str",
        ),
        pytest.param(
            "os.path.bingo.moms",
            pytest.raises(ValueError),
            id="dotted-path-to-nonexistent-module",
        ),
        pytest.param(
            "pytest",
            does_not_raise(),
            id="existing-package.-Already-imported",
        ),
        pytest.param(
            "fileinput",
            does_not_raise(),
            id="existing-package.-Needs-to-be-imported",
        ),
    ),
)
def test_lazy_dotted_path(
    dotted_path: str | float | None,
    expectation: "DOES_NOT_OR_DOES",
) -> None:
    """Test lazy_dotted_path."""
    # pytest --showlocals --log-level INFO -k "test_lazy_dotted_path" tests
    with expectation:
        lazy_dotted_path(dotted_path)
