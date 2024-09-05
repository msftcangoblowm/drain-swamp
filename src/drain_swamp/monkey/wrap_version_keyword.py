"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

Removes the need for a ``setup.py`` file.

In ``pyproject.toml``,

    .. code-block:: text

       [project.entry-points."distutils.setup_keywords"]
       use_scm_version = "drain_swamp.monkey.wrap_version_keyword:version_keyword"


.. py:data:: log
   :type: logging.Logger

   Module level logger

"""

import logging

from setuptools_scm._integration.setuptools import version_keyword as _version_keyword
from setuptools_scm.version import (
    get_local_node_and_date,
    guess_next_dev_version,
)

log = logging.getLogger("drain_swamp.monkey.wrap_version_keyword")


def version_keyword(dist, keyword, value):
    """Called by entrypoint project.entry-points."distutils.setup_keywords".

    With this setup. setup.py is unneeded for versioning purposes.

    In ``pyproject.toml``,

    .. code-block:: text

       [project.entry-points."distutils.setup_keywords"]
       use_scm_version = "drain_swamp.monkey.wrap_version_keyword:version_keyword"

    :param dist: API interface for interacting with setuptools
    :type dist: setuptools.Distribution
    :param keyword: Will be ignored
    :type keyword: str
    :param value: overrides dict normally supplied in setup.py
    :type value: bool | dict[str, typing.Any] | collections.abc.Callable[[], dict[str, typing.Any]]
    """
    # keyword = "use_scm_version"
    d_value = {
        "local_scheme": get_local_node_and_date,
        "version_scheme": guess_next_dev_version,
    }
    # In version_keyword _config.Configuration.from_file param _require_section=False
    _version_keyword(dist, keyword, d_value)
