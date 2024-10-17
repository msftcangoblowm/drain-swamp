"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

..

Unittest for entrypoint, cli_unlock

.. code-block:: shell

   python -m coverage run --source='drain_swamp.cli_unlock' -m pytest \
   --showlocals tests/test_cli_unlock.py && coverage report \
   --data-file=.coverage --include="**/cli_unlock.py"

Integration test

.. code-block:: shell

   make coverage
   pytest --showlocals --cov="drain_swamp" --cov-report=term-missing \
   --cov-config=pyproject.toml tests

.. seealso::

   https://github.com/pytest-dev/pytest-cov/issues/373#issuecomment-1472861775

"""

import logging
import logging.config
import traceback
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from drain_swamp.backend_abc import BackendType
from drain_swamp.cli_unlock import (
    dependencies_lock,
    dependencies_unlock,
    entrypoint_name,
    main,
)
from drain_swamp.constants import (
    LOGGING,
    g_app_name,
)
from drain_swamp.parser_in import TomlParser


def test_cli_main():
    """Minimally test package version is printed."""
    runner = CliRunner()
    # --version
    """
    cmd = ["--version"]
    result = runner.invoke(main, cmd)
    assert result.exit_code == 0
    assert "version" in result.stdout
    """

    # --help
    cmd = ["--help"]
    result = runner.invoke(main, cmd)
    assert result.exit_code == 0
    assert f"Command-line for {entrypoint_name}. Prints usage" in result.stdout


testdata_lock_unlock_successfully = (
    (
        Path(__file__).parent.joinpath("_good_files", "complete.pyproject_toml"),
        "little_shop_of_horrors_shrine_candles",
        (Path("ci"),),
        {"ci": Path("ci/kit.in")},
        True,
    ),
)
ids_lock_unlock_successfully = ("With optional ci/kit.in and additional folder ci",)


@pytest.mark.parametrize(
    "path_pyproject_toml, id_, additional_folders, additional_files, is_locked",
    testdata_lock_unlock_successfully,
    ids=ids_lock_unlock_successfully,
)
def test_lock_unlock_successfully(
    path_pyproject_toml,
    id_,
    additional_folders,
    additional_files,
    is_locked,
    tmp_path,
    caplog,
    has_logging_occurred,
    prep_pyproject_toml,
    prep_cmd_unlock_lock,
    prepare_files_empties,
):
    """Test dependency lock and unlock."""
    # pytest --showlocals --log-level INFO -k "test_lock_unlock_successfully" -v tests
    LOGGING["loggers"][g_app_name]["propagate"] = True
    logging.config.dictConfig(LOGGING)
    logger = logging.getLogger(name=g_app_name)
    logger.addHandler(hdlr=caplog.handler)
    caplog.handler.level = logger.level

    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path) as tmp_dir_path:
        path_tmp_dir = Path(tmp_dir_path)
        # prepare
        #    pyproject.toml
        path_f = prep_pyproject_toml(path_pyproject_toml, path_tmp_dir)
        tp = TomlParser(path_f)
        d_pyproject_toml = tp.d_pyproject_toml

        #    empty files
        prepare_files_empties(
            d_pyproject_toml,
            path_tmp_dir,
            d_add_files=additional_files,
        )
        #    unlock/lock command
        cmd = prep_cmd_unlock_lock(
            path_tmp_dir,
            # snip_co=id_,
            add_folders=additional_folders,
        )
        #    get dependency lock state
        # is_locked = BackendType.is_locked(path_f)
        #    read pyproject.toml contents
        expected = path_f.read_text()

        logger.info(f"cmd (before): {cmd}")
        # logger.info(f"lock state (True is locked): {is_locked}")
        logger.info(f"pyproject.toml (before): {expected}")

        # act
        if is_locked:
            result = runner.invoke(dependencies_unlock, cmd)
            assert result.exit_code == 0
            actual = path_f.read_text()
            logger.info(f"pyproject.toml (after unlock): {actual}")

            result = runner.invoke(dependencies_lock, cmd)
            actual = path_f.read_text()
            logger.info(f"pyproject.toml (after lock): {actual}")
            assert result.exit_code == 0
        else:
            result = runner.invoke(dependencies_lock, cmd)
            assert result.exit_code == 0
            result = runner.invoke(dependencies_unlock, cmd)
            assert result.exit_code == 0
            actual = path_f.read_text()

        assert has_logging_occurred(caplog)
        assert expected == actual


testdata_lock_unlock_and_back_wo_prepare = (
    (
        dependencies_unlock,
        Path(__file__).parent.joinpath("_good_files", "complete.pyproject_toml"),
        "little_shop_of_horrors_shrine_candles",
        (Path("ci"),),
        {"ci": Path("ci/kit.in")},
        3,  # PyProjectTOMLReadError
    ),
    (
        dependencies_lock,
        Path(__file__).parent.joinpath("_good_files", "complete.pyproject_toml"),
        "little_shop_of_horrors_shrine_candles",
        (Path("ci"),),
        {"ci": Path("ci/kit.in")},
        3,  # PyProjectTOMLReadError
    ),
)
ids_lock_unlock_and_back_wo_prepare = (
    "call dependencies_unlock. Additional file ci/kit.in",
    "call dependencies_lock. Additional file ci/kit.in",
)


@pytest.mark.parametrize(
    "func, path_pyproject_toml, id_, additional_folders, additional_files, expected_exit_code",
    testdata_lock_unlock_and_back_wo_prepare,
    ids=ids_lock_unlock_and_back_wo_prepare,
)
def test_lock_unlock_and_back_wo_prepare(
    func,
    path_pyproject_toml,
    id_,
    additional_folders,
    additional_files,
    expected_exit_code,
    tmp_path,
    prep_pyproject_toml,
    prep_cmd_unlock_lock,
    prepare_files_empties,
    caplog,
    has_logging_occurred,
):
    """Test dependency lock and unlock without prepare."""
    # pytest --showlocals --log-level INFO -k "test_lock_unlock_and_back_wo_prepare" -v tests
    LOGGING["loggers"][g_app_name]["propagate"] = True
    logging.config.dictConfig(LOGGING)
    logger = logging.getLogger(name=g_app_name)
    logger.addHandler(hdlr=caplog.handler)
    caplog.handler.level = logger.level

    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path) as tmp_dir_path:
        path_tmp_dir = Path(tmp_dir_path)
        # path_f = prep_pyproject_toml(path_pyproject_toml, path_tmp_dir)
        cmd = prep_cmd_unlock_lock(
            path_tmp_dir,
            add_folders=additional_folders,
            # snip_co=id_,
        )
        # Call cli func blind; no BackendType.is_locked
        result = runner.invoke(func, cmd)

        logger.info(result.output)
        tb = result.exc_info[2]
        # msg_info = f"traceback: {pprint(traceback.format_tb(tb))}"
        msg_info = f"traceback: {traceback.format_tb(tb)}"
        logger.info(msg_info)

        actual_exit_code = result.exit_code
        assert actual_exit_code == expected_exit_code


testdata_lock_unlock_and_back_with_prepare = (
    (
        dependencies_lock,
        Path(__file__).parent.joinpath("_good_files", "complete.pyproject_toml"),
        "little_shop_of_horrors_shrine_candles",
        (Path("ci"),),
        {"ci": Path("ci/kit.in")},
        True,
        False,
        0,  # 6 --> 0 MissingRequirementsFoldersFiles
    ),
    (
        dependencies_unlock,
        Path(__file__).parent.joinpath("_good_files", "complete.pyproject_toml"),
        "little_shop_of_horrors_shrine_candles",
        (Path("ci"),),
        {"ci": Path("ci/kit.in")},
        True,
        False,
        0,  # 6 --> 0 MissingRequirementsFoldersFiles
    ),
    (
        dependencies_lock,
        Path(__file__).parent.joinpath("_bad_files", "snippet-nested.pyproject_toml"),
        "little_shop_of_horrors_shrine_candles",
        (Path("ci"),),
        {"ci": Path("ci/kit.in")},
        True,
        True,
        0,  # 8 --> 0
    ),
    (
        dependencies_unlock,
        Path(__file__).parent.joinpath("_bad_files", "snippet-nested.pyproject_toml"),
        "little_shop_of_horrors_shrine_candles",
        (Path("ci"),),
        {"ci": Path("ci/kit.in")},
        True,
        True,
        0,  # 8 --> 0
    ),
    (
        dependencies_lock,
        Path(__file__).parent.joinpath("_good_files", "complete.pyproject_toml"),
        "little_shop_of_horrors_obedient_girl_friend",
        (Path("ci"),),
        {"ci": Path("ci/kit.in")},
        True,
        True,
        0,  # 9 --> 0
    ),
    (
        dependencies_unlock,
        Path(__file__).parent.joinpath("_good_files", "complete.pyproject_toml"),
        "little_shop_of_horrors_obedient_girl_friend",
        (Path("ci"),),
        {"ci": Path("ci/kit.in")},
        True,
        True,
        0,  # 9 --> 0
    ),
)
ids_lock_unlock_and_back_with_prepare = (
    "lock missing folders and files",
    "unlock missing folders and files",
    "lock Snippet is invalid",
    "unlock Snippet is invalid",
    "lock Snippet no match",
    "unlock Snippet no match",
)


@pytest.mark.parametrize(
    "func, path_pyproject_toml, id_, additional_folders, additional_files, is_prep_pyproject_toml, is_prep_files, expected_exit_code",
    testdata_lock_unlock_and_back_with_prepare,
    ids=ids_lock_unlock_and_back_with_prepare,
)
def test_lock_unlock_and_back_with_prepare(
    func,
    path_pyproject_toml,
    id_,
    additional_folders,
    additional_files,
    is_prep_pyproject_toml,
    is_prep_files,
    expected_exit_code,
    tmp_path,
    caplog,
    has_logging_occurred,
    prep_pyproject_toml,
    prep_cmd_unlock_lock,
    prepare_files_empties,
):
    """Test dependency lock and unlock with prepare."""
    # pytest --showlocals --log-level INFO -k "test_lock_unlock_and_back_with_prepare" -v tests
    LOGGING["loggers"][g_app_name]["propagate"] = True
    logging.config.dictConfig(LOGGING)
    logger = logging.getLogger(name=g_app_name)
    logger.addHandler(hdlr=caplog.handler)
    caplog.handler.level = logger.level

    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path) as tmp_dir_path:
        path_tmp_dir = Path(tmp_dir_path)
        if is_prep_pyproject_toml:
            path_f = prep_pyproject_toml(path_pyproject_toml, path_tmp_dir)
            tp = TomlParser(path_f)
            d_pyproject_toml = tp.d_pyproject_toml
            if is_prep_files:
                prepare_files_empties(
                    d_pyproject_toml,
                    path_tmp_dir,
                    d_add_files=additional_files,
                )

        cmd = prep_cmd_unlock_lock(
            path_tmp_dir,
            # snip_co=id_,
            add_folders=additional_folders,
        )

        # Call cli func blind; no BackendType.is_locked
        result = runner.invoke(func, cmd)

        logger.info(f"exit_code: {result.exit_code}")
        logger.info(f"exception: {result.exception}")
        logger.info(f"output: {result.output}")

        tb = result.exc_info[2]
        # msg_info = f"traceback: {pprint(traceback.format_tb(tb))}"
        msg_info = f"traceback: {traceback.format_tb(tb)}"
        logger.info(msg_info)

        actual_exit_code = result.exit_code
        assert actual_exit_code == expected_exit_code


testdata_lock_unlock_and_back_with_patch = (
    (
        dependencies_lock,
        Path(__file__).parent.joinpath("_good_files", "complete.pyproject_toml"),
        "little_shop_of_horrors_shrine_candles",
        (Path("ci"),),
        {"ci": Path("ci/kit.in")},
        True,
        True,
        7,  # BackendNotSupportedError
    ),
)
ids_lock_unlock_and_back_with_patch = (
    "pip-tools not installed. pip-compile command unavailable",
)


@pytest.mark.parametrize(
    "func, path_pyproject_toml, id_, additional_folders, additional_files, is_prep_pyproject_toml, is_prep_files, expected_exit_code",
    testdata_lock_unlock_and_back_with_patch,
    ids=ids_lock_unlock_and_back_with_patch,
)
def test_lock_unlock_and_back_with_patch(
    func,
    path_pyproject_toml,
    id_,
    additional_folders,
    additional_files,
    is_prep_pyproject_toml,
    is_prep_files,
    expected_exit_code,
    tmp_path,
    caplog,
    has_logging_occurred,
    prep_pyproject_toml,
    prep_cmd_unlock_lock,
    prepare_files_empties,
):
    """Test dependency lock and unlock with patch."""
    # pytest --showlocals --log-level INFO -k "test_lock_unlock_and_back_with_patch" -v tests
    LOGGING["loggers"][g_app_name]["propagate"] = True
    logging.config.dictConfig(LOGGING)
    logger = logging.getLogger(name=g_app_name)
    logger.addHandler(hdlr=caplog.handler)
    caplog.handler.level = logger.level

    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as tmp_dir_path:
        path_tmp_dir = Path(tmp_dir_path)
        if is_prep_pyproject_toml:
            path_f = prep_pyproject_toml(path_pyproject_toml, path_tmp_dir)
            tp = TomlParser(path_f)
            d_pyproject_toml = tp.d_pyproject_toml
            if is_prep_files:
                prepare_files_empties(
                    d_pyproject_toml,
                    path_tmp_dir,
                    d_add_files=additional_files,
                )

        cmd = prep_cmd_unlock_lock(
            path_tmp_dir,
            # snip_co=id_,
            add_folders=additional_folders,
        )

        # Call cli func blind; no BackendType.is_locked
        with patch(
            f"{g_app_name}.lock_toggle.is_package_installed", return_value=False
        ):
            result = runner.invoke(func, cmd)

        logger.info(result.output)
        tb = result.exc_info[2]
        # msg_info = f"traceback: {pprint(traceback.format_tb(tb))}"
        msg_info = f"traceback: {traceback.format_tb(tb)}"
        logger.info(msg_info)

        actual_exit_code = result.exit_code
        assert actual_exit_code == expected_exit_code


testdata_lock_unlock_and_back_card_monte = (
    (
        dependencies_lock,
        Path(__file__).parent.joinpath("_good_files", "complete.pyproject_toml"),
        Path(__file__).parent.joinpath("_bad_files", "backend_only.pyproject_toml"),
        "little_shop_of_horrors_shrine_candles",
        (Path("ci"),),
        {"ci": Path("ci/kit.in")},
        True,
        True,
        4,  # PyProjectTOMLParseError
    ),
    (
        dependencies_unlock,
        Path(__file__).parent.joinpath("_good_files", "complete.pyproject_toml"),
        Path(__file__).parent.joinpath("_bad_files", "backend_only.pyproject_toml"),
        "little_shop_of_horrors_shrine_candles",
        (Path("ci"),),
        {"ci": Path("ci/kit.in")},
        True,
        True,
        4,  # PyProjectTOMLParseError
    ),
)
ids_lock_unlock_and_back_card_monte = (
    "lock. Cause parsing to fail, but not during prep",
    "unlock. Cause parsing to fail, but not during prep",
)


@pytest.mark.parametrize(
    "func, path_pyproject_toml_prep, path_pyproject_toml_test, id_, additional_folders, additional_files, is_prep_pyproject_toml, is_prep_files, expected_exit_code",
    testdata_lock_unlock_and_back_card_monte,
    ids=ids_lock_unlock_and_back_card_monte,
)
def test_lock_unlock_and_back_card_monte(
    func,
    path_pyproject_toml_prep,
    path_pyproject_toml_test,
    id_,
    additional_folders,
    additional_files,
    is_prep_pyproject_toml,
    is_prep_files,
    expected_exit_code,
    tmp_path,
    caplog,
    has_logging_occurred,
    prep_pyproject_toml,
    prep_cmd_unlock_lock,
    prepare_files_empties,
):
    """Would like to cause PyProjectTOMLParseError; exit code 4. But it's
    a catch 22. To prepare the files, need a viable pyproject.toml. To
    trigger the exception need a non-viable pyproject.toml

    So we are gonna play a magic trick. Here you see it; now you don't.
    """
    # pytest --showlocals --log-level INFO -k "test_lock_unlock_and_back_card_monte" -v tests
    LOGGING["loggers"][g_app_name]["propagate"] = True
    logging.config.dictConfig(LOGGING)
    logger = logging.getLogger(name=g_app_name)
    logger.addHandler(hdlr=caplog.handler)
    caplog.handler.level = logger.level

    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as tmp_dir_path:
        # prepare -- use viable pyproject.toml
        path_tmp_dir = Path(tmp_dir_path)
        if is_prep_pyproject_toml:
            path_f_prep = prep_pyproject_toml(path_pyproject_toml_prep, path_tmp_dir)
            tp = TomlParser(path_f_prep)
            d_pyproject_toml = tp.d_pyproject_toml
            if is_prep_files:
                prepare_files_empties(
                    d_pyproject_toml,
                    path_tmp_dir,
                    d_add_files=additional_files,
                )
            prep_pyproject_toml(path_pyproject_toml_test, path_tmp_dir)

        cmd = prep_cmd_unlock_lock(
            path_tmp_dir,
            # snip_co=id_,
            add_folders=additional_folders,
        )

        result = runner.invoke(func, cmd)

        logger.info(result.output)
        tb = result.exc_info[2]
        # msg_info = f"traceback: {pprint(traceback.format_tb(tb))}"
        msg_info = f"traceback: {traceback.format_tb(tb)}"
        logger.info(msg_info)

        actual_exit_code = result.exit_code
        assert actual_exit_code == expected_exit_code


testdata_lock_unlock_and_back_optionals = (
    (
        dependencies_lock,
        Path(__file__).parent.joinpath("_good_files", "complete.pyproject_toml"),
        "little_shop_of_horrors_shrine_candles",
        (Path("ci"),),
        {"ci": Path("ci/kit.in")},
        {
            "web": Path("ci/web.in"),
            "pytest": Path("ci/pytest.in"),
        },
        9,
    ),
    (
        dependencies_unlock,
        Path(__file__).parent.joinpath("_good_files", "complete.pyproject_toml"),
        "little_shop_of_horrors_shrine_candles",
        ("ci",),
        {"ci": Path("ci/kit.in")},
        {
            "web": Path("ci/web.in"),
            "pytest": Path("ci/pytest.in"),
        },
        9,
    ),
)
ids_lock_unlock_and_back_optionals = (
    "lock create two optionals",
    "unlock create two optionals ",
)


@pytest.mark.parametrize(
    "func, path_pyproject_toml, id_, additional_folders, additional_files, d_optionals, expected_count",
    testdata_lock_unlock_and_back_optionals,
    ids=ids_lock_unlock_and_back_optionals,
)
def test_lock_unlock_and_back_optionals(
    func,
    path_pyproject_toml,
    id_,
    additional_folders,
    additional_files,
    d_optionals,
    expected_count,
    tmp_path,
    caplog,
    has_logging_occurred,
    prep_pyproject_toml,
    prep_cmd_unlock_lock,
    prepare_files_empties,
):
    """Test dependency lock and unlock. Optionals."""
    # pytest --showlocals --log-level INFO -k "test_lock_unlock_and_back_optionals" -v tests
    LOGGING["loggers"][g_app_name]["propagate"] = True
    logging.config.dictConfig(LOGGING)
    logger = logging.getLogger(name=g_app_name)
    logger.addHandler(hdlr=caplog.handler)
    caplog.handler.level = logger.level

    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as tmp_dir_path:
        path_tmp_dir = Path(tmp_dir_path)
        path_f = prep_pyproject_toml(path_pyproject_toml, path_tmp_dir)
        tp = TomlParser(path_f)
        d_pyproject_toml = tp.d_pyproject_toml
        prepare_files_empties(
            d_pyproject_toml,
            path_tmp_dir,
            d_add_files=additional_files,
            d_optionals=d_optionals,
        )

        cmd = prep_cmd_unlock_lock(
            path_tmp_dir,
            d_opts=d_optionals,
            add_folders=additional_folders,
            # snip_co=id_,
        )

        result = runner.invoke(func, cmd)
        # logger.info(f"exception: {result.exception}")
        # logger.info(f"output: {result.output}")
        assert result.exit_code == 0

        inst = BackendType(
            path_tmp_dir,
            optionals=d_optionals,
            additional_folders=additional_folders,
        )
        gen = inst.in_files()
        files = list(gen)
        actual_count = len(files)

        assert has_logging_occurred(caplog)

        assert actual_count == expected_count
