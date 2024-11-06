"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

..

Unittest for module, drain_swamp.snippet_dependencies

Unit test -- Module

.. code-block:: shell

   python -m coverage run --source='drain_swamp.snippet_dependencies' -m pytest \
   --showlocals tests/test_snippet_dependencies.py && coverage report \
   --data-file=.coverage --include="**/snippet_dependencies.py"

"""

import logging
import logging.config
import shutil
from contextlib import nullcontext as does_not_raise
from pathlib import Path
from typing import cast

import pytest

from drain_swamp._safe_path import resolve_joinpath
from drain_swamp.constants import (
    LOGGING,
    SUFFIX_IN,
    g_app_name,
)
from drain_swamp.exceptions import MissingRequirementsFoldersFiles
from drain_swamp.lock_util import replace_suffixes_last
from drain_swamp.snippet_dependencies import (
    _fix_suffix,
    generate_snippet,
    get_required_and_optionals,
)

testdata_fix_suffix = (
    ("md", ".md"),
    (".md", ".md"),
)
ids_fix_suffix = (
    "without prefix period",
    "with prefix period",
)


@pytest.mark.parametrize(
    "suffix, expected",
    testdata_fix_suffix,
    ids=ids_fix_suffix,
)
def test_fix_suffix(suffix, expected):
    """Does not barf given multiple suffixes e.g. .tar.gz"""
    # pytest --showlocals --log-level INFO -k "test_fix_suffix" tests
    actual = _fix_suffix(suffix)
    assert actual == expected


testdata_get_required_and_optionals = (
    (
        Path(__file__).parent.joinpath(
            "_bad_files", "keys-wrong-data-type.pyproject_toml"
        ),
        0,
        None,
        0,
    ),
)
ids_get_required_and_optionals = ("pipenv-unlock section unexpected field types",)


@pytest.mark.parametrize(
    "path_config, files_count_expected, required_expected, optionals_expected",
    testdata_get_required_and_optionals,
    ids=ids_get_required_and_optionals,
)
def test_get_required_and_optionals(
    path_config,
    files_count_expected,
    required_expected,
    optionals_expected,
    tmp_path,
    path_project_base,
    prep_pyproject_toml,
):
    """Test parsing pyproject.toml section tool.pipenv-unlock"""
    # pytest -vv --showlocals --log-level INFO -k "test_get_required_and_optionals" tests
    path_cwd = path_project_base()
    # prepare
    #    pyproject.toml
    path_f = prep_pyproject_toml(path_config, tmp_path)

    # act
    abspath_ins, t_required, lst_optionals = get_required_and_optionals(
        path_cwd,
        path_f,
    )
    assert len(abspath_ins) == files_count_expected
    assert t_required is required_expected
    assert len(lst_optionals) == optionals_expected


testdata_snippet_dependencies_create = (
    (
        Path(__file__).parent.joinpath("_req_files", "venvs_minimal.pyproject_toml"),
        ".tools",
        (
            "requirements/pins.shared",
            "docs/pip-tools",
            "requirements/pins-cffi.in",
            "requirements/tox.in",
        ),
        9,
        6,
        does_not_raise(),
    ),
    (
        Path(__file__).parent.joinpath("_good_files", "requires-none.pyproject_toml"),
        ".venv",
        (),
        0,
        0,
        does_not_raise(),
    ),
    (
        Path(__file__).parent.joinpath("_req_files", "venvs_minimal.pyproject_toml"),
        ".tools",
        (
            "requirements/pins.shared",
            "docs/pip-tools",
        ),
        9,
        6,
        pytest.raises(MissingRequirementsFoldersFiles),
    ),
)
ids_snippet_dependencies_create = (
    "setuptools backend",
    "no package dependencies",
    "missing a few requirements files",
)


@pytest.mark.parametrize(
    (
        "path_config, venv_path, seq_reqs_relpath, reqs_count_expected, "
        "line_count_expected, expectation"
    ),
    testdata_snippet_dependencies_create,
    ids=ids_snippet_dependencies_create,
)
def test_snippet_dependencies_create(
    path_config,
    venv_path,
    seq_reqs_relpath,
    reqs_count_expected,
    line_count_expected,
    expectation,
    tmp_path,
    caplog,
    has_logging_occurred,
    path_project_base,
    prepare_folders_files,
    prep_pyproject_toml,
):
    """Buils dependencies and optional dependencies snippet contents."""
    # pytest -vv --showlocals --log-level INFO -k "test_snippet_dependencies_create" tests
    LOGGING["loggers"][g_app_name]["propagate"] = True
    logging.config.dictConfig(LOGGING)
    logger = logging.getLogger(name=g_app_name)
    logger.addHandler(hdlr=caplog.handler)
    caplog.handler.level = logger.level

    path_cwd = path_project_base()

    # prepare
    #    pyproject.toml
    path_f = prep_pyproject_toml(path_config, tmp_path)

    #    copy reqs files
    #    TODO: Ensure folder has no missing requirement files
    for relpath in seq_reqs_relpath:
        abspath_src = cast("Path", resolve_joinpath(path_cwd, relpath))
        abspath_src_in = replace_suffixes_last(abspath_src, SUFFIX_IN)
        src_in_abspath = str(abspath_src_in)
        abspath_dest = cast("Path", resolve_joinpath(tmp_path, relpath))
        abspath_dest_in = replace_suffixes_last(abspath_dest, SUFFIX_IN)
        abspath_dest_in.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_in_abspath, abspath_dest_in)

    abspath_ins, t_required, d_optionals = get_required_and_optionals(tmp_path, path_f)

    #    copy ``.in`` files
    for abspath_dest_in in abspath_ins:
        relpath = abspath_dest_in.relative_to(tmp_path)
        abspath_src_in = cast("Path", resolve_joinpath(path_cwd, relpath))
        src_in_abspath = str(abspath_src_in)
        abspath_dest_in.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_in_abspath, abspath_dest_in)

    with expectation:
        # MissingRequirementsFoldersFiles --> halts creating snippet
        # ValueError, KeyError
        str_lines_all = generate_snippet(tmp_path, path_f)
    if isinstance(expectation, does_not_raise):
        # TOML format -- Even on Windows, line seperator must be "\n"
        if len(str_lines_all) != 0:
            lines = str_lines_all.split("\n")
        else:
            lines = []
        lines_count_actual = len(lines)
        assert lines_count_actual == line_count_expected
