"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

Get semantic version from scm and write version file

Limit to setuptools-scm codebase. Is exactly equivalent to generic
setuptools-scm ``setup.py``

.. py:data:: log
   :type: logging.Logger

   Module level logger

.. py:data:: __all__
   :type: tuple[str, str, str]
   :value: ("scm_version", "write_to_file", "SEM_VERSION_FALLBACK_SANE")

"""

from __future__ import annotations

import contextlib
import io
import logging
import warnings
from pathlib import Path

from setuptools_scm import (
    Configuration,
    _get_version,
    git,
    hg,
)
from setuptools_scm._integration.pyproject_reading import get_args_for_pyproject
from setuptools_scm._overrides import read_toml_overrides
from setuptools_scm._version_cls import InvalidVersion
from setuptools_scm.fallbacks import parse_pkginfo
from setuptools_scm.version import (
    get_local_node_and_date,
    guess_next_dev_version,
    tag_to_version,
)

from ..version_file.dump_version import write_version_files
from .patch_pyproject_reading import ReadPyproject

log = logging.getLogger("drain_swamp.monkey.wrap_get_version")

__all__ = (
    "scm_version",
    "write_to_file",
    "SEM_VERSION_FALLBACK_SANE",
)

SEM_VERSION_FALLBACK_SANE = "0.0.1"

try_parse = [
    parse_pkginfo,
    git.parse,
    hg.parse,
    git.parse_archival,
    hg.parse_archival,
]


def _parse(root, config):
    """Get the version from underlying scm. Either pkginfo, git, or Mercurial

    :param root: absolute path to root or file on repo base folder
    :type root: str
    :param config:

       A data class usually derived for the most part from ``pyproject.toml``

    :type config: Configuration
    :returns: version str from the underlying scm
    :rtype: ScmVersion | None
    :meta private:
    """
    mod_path = "drain_swamp.monkey.wrap_get_version._parse"
    for maybe_parse in try_parse:
        try:
            # temporarily suppress stderr
            # WARNING  command hg missing:
            # [Errno 2] No such file or directory: 'hg'            _run_cmd.py:195
            with contextlib.redirect_stderr(io.StringIO()):
                parsed = maybe_parse(root, config)
        except OSError as e:
            # Happens often, so suppress importance
            msg_info = f"{mod_path} parse with {maybe_parse!s} failed with: {e!s}"
            log.info(msg_info)
        else:
            if parsed is not None:  # pragma: no cover
                """tox, runs within it's own virtual environment, during
                testing, does not see git. So file finder will not find any match"""
                return parsed
            else:  # pragma: no cover
                pass
    else:
        return None


def scm_version(relative_to, sane_default=SEM_VERSION_FALLBACK_SANE):
    """Get the scm version from git or Mercurial

    Does not write to the version_file

    :param relative_to: absolute path to a file on the repo base folder
    :type relative_to: str
    :param sane_default:

       Default "0.0.1". Fallback version when cannot get scm version
       cuz git uninitialized

    :type sane_default: typing.Any | None
    :returns: parsed version str
    :rtype: str

    .. seealso::

       https://github.com/pypa/setuptools_scm/blob/main/src/setuptools_scm/_get_version_impl.py

    """
    mod_path = "drain_swamp.monkey.wrap_get_version:scm_version"
    is_empty = (
        sane_default is None
        or not isinstance(sane_default, str)
        or len(sane_default.strip()) == 0
    )
    if is_empty:  # pragma: no cover
        sane_default = SEM_VERSION_FALLBACK_SANE
    else:  # pragma: no cover
        pass

    """Configuration.from_file needs to be patched, not Configuration.from_data
    Configuration.from_data does not parse pyproject.toml can't / don't
    write to version_file
    """
    d_data = {
        "parse": _parse,
        "version_scheme": guess_next_dev_version,
        "local_scheme": get_local_node_and_date,
    }
    config = Configuration.from_data(relative_to, d_data)

    scm_ver = _get_version(config, force_write_version_files=False)

    # Apply sane default if no override, no version_file, and no fallback
    if scm_ver is None:
        ret = sane_default
    else:
        ret = scm_ver

    msg_info = f"INFO {mod_path} parsed version: {ret} "
    log.info(msg_info)

    return ret


def write_to_file(
    name: str,
    str_ver: str,
    write_to: str | None = None,
    dist_name: str | None = None,
    is_only_not_exists: bool | None = False,
) -> None:
    """Write version_file

    read_pyproject default is to combine sections:
    [tool.drain_swamp] and [tool.pipenv-unlock]

    Does not read section [tool-setuptools-scm]

    :param name: absolute path to a file on the repo base folder
    :type name: str
    :param str_ver: version str
    :type str_ver: str
    :param write_to: Default None. override version_file. Used for testing
    :type write_to: str | None
    :param dist_name:

       Default None. pyproject.toml section [tool.[name]] Unspecified --> pipenv-unlock

    :type dist_name: str | None
    :param is_only_not_exists: Default False. Write file only if it does not already exit
    :type is_only_not_exists: bool | None
    :raises:

       - :py:exc:`LookupError` -- Either pyproject.toml missing or
         required missing sections

       - :py:exc:`ValueError` -- Semantic version str invalid. Write
         to version file skipped

    """
    if is_only_not_exists is None or not isinstance(is_only_not_exists, bool):
        is_only_not_exists = False
    else:  # pragma: no cover
        pass

    kwargs = {}
    path_file_on_root = Path(name)
    path_root = path_file_on_root.parent

    try:
        # pyproject_data = read_pyproject(path_file_on_root)
        pyproject_data = ReadPyproject()(path=path_file_on_root)
    except LookupError as e:
        msg_info = (
            "To set version_file, in pyproject.toml [tool.pipenv-unlock] "
            "Set version_file to a relative path to a .py file"
        )
        # log.info(msg_info)
        msg_warn = (
            "Either missing pyproject.toml or missing sections: "
            "[tool.drain-swamp] and [tool.pipenv-unlock] "
            f"{path_file_on_root}"
        )
        # log.warning(msg_warn)
        msgs = f"{msg_info}\n{msg_warn}"
        raise LookupError(msgs) from e

    args = get_args_for_pyproject(pyproject_data, dist_name, kwargs)
    args.update(read_toml_overrides(args["dist_name"]))
    # relative_to = args.pop("relative_to", name)

    is_empty = (
        write_to is None or not isinstance(write_to, str) or len(write_to.strip()) == 0
    )
    if is_empty:
        version_file = args.get("version_file")
        str_write_to = None
    else:
        # for testing
        version_file = None
        str_write_to = write_to

    # Check semantic version str. Skip if invalid
    config = Configuration()
    #    py311+ warnings.catch_warnings has category and action kwargs
    with warnings.catch_warnings():
        # setuptools_scm/version.py:102: UserWarning:
        # tag 'golf balls get lost' no version found
        warnings.simplefilter("ignore")
        msg_warn = (
            "drain_swamp.monkey.wrap_get_version invalid semantic version str, "
            f"{str_ver!r}. Write version file skipped"
        )
        # BUG (upstream setuptools-scm): not catching InvalidVersion exception
        try:
            ver_clean = tag_to_version(str_ver, config)
        except InvalidVersion:
            """Passes regex (setuptools_scm.version._parse_version_tag),
            but is invalid semantic version str, e.g. '0.0.1-dev1.g1234123'

            Exception properly handled in setuptools_scm._version_cls._version_as_tuple
            """
            is_invalid = True
        else:
            if ver_clean is None:
                # not a semantic version str e.g.
                # 'getting hit by a golf ball hurts'
                is_invalid = True
            else:
                is_invalid = False

        if is_invalid is True:
            raise ValueError(msg_warn)
        else:
            # str(Version("0.0.1")) --> "0.0.1"
            str_ver_clean = str(ver_clean)
            assert str_ver_clean is not None and isinstance(str_ver_clean, str)
            write_version_files(
                str_ver_clean,
                path_root,
                str_write_to,
                version_file,
                is_only_not_exists=is_only_not_exists,
            )
