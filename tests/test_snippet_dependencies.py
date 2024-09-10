"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

..

Unittest for module, drain_swamp.snippet_dependencies

Unit test -- Module

.. code-block:: shell

   python -m coverage run --source='drain_swamp.snippet_dependencies' -m pytest \
   --showlocals tests/test_snippet_dependencies.py && coverage report \
   --data-file=.coverage --include="**/snippet_dependencies.py"

Integration test

.. code-block:: shell

   make coverage
   pytest --showlocals --cov="drain_swamp" --cov-report=term-missing \
   --cov-config=pyproject.toml tests

"""

import logging
import logging.config
from collections.abc import (
    Generator,
    Sequence,
)
from contextlib import nullcontext as does_not_raise
from pathlib import Path

import pytest

from drain_swamp.backend_abc import (
    BackendType,
    get_optionals_pyproject_toml,
    get_required_pyproject_toml,
)
from drain_swamp.constants import (
    LOGGING,
    g_app_name,
)
from drain_swamp.exceptions import MissingRequirementsFoldersFiles
from drain_swamp.parser_in import TomlParser
from drain_swamp.snippet_dependencies import (
    SnippetDependencies,
    _fix_suffix,
)

testdata_fix_suffix = [
    ("md", ".md"),
    (".md", ".md"),
]
ids_fix_suffix = [
    "without prefix period",
    "with prefix period",
]


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


testdata_load_factory_good = (
    (
        Path(__file__).parent.joinpath("_good_files", "complete.pyproject_toml"),
        does_not_raise(),
        "setuptools",
    ),
    (
        Path(__file__).parent.joinpath("_good_files", "requires-none.pyproject_toml"),
        pytest.raises(MissingRequirementsFoldersFiles),
        "setuptools",
    ),
)
ids_load_factory_good = (
    "setuptools backend",
    "no package dependencies. Empty dict",
)


@pytest.mark.parametrize(
    "path_config, expectation, backend_expected",
    testdata_load_factory_good,
    ids=ids_load_factory_good,
)
def test_load_factory_good(
    path_config,
    expectation,
    backend_expected,
    tmp_path,
    caplog,
    has_logging_occurred,
    prepare_folders_files,
    prep_pyproject_toml,
):
    """BackendType factory works with supported build backends."""
    # pytest --showlocals --log-level INFO -k "test_load_factory_good" tests
    LOGGING["loggers"][g_app_name]["propagate"] = True
    logging.config.dictConfig(LOGGING)
    logger = logging.getLogger(name=g_app_name)
    logger.addHandler(hdlr=caplog.handler)
    caplog.handler.level = logger.level

    # prepare
    #    create folders and files
    tp = TomlParser(path_config)
    d_pyproject_toml = tp.d_pyproject_toml

    #    optionals
    d_optionals = dict()
    get_optionals_pyproject_toml(
        d_optionals,
        d_pyproject_toml,
        tmp_path,
        is_bypass=True,
    )
    seq_prepare_these = list(d_optionals.values())
    logger.info(f"prepare optionals: {seq_prepare_these}")
    prepare_folders_files(seq_prepare_these, tmp_path)

    #    required
    t_required = get_required_pyproject_toml(
        d_pyproject_toml,
        tmp_path,
        is_bypass=True,
    )
    msg_info = f"prepare required (t_required): {t_required}"
    logger.info(msg_info)
    if (
        t_required is not None
        and isinstance(t_required, Sequence)
        and len(t_required) == 2
    ):
        seq_prepare_these = (t_required[1],)
        logger.info(f"prepare required: {seq_prepare_these}")
        prepare_folders_files(seq_prepare_these, tmp_path)

    #    required
    t_required = BackendType.get_required(
        d_pyproject_toml,
        path_config,
        required=None,
    )

    lst_files = list(tmp_path.glob("**/*.in"))
    logger.info(f"lst_files: {lst_files}")

    assert has_logging_occurred(caplog)

    #    pyproject.toml
    path_f = prep_pyproject_toml(path_config, tmp_path)

    # Confirm backend name
    inst_backend = BackendType(path_f, parent_dir=tmp_path)

    assert inst_backend.path_config == path_f
    assert inst_backend.parent_dir != path_f

    # BackendType.parent_dir setter only accepts folder
    parent_dir_before = inst_backend.parent_dir
    assert parent_dir_before.exists() and parent_dir_before.is_dir()
    assert parent_dir_before == tmp_path
    #    not a folder. Coerses file --> folder
    inst_backend.parent_dir = tmp_path.joinpath(inst_backend.path_config.name)
    del inst_backend
    inst_backend = BackendType(path_config, parent_dir=tmp_path)

    suffixes = (
        ".lock",
        ".unlock",
    )
    for suffix in suffixes:
        gen_in_files = inst_backend.in_files()
        in_files = list(gen_in_files)
        in_files_count = len(in_files)

        gen_in_files = inst_backend.in_files()
        assert isinstance(gen_in_files, Generator)
        with expectation:
            str_lines_all = SnippetDependencies()(
                suffix,
                inst_backend.parent_dir,
                gen_in_files,
                inst_backend.required,
                inst_backend.optionals,
            )
        if isinstance(expectation, does_not_raise):
            # TOML format -- Even on Windows, line seperator must be "\n"
            lines = str_lines_all.split("\n")
            lines_count = len(lines)
            # Assumes there are no duplicate required or optionals
            assert in_files_count == lines_count

        # Empty required = None
        gen_in_files = inst_backend.in_files()
        assert isinstance(gen_in_files, Generator)
        with expectation:
            str_lines_all = SnippetDependencies()(
                suffix,
                inst_backend.parent_dir,
                gen_in_files,
                None,
                inst_backend.optionals,
            )
            # TOML format -- Even on Windows, line seperator must be "\n"
            lines = str_lines_all.split("\n")
            lines_count = len(lines)
            in_files_wo_required = in_files_count - 1
            assert in_files_wo_required == lines_count
