"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

Unit test -- Module

.. code-block:: shell

   python -m coverage run --source='drain_swamp.wrap_version_keyword' -m pytest \
   --showlocals tests/test_wrap_version_keyword.py && coverage report \
   --data-file=.coverage --include="**/wrap_version_keyword.py"

Integration test

.. code-block:: shell

   make coverage
   pytest --showlocals --cov="drain_swamp" --cov-report=term-missing \
   --cov-config=pyproject.toml tests

.. seealso::

   `[setuptools test_dist] <https://github.com/pypa/setuptools/blob/main/setuptools/tests/test_dist.py>`_
   `[setuptools package discovery] <https://setuptools.pypa.io/en/latest/userguide/package_discovery.html#package-discovery-and-namespace-packages>`_
   `[setuptools test integration] <https://github.com/pypa/setuptools_scm/blob/main/testing/test_integration.py>`_

"""

from collections.abc import Mapping
from pathlib import Path
from unittest.mock import (
    MagicMock,
    patch,
)

import pytest  # noqa: F401
from setuptools.dist import Distribution
from setuptools_scm._config import Configuration
from wreck.monkey.patch_pyproject_reading import ReadPyprojectStrict

from drain_swamp.constants import g_app_name
from drain_swamp.monkey.wrap_version_keyword import version_keyword


@pytest.fixture
def version_file():
    """Ensure the temporary version file is removed"""
    path_root_dir = Path(__file__).parent.parent
    path_f = path_root_dir.joinpath("src", "_version.py")
    path_f.touch()
    yield path_f
    path_f.unlink()


@pytest.mark.logging_package_name(g_app_name)
def test_version_keyword(logging_strict, has_logging_occurred, version_file):
    """setuptools-scm would normally needs a setup.py to be executed"""
    # pytest --showlocals --log-level INFO -k "test_version_keyword" tests
    t_two = logging_strict()
    logger, loggers = t_two

    path_root_dir = Path(__file__).parent.parent
    path_version_file_relpath = str(version_file.relative_to(path_root_dir))
    root_abspath = str(path_root_dir)
    package_dir = {"": "src"}
    attrs = {
        "src_root": root_abspath,
        "package_dir": package_dir,
    }
    key = "use_scm_version"

    # can be dict or True
    value = {"important": "stuff"}
    assert isinstance(value, Mapping)

    # from importlib.metadata import distribution
    # dist_0 = distribution(g_app_name)
    # pkg_name = dist_0.name
    # ver_pkg = dist_0.version
    # logger.info(f"dist.name: {pkg_name}")
    # logger.info(f"dist.version: {dist_0.version}")

    dist = Distribution(attrs)
    dist.set_defaults()

    relative_to = "pyproject.toml"
    data = {"root": root_abspath, "write_to": path_version_file_relpath}
    with (
        # setuptools_scm._integration.setuptools._assign_version
        patch(
            "setuptools_scm._integration.setuptools._config._read_pyproject",
            new_callable=MagicMock(wraps=ReadPyprojectStrict),
        ),
        # setuptools_scm._config.Configuration.from_file
        patch(
            "setuptools_scm._config._read_pyproject",
            new_callable=MagicMock(wraps=ReadPyprojectStrict),
        ),
        patch(
            "setuptools_scm._config.Configuration.from_data",
            return_value=Configuration.from_data(relative_to, data),
        ),
    ):
        # getter; not a setter. So src/_version.py not written to
        version_keyword(dist, key, value)

    assert isinstance(dist.metadata.version, str)
    assert len(dist.metadata.version) != 0
    # assert has_logging_occurred(caplog)
