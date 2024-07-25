"""
.. code-block:: shell

   pytest --showlocals --log-level INFO tests/test_wrap_version_keyword.py
   pytest --showlocals --cov="drain_swamp" --cov-report=term-missing tests/test_wrap_version_keyword.py

.. seealso::

   https://github.com/pypa/setuptools/blob/main/setuptools/tests/test_dist.py
   https://setuptools.pypa.io/en/latest/userguide/package_discovery.html#package-discovery-and-namespace-packages
   https://github.com/pypa/setuptools_scm/blob/main/testing/test_integration.py

"""

import logging
import logging.config
from collections.abc import Mapping
from pathlib import Path
from unittest.mock import (
    MagicMock,
    patch,
)

import pytest  # noqa: F401
from setuptools.dist import Distribution
from setuptools_scm._config import Configuration

from drain_swamp.constants import (
    LOGGING,
    g_app_name,
)
from drain_swamp.monkey.patch_pyproject_reading import ReadPyprojectStrict
from drain_swamp.monkey.wrap_version_keyword import version_keyword


@pytest.fixture
def version_file():
    """Ensure the temporary version file is removed"""
    path_root_dir = Path(__file__).parent.parent
    path_f = path_root_dir.joinpath("src", "_version.py")
    path_f.touch()
    yield path_f
    path_root_dir.joinpath("src", "_version.py").unlink()


def test_version_keyword(caplog, has_logging_occurred, version_file):
    """setuptools-scm would normally needs a setup.py to be executed"""
    LOGGING["loggers"][g_app_name]["propagate"] = True
    logging.config.dictConfig(LOGGING)
    logger = logging.getLogger(name=g_app_name)
    logger.addHandler(hdlr=caplog.handler)
    caplog.handler.level = logger.level

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
