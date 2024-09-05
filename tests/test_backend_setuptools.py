"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

..

Unittest for module, drain_swamp.backend_setupttools

Unit test -- Module

.. code-block:: shell

   python -m coverage run --source='drain_swamp.backend_setuptools' -m pytest \
   --showlocals tests/test_backend_setuptools.py && coverage report \
   --data-file=.coverage --include="**/backend_setuptools.py"

Integration test

.. code-block:: shell

   make coverage
   pytest --showlocals --cov="drain_swamp" --cov-report=term-missing \
   --cov-config=pyproject.toml tests

"""

import logging
import logging.config
import sys
from contextlib import nullcontext as does_not_raise
from pathlib import Path

import pytest

from drain_swamp.backend_abc import (
    BackendType,
    get_optionals_pyproject_toml,
    get_required_pyproject_toml,
)
from drain_swamp.backend_setuptools import BackendSetupTools  # noqa: F401
from drain_swamp.constants import (
    LOGGING,
    g_app_name,
)
from drain_swamp.exceptions import (
    BackendNotSupportedError,
    MissingRequirementsFoldersFiles,
    PyProjectTOMLParseError,
)
from drain_swamp.parser_in import TomlParser

if sys.version_info >= (3, 9):  # pragma: no cover
    from collections.abc import (
        Generator,
        Sequence,
    )
else:  # pragma: no cover
    from typing import (
        Generator,
        Sequence,
    )

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
    inst_backend = BackendType.load_factory(path_f, parent_dir=tmp_path)

    assert inst_backend.path_config == path_f
    assert inst_backend.parent_dir != path_f
    assert issubclass(type(inst_backend), BackendType)
    assert backend_expected == inst_backend.backend

    # BackendType.parent_dir setter only accepts folder
    parent_dir_before = inst_backend.parent_dir
    assert parent_dir_before.exists() and parent_dir_before.is_dir()
    assert parent_dir_before == tmp_path
    #    not a folder. Coerses file --> folder
    inst_backend.parent_dir = tmp_path.joinpath(inst_backend.path_config.name)
    del inst_backend
    inst_backend = BackendType.load_factory(path_config, parent_dir=tmp_path)

    # BackendSetupTools.compose_dependencies_line
    suffixes = (
        ".lock",
        ".unlock",
    )
    for suffix in suffixes:
        gen_actual = inst_backend.compose_dependencies_line(suffix)
        assert isinstance(gen_actual, Generator)
        lst_required_line = list(gen_actual)
        if len(lst_required_line) == 0:
            # no required packages no dependencies .in file
            pass
        else:
            assert isinstance(lst_required_line[0], str)
            assert suffix in lst_required_line[0]

        logger.info(
            f"optionals: ({len(inst_backend.optionals)}): {inst_backend.optionals}"
        )

        gen_actual = inst_backend.compose_optional_lines(suffix)
        assert isinstance(gen_actual, Generator)
        optional_lines = list(gen_actual)
        set_lines = set(optional_lines)

        set_from_parts = set()
        for line in set_lines:
            set_from_parts.add(line)
        if len(lst_required_line) != 0:
            set_from_parts.add(lst_required_line[0])

        """raises MissingRequirementsFoldersFiles if both required or
        optionals are missing"""
        with expectation:
            str_lines_all = inst_backend.compose(suffix)
        if isinstance(expectation, does_not_raise):
            if len(str_lines_all) == 0:
                assert len(set_from_parts) == 0
            else:
                lines_all = str_lines_all.split("\n")
                set_from_all = set(lines_all)

                assert set_from_all == set_from_parts


testdata_load_factory_bad = (
    (
        Path(__file__).parent.joinpath("_bad_files", "backend_only.pyproject_toml"),
        pytest.raises(PyProjectTOMLParseError),
    ),
    (
        Path(__file__).parent.joinpath(
            "_good_files", "backend-unsupported.pyproject_toml"
        ),
        pytest.raises(BackendNotSupportedError),
    ),
)
ids_load_factory_bad = (
    "has malformed value without closing double quote",
    "unsupported or unknown backend",
)


@pytest.mark.parametrize(
    "path_config, expectation",
    testdata_load_factory_bad,
    ids=ids_load_factory_bad,
)
def test_load_factory_bad(
    path_config,
    expectation,
    tmp_path,
    prep_pyproject_toml,
):
    """BackendType.load_factory exceptions."""
    # pytest --showlocals --log-level INFO -k "test_load_factory_bad" tests
    # prepare
    prep_pyproject_toml(path_config, tmp_path)
    # act
    with expectation:
        BackendType.load_factory(path_config, parent_dir=tmp_path)
