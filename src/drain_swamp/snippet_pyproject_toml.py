"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

Normally a snippet parser does not have any insights or understanding of the
snippet contents. Manipulating the contents is not the best idea.

This is an unavoidable exceptional case where ``UX > coding orthodoxy``

The ``pyproject.toml`` snippet handles the dependency locks. lock and unlock
updates ``pyproject.toml`` with their respective suffix. Then the refresh
command is run which also will need to update the dependency locks' suffix

``lock`` and ``unlock`` replace the entire snippet contents

``refresh`` is being sly, delving into matters it hasn't the facilities
to comprehend. Manipulating the dependency lock suffix if it ends with
``.unlock`` or ``.lock``. But what if it's something else? Then can't guarantee
the refresh accomplishes it's task

.. py:data:: SNIPPET_NO_MATCH
   :type: str

   Warning message when no snippet found with a particular snippet id

.. py:data:: SNIPPET_VALIDATE_FAIL
   :type: str

   Warning message when a snippet is invalid

.. py:data:: __all__
   :type: tuple[str, str, str]
   :value: ("SNIPPET_NO_MATCH", "SNIPPET_VALIDATE_FAIL", "snippet_replace_suffixes")

.. py:data:: is_module_debug
   :type: bool

   Module debugging messages flag

.. py:data:: _logger
   :type: logging.Logger

   Module level logger

"""

import logging

from drain_swamp_snippet import (
    ReplaceResult,
    Snip,
)

from .constants import (
    SUFFIX_LOCKED,
    SUFFIX_SYMLINK,
    SUFFIX_UNLOCKED,
    g_app_name,
)

SNIPPET_NO_MATCH = "In pyproject.toml, there is no snippet with snippet code {}"
SNIPPET_VALIDATE_FAIL = (
    "Snippet is invalid. Validation failed. Either nested or "
    "unmatched start end tokens"
)

__all__ = (
    "SNIPPET_NO_MATCH",
    "SNIPPET_VALIDATE_FAIL",
    "snippet_replace_suffixes",
)
is_module_debug = False
_logger = logging.getLogger(f"{g_app_name}.snippet_pyproject_toml")


def snippet_replace_suffixes(path_config, snippet_co=None):
    """in pyproject.toml, replace .lock or .unlock --> .lnk

    :param path_config: path to ``pyproject.toml`` file
    :type path_config: pathlib.Path
    :param snippet_co:

       Default None. Snippet code to ``pyproject.toml`` snippet. Only
       needed if multiple. This snippet should contain:
       dependency and optional-dependencies

    :type snippet_co: str | None
    :returns:

        On success, None. Otherwise check for
        ReplaceResult.VALIDATE_FAIL and ReplaceResult.NO_MATCH

    :rtype: drain_swamp_snippet.ReplaceResult | None
    """

    modpath = f"{g_app_name}.snippet_pyproject_toml.snippet_replace_suffixes"
    if is_module_debug:  # pragma: no cover
        msg_info = f"{modpath} path containing snippet {path_config!r}"
        _logger.info(msg_info)
    else:  # pragma: no cover
        pass

    snip = Snip(path_config)

    #    get
    t_out = snip.contents(id_=snippet_co)
    if t_out == ReplaceResult.VALIDATE_FAIL or t_out == ReplaceResult.NO_MATCH:
        return t_out
    else:  # pragma: no cover
        pass

    if is_module_debug:  # pragma: no cover
        msg_info = f"{modpath} t_out (after snippet read) {t_out!r}"
        _logger.info(msg_info)
    else:  # pragma: no cover
        pass

    contents, snippet_co_actual = t_out
    contents_orig = contents

    #    modify
    suffixes = (
        SUFFIX_UNLOCKED,
        SUFFIX_LOCKED,
    )
    for suffix in suffixes:
        if suffix in contents:
            contents = contents.replace(suffix, SUFFIX_SYMLINK)
        else:  # pragma: no cover
            pass

    #    replace
    is_not_same = contents_orig != contents
    if is_not_same:
        if is_module_debug:  # pragma: no cover
            msg_info = (
                f"{modpath} snippet contents(before snippet replace): {contents!r}"
            )
            _logger.info(msg_info)
        else:  # pragma: no cover
            pass

        snip.replace(contents, id_=snippet_co_actual)
    else:
        # Nothing to do. in pyproject.toml snippet. suffixes already SUFFIX_SYMLINK
        pass
