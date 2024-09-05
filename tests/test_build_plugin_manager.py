"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

..

Unittest for build plugins manager

Unit test -- Module

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

import pytest
from pluggy import PluginManager

import drain_swamp.monkey.plugins as package_plugins
from drain_swamp.monkey.hooks.manager import (
    get_plugin_manager,
    lazy_dotted_path,
    lazy_package,
)

testdata_get_plugin_manager = (
    (
        None,
        {},
        pytest.raises(TypeError),
    ),
    (
        1.2,
        {},
        pytest.raises(TypeError),
    ),
    (
        package_plugins,
        {"namespace": None},
        does_not_raise(),
    ),
    (
        package_plugins,
        {"specs_dotted_path": None},
        does_not_raise(),
    ),
    (
        package_plugins,
        {"entrypoint_plugins": None},
        does_not_raise(),
    ),
)
ids_get_plugin_manager = (
    "module is None",
    "module unsupposed type",
    "namespace None",
    "specs_dotted_path None",
    "entrypoint_plugins None",
)


@pytest.mark.parametrize(
    "mod_pkg, kwargs, expectation",
    testdata_get_plugin_manager,
    ids=ids_get_plugin_manager,
)
def test_get_plugin_manager(mod_pkg, kwargs, expectation):
    """Test get_plugin_manager."""
    # pytest --showlocals --log-level INFO -k "test_get_plugin_manager" tests
    with expectation:
        pm = get_plugin_manager(mod_pkg, **kwargs)
    if isinstance(expectation, does_not_raise):
        assert isinstance(pm, PluginManager)


testdata_lazy_package = (
    (
        None,
        pytest.raises(TypeError),
    ),
)
ids_lazy_package = ("None is not a module",)


@pytest.mark.parametrize(
    "mod_pkg, expectation",
    testdata_lazy_package,
    ids=ids_lazy_package,
)
def test_lazy_package(mod_pkg, expectation):
    """Test lazy_package exceptions."""
    # pytest --showlocals --log-level INFO -k "test_lazy_package" tests
    with expectation:
        lazy_package(mod_pkg)


testdata_lazy_dotted_path = (
    (
        None,
        pytest.raises(TypeError),
    ),
    (
        1.2345,
        pytest.raises(TypeError),
    ),
    (
        "os.path.bingo.moms",
        pytest.raises(ValueError),
    ),
    (
        "pytest",
        does_not_raise(),
    ),
    (
        "fileinput",
        does_not_raise(),
    ),
)

ids_lazy_dotted_path = (
    "None. Expected dotted path str",
    "Unsupposed type. Expected dotted path str",
    "dotted path to nonexistant module",
    "existing package. Already imported",
    "existing package. Needs to be imported",
)


@pytest.mark.parametrize(
    "dotted_path, expectation",
    testdata_lazy_dotted_path,
    ids=ids_lazy_dotted_path,
)
def test_lazy_dotted_path(dotted_path, expectation):
    """Test lazy_dotted_path."""
    # pytest --showlocals --log-level INFO -k "test_lazy_dotted_path" tests
    with expectation:
        lazy_dotted_path(dotted_path)
