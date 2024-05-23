from __future__ import annotations

from setuptools import setup
from setuptools_scm.version import (
    get_local_node_and_date,
    guess_next_dev_version,
)


def _clean_version() -> dict[str, str]:
    """``setuptools-scm`` get the current version if you're in a tagged commit.
    When not, most of the time, tries very hard to "guess" the next version
    dividing it in two parts, the "version" and the "local" part, with the
    format {version}+{local}, both of them can be configured.

    CI/CD configuration

    Runs on every push, but setup to do nothing unless on a tagged release

    LOCAL

    Options

    - node-and-date (default)
    - node-and-timestamp
    - dirty-tag
    - no-local-version

    Although pypi only accepts ``no-local-version``, chose
    ``node-and-date`` (:py:func:`get_local_node_and_date`)

    Rationale:

    - when testing locally, a non-local version build would be very confusing

    - never have uncommitted files in workdir (+dirty or +clean)

    VERSION

    Try default, ``guess-next-dev``

    :returns:

       dict containing handlers for version_scheme and local_scheme. The
       resulting str are combined with format, ``{version}+{local}``

    :rtype: dict[str, str]

    .. seealso::

       Built-in
       `[version_scheme] <https://setuptools-scm.readthedocs.io/en/latest/extending/#setuptools_scmversion_scheme>`_
       handlers

       Built-in
       `[local_scheme] <https://setuptools-scm.readthedocs.io/en/latest/extending/#setuptools_scmlocal_scheme>`_
       handlers

       For usage, see :py:mod:`logging_strict.constants`

    """
    return {
        "local_scheme": get_local_node_and_date,
        "version_scheme": guess_next_dev_version,
    }


# dict communicating between :menuselection:`setuptools_scm --> setuptools`
setup(
    use_scm_version=_clean_version,
)
