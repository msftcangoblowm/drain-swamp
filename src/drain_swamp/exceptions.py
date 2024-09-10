"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

Package wide exceptions

.. py:data:: __all__
   :type: tuple[str, str, str]
   :value: ("PyProjectTOMLParseError", \
   "PyProjectTOMLReadError", "MissingRequirementsFoldersFiles")

   Module exports

"""

__package__ = "drain_swamp"
__all__ = (
    "PyProjectTOMLParseError",
    "PyProjectTOMLReadError",
    "MissingRequirementsFoldersFiles",
)


class PyProjectTOMLReadError(OSError):
    """``pyproject.toml`` Issue, not a file or insufficient permissions.

    Although an :py:exc:`OSError`, it's generic. The cause of the error
    is not passed forward (aka allowed to be lost)

    :ivar msg: The error message
    :vartype msg: str
    """

    def __init__(self, msg: str) -> None:
        """Class constructor."""
        errno = None
        super().__init__(errno, msg)


class PyProjectTOMLParseError(ValueError):
    """No point in continuing if the ``pyproject.toml`` can't be parsed and loaded.

    :ivar msg: The error message
    :vartype msg: str
    """

    def __init__(self, msg: str) -> None:
        """Class constructor."""
        super().__init__(msg)


class MissingRequirementsFoldersFiles(AssertionError):
    """Neglected to create/prepare requirements folders and ``.in`` files.

    Unabated would produce an empty string snippet. Instead provide
    user feedback

    :ivar msg: The error message
    :vartype msg: str
    """

    def __init__(self, msg: str) -> None:
        """Class constructor."""
        super().__init__(msg)
