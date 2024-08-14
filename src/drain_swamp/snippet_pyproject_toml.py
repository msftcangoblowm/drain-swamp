from .constants import (
    SUFFIX_LOCKED,
    SUFFIX_SYMLINK,
    SUFFIX_UNLOCKED,
)
from .snip import (
    ReplaceResult,
    Snip,
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

    :rtype: drain_swamp.snip.ReplaceResult | None
    """

    snip = Snip(path_config, is_quiet=True)

    #    get
    t_out = snip.contents(id_=snippet_co)
    if t_out == ReplaceResult.VALIDATE_FAIL or t_out == ReplaceResult.NO_MATCH:
        return t_out
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
        snip.replace(contents, id_=snippet_co_actual)
    else:
        # Nothing to do. in pyproject.toml snippet. suffixes already SUFFIX_SYMLINK
        pass
