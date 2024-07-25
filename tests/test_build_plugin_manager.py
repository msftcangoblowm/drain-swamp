"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

..

Unittest for build plugins manager

.. code-block:: shell

   pytest --showlocals --log-level INFO tests/test_build_plugin_manager.py
   pytest --showlocals --cov="drain_swamp" --cov-report=term-missing tests/test_build_plugin_manager.py

"""

import pytest
from pluggy import PluginManager

import drain_swamp.monkey.plugins as package_plugins
from drain_swamp.monkey.hooks.manager import (
    get_plugin_manager,
    lazy_dotted_path,
    lazy_package,
)


def test_get_plugin_manager():
    # pytest --showlocals --log-level INFO -k "test_get_plugin_manager" tests
    # positional arg unsupported type --> TypeError
    invalids = (
        None,
        1.2,
    )
    for invalid in invalids:
        with pytest.raises(TypeError):
            get_plugin_manager(invalid)

    #
    pm = get_plugin_manager(
        package_plugins,
        namespace=None,
    )
    assert isinstance(pm, PluginManager)
    del pm
    pm = get_plugin_manager(
        package_plugins,
        specs_dotted_path=None,
    )
    assert isinstance(pm, PluginManager)
    del pm
    pm = get_plugin_manager(
        package_plugins,
        entrypoint_plugins=None,
    )
    assert isinstance(pm, PluginManager)


def test_lazy_package():
    # pytest --showlocals --log-level INFO -k "test_lazy_package" tests
    # unsupported types
    with pytest.raises(TypeError):
        lazy_package(None)
    with pytest.raises(TypeError):
        lazy_dotted_path(None)
