"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

With coverage

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
from typing import TYPE_CHECKING
from unittest.mock import (
    MagicMock,
    patch,
)

import pytest  # noqa: F401
from setuptools.dist import Distribution
from wreck.monkey.patch_pyproject_reading import ReadPyprojectStrict

from drain_swamp.constants import g_app_name
from drain_swamp.monkey.wrap_version_keyword import version_keyword

try:
    from setuptools_scm._config import Configuration
except (ImportError, ModuleNotFoundError):  # pragma: no cover
    from vcs_versioning._config import Configuration

if TYPE_CHECKING:
    import logging
    from collections.abc import (
        Callable,
        Sequence,
    )


@pytest.fixture
def version_file(request: pytest.FixtureRequest) -> "Path":
    """Ensure the temporary version file is removed"""
    abspath_root_dir = request.path.parent.parent
    path_f = abspath_root_dir.joinpath("src", "_version.py")
    path_f.touch()
    yield path_f
    path_f.unlink()


@pytest.mark.logging_package_name(g_app_name)
def test_version_keyword(
    request: pytest.FixtureRequest,
    logging_strict: "Callable[[], tuple[logging.Logger, Sequence[logging.Logger]]]",
    has_logging_occurred: "Callable[[], bool]",
    version_file: "Path",
    has_vcs_versioning: bool,
) -> None:
    """setuptools-scm would normally needs a setup.py to be executed"""
    # pytest --showlocals --log-level INFO -k "test_version_keyword" tests
    t_two = logging_strict()
    logger, loggers = t_two

    abspath_root_dir = request.path.parent.parent
    path_version_file_relpath = str(version_file.relative_to(abspath_root_dir))
    root_abspath = str(abspath_root_dir)
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
    d_data = {
        "root": root_abspath,
        "write_to": path_version_file_relpath,
        "write_to_source": True,
    }
    # tool_names = ["DRAIN_SWAMP"]
    # env = VcsEnvironment.from_env(*tool_names, dist_name=dist)
    # pyproject = read_pyproject(path=Path(root_abspath).joinpath(relative_to), tool_names=[])

    if not has_vcs_versioning:
        # setuptools-scm>=8,<10 was subclassing, a forgiving, PyProjectData
        with (
            patch(
                "setuptools_scm._integration.setuptools._config._read_pyproject",
                new_callable=MagicMock(wraps=ReadPyprojectStrict),
            ),
            patch(
                "setuptools_scm._config._read_pyproject",
                new_callable=MagicMock(wraps=ReadPyprojectStrict),
            ),
            patch(
                "setuptools_scm._config.Configuration.from_data",
                return_value=Configuration.from_data(relative_to, d_data),
            ),
        ):
            # getter; not a setter. So src/_version.py not written to
            version_keyword(dist, key, value)
    else:
        # `vcs_versioning` has a dataclass (not NamedTuple), `PyProjectData`.
        #    config ([tool.vcs-versioning]) and drain_cfg ([tool.drain-swamp])
        #    can co-exist. `drain_swamp` only forwards `vcs_versioning` supported
        #     config settings to `vcs_versioning`.
        """
        with (
            patch(
                "vcs_versioning._pyproject_reading.read_pyproject",
                new_callable=MagicMock(wraps=ReadPyprojectStrict),
            ),
            patch(
                "vcs_versioning._config.Configuration.from_data",
                return_value=Configuration.from_data(relative_to, d_data),  # _env=env
            ),
        ):
            # getter; not a setter. So src/_version.py not written to
            version_keyword(dist, key, value)
        """
        # does this even need to be patched?!
        version_keyword(dist, key, value)

    assert isinstance(dist.metadata.version, str)
    assert len(dist.metadata.version) != 0
    # assert has_logging_occurred(caplog)
