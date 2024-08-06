"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

The _version module is generated and not guaranteed to exist.

When _version is missing, such as after a :code:`git clone` or within CI/CD,
there is no reason to allow this fyi only package info to be the cause of failure

.. py:data:: __version_app
   :type: str

   Official app version. Semantic versioning fully supported. So pre and post releases,
   release candidate, and dev releases are possible

   tagged post releases are encouraged. Cuz that means used
   :command:`git rebase` to fix a problem at when it originally occured
   rather than applying the fix and ignoring the past

.. py:data:: __url__
   :type: str

   rtd URL to for current tagged version. This is not used for anything.
   Just here for completeness.

.. py:data:: __all__
   :type: tuple[str, str]
   :value: ("__version_app", "__url__")

   Module exports

.. todo:: lookup module

   Lookup in pyproject.toml for the dotted path of version file. Then
   atttempt to import it

"""

from .constants import g_app_name
from .version_semantic import (
    SemVersion,
    sanitize_tag,
)

__all__ = (
    "__version_app",
    "__url__",
)

try:
    # hardcoded import is bad
    from ._version import __version__
except (ModuleNotFoundError, ImportError):  # pragma: no cover
    __version_app = "unreleased"
    __url__ = None
else:
    # Removes epoch and local. Fixes version
    __version_app, local = sanitize_tag(__version__)

    sv = SemVersion()
    sv.parse_ver(__version__, local=local)
    __url__ = sv.readthedocs_url(g_app_name, is_latest=False)
