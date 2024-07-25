"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

Module to construct setuptools-scm PRETEND_VERSION environment variable string

.. py:data:: PRETEND_KEY
   :type: str
   :value: "SETUPTOOLS_SCM_PRETEND_VERSION"

.. py:data:: PRETEND_KEY_NAMED
   :type: str
   :value: "SETUPTOOLS_SCM_PRETEND_VERSION_for_{name}"

   Get environmental variable key for forcing setuptools-scm to use a
   particular semantic version

.. py:data:: __all__
   :type: tuple[str]
   :value: ("normalize_dist_name")

   Module exports

.. seealso::

   `[Source] <https://github.com/pypa/setuptools_scm/blob/main/src/setuptools_scm/_overrides.py>`_
   `[LICENSE:MIT] <https://github.com/pypa/setuptools_scm/blob/main/LICENSE>`_

"""

import os
import re

PRETEND_KEY = "SETUPTOOLS_SCM_PRETEND_VERSION"
PRETEND_KEY_NAMED = PRETEND_KEY + "_FOR_{name}"

__all__ = ("normalize_dist_name",)


def normalize_dist_name(dist_name):
    """Normalize the dist name as per PEP 503

    :param dist_name:

       May contain period(s), hyphen(s), and/or underscore(s)

    :type dist_name: str
    :returns: dist name normalized and uppercase
    :rtype: str
    """
    normalized_dist_name = re.sub(r"[-_.]+", "-", dist_name)
    env_var_dist_name = normalized_dist_name.replace("-", "_").upper()

    return env_var_dist_name


def _scm_key(dist_name):
    """When want to set a specific version, setuptools-scm offers an
    environment variable which overrides normal behavior

    This is needed when wanting to create a:
    - tagged version
    - post-release version
    - pre-release version

    :param dist_name:

       package name. Will upper case and replace hyphens with underscores

    :type dist_name: str
    :returns: environment variable to affect setuptools-scm behavior
    :rtype: str
    :meta private:
    """
    # source setuptools_scm._override.read_named_env
    env_var_dist_name = normalize_dist_name(dist_name)
    d_named = {"name": env_var_dist_name}
    scm_override_key = PRETEND_KEY_NAMED.format(**d_named)

    return scm_override_key


def read_named_env(
    *,
    tool="SETUPTOOLS_SCM",
    name,
    dist_name,
):
    """From environment, get variable value. Will contain the version

    :param tool: Default "SETUPTOOLS_SCM". Hardcoded tool name
    :type tool: str
    :param name: Can be ``PRETEND_VERSION`` or ``OVERRIDES``
    :type name: str
    :param dist_name: target package name
    :type dist_name: str | None
    :returns: version str
    :rtype: str | None
    """
    if dist_name is not None:
        # Normalize the dist name as per PEP 503.
        env_var_dist_name = normalize_dist_name(dist_name)
        val = os.environ.get(f"{tool}_{name}_FOR_{env_var_dist_name}")
        if val is not None:
            ret = val
        else:  # pragma: no cover
            ret = None
    else:  # pragma: no cover
        ret = None

    if ret is None:
        ret = os.environ.get(f"{tool}_{name}")
    else:  # pragma: no cover
        pass

    return ret
