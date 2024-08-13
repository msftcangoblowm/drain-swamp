"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

Check if package is installed.

Used by multiple modules; separated to keep DRY

.. py:data:: __all__
   :type: tuple[str]
   :value: ("is_package_installed",)

   Module exports

"""

from importlib.metadata import (
    PackageNotFoundError,
    metadata,
)

__all__ = ("is_package_installed",)


def is_package_installed(app_name):
    """Check if package is installed

    :param app_name: Accepts either package name or app name. No need for check
    :type app_name: str
    :returns: True package is installed otherwise False
    :rtype: bool
    """
    # metadata is hardened; accepts either package name or app name
    try:
        metadata(app_name)
    except PackageNotFoundError:
        ret = False
    else:
        ret = True

    return ret
