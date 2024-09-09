"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

repr helpers. Careful to use PurePath subclasses

.. py:data:: __all__
   :type: tuple[str, str, str]
   :value: ("repr_dict_str_path", "repr_set_path", "repr_path")

   Module's exports

"""

from collections.abc import (
    Mapping,
    MutableSet,
)
from pathlib import PurePath

from ._safe_path import _to_purepath

__all__ = (
    "repr_dict_str_path",
    "repr_set_path",
    "repr_path",
)


def _fix_bool(val, default=False):
    """Fix bool.

    :param val: A value hopefully a bool
    :type val: typing.Any
    :param val: Default is False unless override provided
    :type val: bool
    :returns: Any --> bool
    :rtype: bool
    """
    is_l = val is not None and isinstance(val, bool)
    if not is_l:
        ret = default
    else:
        ret = val

    return ret


def _append_comma(str_a, is_condition):
    """Append <comma><space> if condition is met.

    :param str_a: original str
    :type str_a: str
    :param is_condition: True append the token
    :type is_condition: bool
    :returns: concatenated str
    :rtype: str
    """
    token = ", "
    if is_condition:
        ret = f"{str_a}{token}"
    else:
        ret = str_a

    return ret


def repr_dict_str_path(k, d_repr, is_last=False):
    """repr of dict value is a :py:func:`pathlib.Path`.

    :param k: Class field name
    :type k: str
    :param d_repr: dict containing a path value
    :type d_repr: dict[str, pathlib.Path]
    :param is_last: Default False. Is last line of the repr. If False, appends ``", "``
    :type is_last: bool
    :returns: Portion of a repr
    :rtype: str
    :raises:

        - :py:exc:`TypeError` -- If an arg has unexpected type

    """
    is_last_bool = _fix_bool(is_last)

    is_k = k is not None and isinstance(k, str)
    is_d_repr = d_repr is not None and isinstance(d_repr, Mapping)
    conditions = (is_k, is_d_repr)
    is_conditions = all(conditions)
    msg_warn = f"k is an str. d_repr is a Mapping. Got {type(k)} {type(d_repr)}"
    if not is_conditions:  # pragma: no cover
        raise TypeError(msg_warn)
    else:  # pragma: no cover
        pass

    val = "{"
    idx_last = len(d_repr.keys()) - 1
    for idx, t_pair in enumerate(d_repr.items()):
        k_0, v_0 = t_pair
        pure_v_0 = _to_purepath(v_0)
        val += f"""'{k_0!s}': {pure_v_0!r}"""

        is_last_item = idx != idx_last
        if is_last_item:
            val += ", "
        else:  # pragma: no cover
            pass

    val += "}"

    ret = f"{k}={val}"
    ret = _append_comma(ret, not is_last_bool)

    return ret


def repr_set_path(k, set_repr, is_last=False):
    """repr of set of :py:func:`pathlib.Path`.

    :param k: Class field name
    :type k: str
    :param set_repr: set containing a path value
    :type set_repr: set[pathlib.Path]
    :param is_last: Default False. Is last line of the repr. If False, appends ``", "``
    :type is_last: bool
    :returns: Portion of a repr
    :rtype: str
    :raises:

        - :py:exc:`TypeError` -- If an arg has unexpected type

    """
    is_last_bool = _fix_bool(is_last)

    is_k = k is not None and isinstance(k, str)
    is_set_repr = set_repr is not None and isinstance(set_repr, MutableSet)
    conditions = (is_k, is_set_repr)
    is_conditions = all(conditions)
    msg_warn = (
        "k is an str. set_repr is a MutableSet. Got "
        f"{type(k)} {type(set_repr)} {type(is_last)}"
    )
    if not is_conditions:  # pragma: no cover
        raise TypeError(msg_warn)
    else:  # pragma: no cover
        pass

    val = "{"
    idx_last = len(set_repr) - 1
    for idx, path_f in enumerate(set_repr):
        pure_f = _to_purepath(path_f)
        val += repr(pure_f)

        is_last_item = idx != idx_last
        if is_last_item:
            val += ", "
        else:  # pragma: no cover
            pass

    val += "}"

    ret = f"{k}={val}"
    ret = _append_comma(ret, not is_last_bool)

    return ret


def repr_path(k, path, is_last=False):
    """repr of a :py:func:`pathlib.Path`.

    :param k: Class field name
    :type k: str
    :param path: set containing a path value
    :type path: set[pathlib.Path]
    :param is_last: Default False. Is last line of the repr. If False, appends ``", "``
    :type is_last: bool
    :returns: Portion of a repr
    :rtype: str
    :raises:

        - :py:exc:`TypeError` -- If an arg has unexpected type

    """
    is_last_bool = _fix_bool(is_last)

    is_k = k is not None and isinstance(k, str)
    is_path = path is not None and issubclass(type(path), PurePath)

    conditions = (is_k, is_path)
    is_conditions = all(conditions)
    msg_warn = (
        "k is an str. path is a PurePath. Got "
        f"{type(k)} {type(path)} {type(is_last)}"
    )
    if not is_conditions:  # pragma: no cover
        raise TypeError(msg_warn)
    else:  # pragma: no cover
        pass

    pure_f = _to_purepath(path)
    val = f"{pure_f!r}"

    ret = f"{k}={val}"
    ret = _append_comma(ret, not is_last_bool)

    return ret
