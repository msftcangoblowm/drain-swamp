"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

:py:meth:`datetime.datetime.strftime` has spotty feature support.

There are unsupported features affecting particular platforms. Fix those issues.

.. py:data:: _d_convert
   :type: dict[str, tuple[Callable[[dt, str], bool], str]

   The key is a strftime format str that needs a fix for a particular platform
   Value tuple contains a fix function and a boolean indicating if the platform
   needs to apply this fix.

.. py:data:: __all__
   :type: tuple[str]
   :value: ("StrFTime",)

   Module exports.

"""

import abc
import shlex

from .._safe_path import (
    is_linux,
    is_macos,
)

__all__ = ("StrFTime",)


class Patch(abc.ABC):
    """ABC of patches. A patch knows the affected token and platform."""

    @abc.abstractmethod
    def __call__(self, dt_a, str_part):
        """Makes subclass a callable.

        :param dt_a: Fix requires the datetime, to base the fix on
        :type dt_a: datetime.datetime
        :param str_part: May contain other characters and one token
        :type str_part: str
        """
        ...


class PatchLeadingDay(Patch):
    """Patch to fix ``%-d``.

    .. py:attribute:: AFFECTED_TOKEN
       :type: str
       :value: "%-d"

       Affects this token

    .. py:attribute:: AFFECTS
       :type: bool

       Affects these platforms

    """

    AFFECTED_TOKEN = "%-d"
    AFFECTS = not (is_linux() or is_macos())

    def __call__(self, dt_a, str_part):
        """Replace bad token ``<perc><hyphen>d``.

        :param dt_a: Fix requires the datetime, to base the fix on
        :type dt_a: datetime.datetime
        :param str_part: May contain other characters and one token
        :type str_part: str
        :returns: fixed token or rendered value
        :rtype: str
        """
        cls = type(self)
        token_bad = cls.AFFECTED_TOKEN

        str_portable = dt_a.strftime("%d").lstrip("0")

        return str_part.replace(token_bad, str_portable)


class PatchAggregateD(Patch):
    """Patch to fix ``%D``.

    .. py:attribute:: AFFECTED_TOKEN
       :type: str
       :value: "%D"

       Affects this token

    .. py:attribute:: AFFECTS
       :type: bool
       :value: False

       Affects these platforms. Does not seem to affect MacOS.

    """

    AFFECTED_TOKEN = "%D"
    AFFECTS = False

    def __call__(self, dt_a, str_part):
        """Replace bad token ``<perc>D``.

        :param dt_a: Fix requires the datetime, to base the fix on
        :type dt_a: datetime.datetime
        :param str_part: May contain other characters and one token
        :type str_part: str
        :returns: fixed token or rendered value
        :rtype: str
        """
        cls = type(self)
        token_bad = cls.AFFECTED_TOKEN
        replace_with = "%m/%d/%Y"

        return str_part.replace(token_bad, replace_with)


class PatchAggregateT(Patch):
    """Patch to fix ``%T``.

    .. py:attribute:: AFFECTED_TOKEN
       :type: str
       :value: "%T"

       Affects this token

    .. py:attribute:: AFFECTS
       :type: bool

       Affects these platforms

    """

    AFFECTED_TOKEN = "%T"
    AFFECTS = False

    def __call__(self, dt_a, str_part):
        """Replace bad token ``<perc>T``.

        :param dt_a: Fix requires the datetime, to base the fix on
        :type dt_a: datetime.datetime
        :param str_part: May contain other characters and one token
        :type str_part: str
        :returns: fixed token or rendered value
        :rtype: str
        """
        cls = type(self)
        token_bad = cls.AFFECTED_TOKEN

        replace_with = "%H:%M:%S"

        return str_part.replace(token_bad, replace_with)


class StrFTime:
    """:py:class:`datetime.datetime` is a type. Monkey patching a
    built-in (C code) is impossible. Instead just provide a class with
    only one method, strftime

    .. py:attribute: patches
       :type: tuple[type[Patch], ...]

       Patches that fix holes in platform specific strftime implementations

    :ivar dt: datetime instance to act upon
    :vartype dt: datetime.datetime

    """

    patches = (PatchLeadingDay, PatchAggregateD, PatchAggregateT)

    def __init__(self, dt):
        """Class constructor."""
        self._dt = dt

    @classmethod
    def fix_strftime_input(cls, dt_a, strftime_str):
        """Run all strftime fixes.

        :param dt_a: Fix requires the datetime, to base the fix on
        :type dt_a: datetime.datetime
        :param strftime_str: Format str
        :type strftime_str: str
        :returns: Fixed strftime format str
        :rtype: str
        """
        parts = shlex.split(strftime_str)
        for idx, str_part in enumerate(parts):
            for cls_patch in cls.patches:
                affects = cls_patch.AFFECTS
                token = cls_patch.AFFECTED_TOKEN
                is_affected = affects and token in str_part
                if is_affected:
                    # Apply patch
                    parts[idx] = cls_patch()(dt_a, str_part)
                else:  # pragma: no cover
                    pass
        str_fixed = " ".join(parts)

        return str_fixed

    def strftime(self, format_):
        """Format datetime as str.

        :param dt_a: datetime to format
        :type dt_a: datetime.datetime
        :param strftime_str: format str
        :type strftime_str: str
        :returns: Formatted datetime str
        :rtype: str
        :raises:

           - :py:exc:`TypeError` -- Unsupported type expected str

        """
        if format_ is None or not isinstance(format_, str):
            msg_warn = f"Unsupported type expected str got {type(format_)}"
            raise TypeError(msg_warn)
        else:  # pragma: no cover
            pass

        cls = type(self)
        str_fixed = cls.fix_strftime_input(self._dt, format_)
        ret = self._dt.strftime(str_fixed)

        return ret
