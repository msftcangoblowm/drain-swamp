"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

..

Unittest for module, drain_swamp.lock_toggle

Without coverage

.. code-block:: shell

   pytest --showlocals --log-level INFO tests/test_lock_toggle.py

With coverage

.. code-block:: shell

   pytest --showlocals --cov="drain_swamp" --cov-report=term-missing tests/test_lock_toggle.py

"""

import logging
import logging.config
import pkgutil
from pathlib import Path
from unittest.mock import (
    Mock,
    patch,
)

import pytest

from drain_swamp.backend_abc import BackendType
from drain_swamp.backend_setuptools import BackendSetupTools  # noqa: F401
from drain_swamp.constants import (
    LOGGING,
    g_app_name,
)
from drain_swamp.lock_toggle import (
    lock_compile,
    unlock_create,
)

testdata_lock_compile = (
    (
        Path(__file__).parent.joinpath("_good_files", "complete.pyproject_toml"),
        (
            "requirements/prod.in",
            "requirements/pip.in",
            "requirements/pip-tools.in",
            "requirements/dev.in",
            "requirements/manage.in",
            "docs/requirements.in",
        ),
        (),
    ),
    (
        Path(__file__).parent.joinpath("_good_files", "complete.pyproject_toml"),
        (
            "requirements/prod.in",
            "requirements/pip.in",
            "requirements/pip-tools.in",
            "requirements/dev.in",
            "requirements/manage.in",
            "docs/requirements.in",
            "ci/tox.in",
        ),
        (Path("ci"),),
    ),
)
ids_lock_compile = (
    "Without extra folders",
    "With additional folder, ci",
)


@pytest.mark.skipif(
    pkgutil.find_loader("piptools") is None,
    reason="uses pip-compile part of pip-tools",
)
@pytest.mark.parametrize(
    "path_config, seq_create_these, additional_folders",
    testdata_lock_compile,
    ids=ids_lock_compile,
)
def test_lock_compile(
    path_config,
    seq_create_these,
    additional_folders,
    tmp_path,
    prepare_folders_files,
    caplog,
    has_logging_occurred,
):
    # pytest --showlocals --log-level INFO -k "test_lock_compile" tests
    LOGGING["loggers"][g_app_name]["propagate"] = True
    logging.config.dictConfig(LOGGING)
    logger = logging.getLogger(name=g_app_name)
    logger.addHandler(hdlr=caplog.handler)
    caplog.handler.level = logger.level

    # prepare (required and optionals .in files)
    prepare_folders_files(seq_create_these, tmp_path)

    inst = BackendType.load_factory(
        path_config,
        parent_dir=tmp_path,
        additional_folders=additional_folders,
    )

    expected = list(inst.in_files())
    expected_count = len(expected)

    # dry run. Thank you /bin/true
    with (patch(f"{g_app_name}.lock_toggle.PATH_PIP_COMPILE", Path("/bin/true")),):
        gen_lock_files = lock_compile(inst)
        actual_count = len(list(gen_lock_files))
        assert actual_count == 0

    # for realz
    gen_lock_files = lock_compile(inst)
    actual_count = len(list(gen_lock_files))
    assert has_logging_occurred(caplog)
    assert expected_count == actual_count


@pytest.mark.parametrize(
    "path_config, seq_create_these, additional_folders",
    testdata_lock_compile,
    ids=ids_lock_compile,
)
def test_unlock_create(
    path_config,
    seq_create_these,
    additional_folders,
    tmp_path,
    prepare_folders_files,
):
    """Currently a placeholder; does nothing (atm)"""
    # pytest --showlocals --log-level INFO -k "test_unlock_create" tests

    # prepare (required and optionals .in files)
    prepare_folders_files(seq_create_these, tmp_path)

    inst = BackendType.load_factory(
        path_config,
        parent_dir=tmp_path,
        additional_folders=additional_folders,
    )

    """
    expected = list(inst.in_files())
    expected_count = len(expected)
    """
    pass

    mock = Mock(wraps=unlock_create)
    mock(inst)
    mock.assert_called()
