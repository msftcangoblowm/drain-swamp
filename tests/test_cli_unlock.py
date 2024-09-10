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

from drain_swamp._safe_path import is_win
from drain_swamp.backend_abc import BackendType
from drain_swamp.cli_unlock import (
    create_links,
    dependencies_lock,
    dependencies_unlock,
    entrypoint_name,
    main,
    state_is_lock,
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
    ),
)
ids_lock_unlock_successfully = ("With optional ci/kit.in and additional folder ci",)


@pytest.mark.parametrize(
    "path_pyproject_toml, id_, additional_folders, additional_files",
    testdata_lock_unlock_successfully,
    ids=ids_lock_unlock_successfully,
)
def test_lock_unlock_successfully(
    path_pyproject_toml,
    id_,
    additional_folders,
    additional_files,
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
            snip_co=id_,
            add_folders=additional_folders,
        )
        #    get dependency lock state
        is_locked = BackendType.is_locked(path_f)
        #    read pyproject.toml contents
        expected = path_f.read_text()

        logger.info(f"cmd (before): {cmd}")
        logger.info(f"lock state (True is locked): {is_locked}")
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
            snip_co=id_,
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
        6,  # MissingRequirementsFoldersFiles
    ),
    (
        dependencies_unlock,
        Path(__file__).parent.joinpath("_good_files", "complete.pyproject_toml"),
        "little_shop_of_horrors_shrine_candles",
        (Path("ci"),),
        {"ci": Path("ci/kit.in")},
        True,
        False,
        6,  # MissingRequirementsFoldersFiles
    ),
    (
        dependencies_lock,
        Path(__file__).parent.joinpath("_bad_files", "snippet-nested.pyproject_toml"),
        "little_shop_of_horrors_shrine_candles",
        (Path("ci"),),
        {"ci": Path("ci/kit.in")},
        True,
        True,
        8,
    ),
    (
        dependencies_unlock,
        Path(__file__).parent.joinpath("_bad_files", "snippet-nested.pyproject_toml"),
        "little_shop_of_horrors_shrine_candles",
        (Path("ci"),),
        {"ci": Path("ci/kit.in")},
        True,
        True,
        8,
    ),
    (
        dependencies_lock,
        Path(__file__).parent.joinpath("_good_files", "complete.pyproject_toml"),
        "little_shop_of_horrors_obedient_girl_friend",
        (Path("ci"),),
        {"ci": Path("ci/kit.in")},
        True,
        True,
        9,
    ),
    (
        dependencies_unlock,
        Path(__file__).parent.joinpath("_good_files", "complete.pyproject_toml"),
        "little_shop_of_horrors_obedient_girl_friend",
        (Path("ci"),),
        {"ci": Path("ci/kit.in")},
        True,
        True,
        9,
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
            snip_co=id_,
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
            snip_co=id_,
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
            snip_co=id_,
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
            snip_co=id_,
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


testdata_is_lock = (
    (
        Path(__file__).parent.joinpath("_good_files", "complete.pyproject_toml"),
        0,
    ),
    (
        Path(__file__).parent.joinpath(
            "_good_files", "complete-manage-pip-prod-unlock.pyproject_toml"
        ),
        1,
    ),
    (
        Path(__file__).parent.joinpath(
            "_bad_files", "static_dependencies.pyproject_toml"
        ),
        4,
    ),
    (
        Path(__file__).parent.joinpath("_changelog_files", "CHANGES-empty.rst"),
        3,
    ),
)
ids_is_lock = (
    "locked",
    "unlocked",
    "static dependencies. No tool.setuptools.dynamic section",
    "not a toml file",
)


@pytest.mark.parametrize(
    "path_pyproject_toml, expected_exit_code",
    testdata_is_lock,
    ids=ids_is_lock,
)
def test_state_is_lock(
    path_pyproject_toml,
    expected_exit_code,
    tmp_path,
    prep_pyproject_toml,
    caplog,
    has_logging_occurred,
):
    """Test state is_lock."""
    # pytest --showlocals --log-level INFO -k "test_state_is_lock" tests
    LOGGING["loggers"][g_app_name]["propagate"] = True
    logging.config.dictConfig(LOGGING)
    logger = logging.getLogger(name=g_app_name)
    logger.addHandler(hdlr=caplog.handler)
    caplog.handler.level = logger.level

    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as tmp_dir_path:
        path_tmp_dir = Path(tmp_dir_path)
        path_f = prep_pyproject_toml(path_pyproject_toml, path_tmp_dir)
        # click chokes! Attempts to Path.resolve a float
        invalids = (1.2345,)
        for invalid in invalids:
            cmd = [
                "--path",
                invalid,
            ]
            result = runner.invoke(state_is_lock, cmd)
            assert result.exception.__class__ == TypeError
            # logger.info(f"result.output: {result.output}")
            # logger.info(f"result.exit_code: {result.exit_code}")
            # tb = result.exc_info[2]
            # logger.info(f"traceback: {traceback.format_tb(tb)}")
            pass

        relpath_f = path_f.relative_to(path_tmp_dir)

        cmds = [
            ("--path", str(relpath_f)),  # relative path
            (
                "--path",
                path_f,
            ),  # absolute path
            (
                "--path",
                "",
            ),  # --> default path
        ]

        for func_cmd in cmds:
            result = runner.invoke(state_is_lock, func_cmd)
            logger.info(f"result.exception: {result.exception}")
            logger.info(f"result.output: {result.output}")
            assert result.exit_code == expected_exit_code

        # assert has_logging_occurred(caplog)
        pass


def test_create_links_exceptions(
    caplog, tmp_path, prep_pyproject_toml, has_logging_occurred, prepare_folders_files
):
    """Test create symlinks exceptions."""
    # pytest --showlocals --log-level INFO -k "test_create_links_exceptions" tests
    LOGGING["loggers"][g_app_name]["propagate"] = True
    logging.config.dictConfig(LOGGING)
    logger = logging.getLogger(name=g_app_name)
    logger.addHandler(hdlr=caplog.handler)
    caplog.handler.level = logger.level

    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as tmp_dir_path:
        path_tmp_dir = Path(tmp_dir_path)
        # PyProjectTOMLReadError (3) -- note BackendType call is wrong
        func_cmd = [
            "--path",
            tmp_dir_path,
        ]
        result = runner.invoke(create_links, func_cmd)
        exit_code_actual = result.exit_code
        assert exit_code_actual == 3

        # malformed toml / backend only --> PyProjectTOMLParseError
        path_pyproject_toml_4 = Path(__file__).parent.joinpath(
            "_bad_files", "backend_only.pyproject_toml"
        )
        expected = 4
        path_f = prep_pyproject_toml(path_pyproject_toml_4, path_tmp_dir)
        result = runner.invoke(create_links, func_cmd)
        exit_code_actual = result.exit_code
        assert exit_code_actual == expected

        # Path is expected to be a folder, not a file (2)
        path_pyproject_toml_7 = Path(__file__).parent.joinpath(
            "_bad_files", "static_dependencies.pyproject_toml"
        )
        expected = 2
        #    prepare
        path_f = prep_pyproject_toml(path_pyproject_toml_7, path_tmp_dir)
        func_cmd = [
            "--path",
            str(path_f),
        ]
        inst = BackendType(
            path_f,
            parent_dir=tmp_dir_path,
        )
        assert inst.parent_dir == path_tmp_dir
        with patch(
            f"{g_app_name}.cli_unlock.BackendType",
            return_value=inst,
        ):
            result = runner.invoke(create_links, func_cmd)
            exit_code_actual = result.exit_code
            assert exit_code_actual == expected

        """static dependencies (7)

        - No dynamic section in pyproject.toml
        - no ``dependencies`` key

        unlocked == "0" locked == "1". None use current lock state
        """
        expected = 7
        func_cmd = [
            "--path",
            tmp_dir_path,
        ]
        with patch(
            f"{g_app_name}.cli_unlock.BackendType",
            return_value=inst,
        ):
            result = runner.invoke(create_links, func_cmd)
            exit_code_actual = result.exit_code
            assert exit_code_actual == expected

            """
            logger.info(f"result.output: {result.output}")
            logger.info(f"result.exit_code: {result.exit_code}")
            logger.info(f"result.exception: {result.exception}")
            tb = result.exc_info[2]
            logger.info(f"traceback: {traceback.format_tb(tb)}")
            assert has_logging_occurred(caplog)


            assert result.stdout.rstrip() == expected_text

            expected_text = "In pyproject.toml no section, tool.setuptools.dynamic"
            """
            pass


testdata_create_links_set_lock = (
    (
        Path(__file__).parent.joinpath(
            "_good_files", "complete-manage-pip-prod-unlock.pyproject_toml"
        ),
        (
            "requirements/prod.in",
            "requirements/pip.in",
            "requirements/manage.in",
        ),
        (
            "requirements/prod.unlock",
            "requirements/pip.unlock",
            "requirements/manage.unlock",
        ),
        (
            "requirements/prod.lock",
            "requirements/pip.lock",
            "requirements/manage.lock",
        ),
        "1",
        None,
        0,
    ),
    (
        Path(__file__).parent.joinpath(
            "_good_files", "complete-manage-pip-prod-unlock.pyproject_toml"
        ),
        (
            "requirements/prod.in",
            "requirements/pip.in",
            "requirements/manage.in",
        ),
        (
            "requirements/prod.unlock",
            "requirements/pip.unlock",
            "requirements/manage.unlock",
        ),
        (
            "requirements/prod.lock",
            "requirements/pip.lock",
            "requirements/manage.lock",
        ),
        "0",
        None,
        0,
    ),
    (
        Path(__file__).parent.joinpath(
            "_good_files", "complete-manage-pip-prod-unlock.pyproject_toml"
        ),
        (
            "requirements/prod.in",
            "requirements/pip.in",
            "requirements/manage.in",
        ),
        (
            "requirements/prod.unlock",
            "requirements/pip.unlock",
            "requirements/manage.unlock",
        ),
        (
            "requirements/prod.lock",
            "requirements/pip.lock",
            "requirements/manage.lock",
        ),
        None,
        None,
        0,
    ),
    (
        Path(__file__).parent.joinpath(
            "_good_files", "complete-manage-pip-prod-unlock.pyproject_toml"
        ),
        (
            "requirements/prod.in",
            "requirements/pip.in",
            "requirements/manage.in",
        ),
        (
            "requirements/prod.unlock",
            "requirements/pip.unlock",
            "requirements/manage.unlock",
        ),
        (
            "requirements/prod.lock",
            "requirements/pip.lock",
            "requirements/manage.lock",
        ),
        None,
        "nonexistent_snippet",
        9,
    ),
    (
        Path(__file__).parent.joinpath("_bad_files", "snippet-nested.pyproject_toml"),
        (
            "requirements/prod.in",
            "requirements/pip.in",
            "requirements/manage.in",
            "requirements/pip-tools.in",
            "requirements/dev.in",
            "requirements/manage.in",
            "docs/requirements.in",
        ),
        (
            "requirements/prod.unlock",
            "requirements/pip.unlock",
            "requirements/manage.unlock",
            "requirements/pip-tools.unlock",
            "requirements/dev.unlock",
            "requirements/manage.unlock",
            "docs/requirements.unlock",
        ),
        (
            "requirements/prod.lock",
            "requirements/pip.lock",
            "requirements/manage.lock",
            "requirements/pip-tools.lock",
            "requirements/dev.lock",
            "requirements/manage.lock",
            "docs/requirements.lock",
        ),
        None,
        None,
        8,
    ),
)
ids_create_links_set_lock = (
    "set symlink to dependency locked",
    "set symlink to dependency unlocked",
    "set symlink to current lock state",
    "dependencies ok. snippet_co no match. Cannot update snippet",
    "dependencies ok. snippet malformed. Cannot update snippet",
)


@pytest.mark.parametrize(
    "path_pyproject_toml, seq_in, seq_unlock, seq_lock, set_lock, snippet_co, expected",
    testdata_create_links_set_lock,
    ids=ids_create_links_set_lock,
)
def test_create_links_set_lock(
    path_pyproject_toml,
    seq_in,
    seq_unlock,
    seq_lock,
    set_lock,
    snippet_co,
    expected,
    caplog,
    tmp_path,
    prep_pyproject_toml,
    has_logging_occurred,
    prepare_folders_files,
):
    """Test create .lnk symlinks set_lock."""
    # pytest --showlocals --log-level INFO -k "test_create_links_set_lock" tests
    LOGGING["loggers"][g_app_name]["propagate"] = True
    logging.config.dictConfig(LOGGING)
    logger = logging.getLogger(name=g_app_name)
    logger.addHandler(hdlr=caplog.handler)
    caplog.handler.level = logger.level

    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as tmp_dir_path:
        path_tmp_dir = Path(tmp_dir_path)
        # prepare
        path_config = prep_pyproject_toml(path_pyproject_toml, path_tmp_dir)

        #    .in
        prepare_folders_files(seq_in, path_tmp_dir)
        #    .unlock .lock
        prepare_folders_files(seq_unlock, path_tmp_dir)
        prepare_folders_files(seq_lock, path_tmp_dir)

        inst = BackendType(
            path_config,
            parent_dir=tmp_dir_path,
        )
        for in_ in inst.in_files():
            assert in_.exists()

        #    cmd
        click_true = ("1", "true", "t", "yes", "y", "on")
        click_false = ("0", "false", "f", "no", "n", "off")
        if set_lock in click_true:
            from_suffix = ".lock"
        elif set_lock == click_false:
            from_suffix = ".unlock"
        else:
            is_locked = inst.is_locked(path_config)
            if is_locked:
                from_suffix = ".lock"
            else:
                from_suffix = ".unlock"

        #    Defaults to None, but can't pass in None explicitly
        func_cmd = [
            "--path",
            tmp_dir_path,
        ]

        if set_lock is not None and isinstance(set_lock, str):
            func_cmd.extend(["--set-lock", set_lock])

        if snippet_co is not None and isinstance(snippet_co, str):
            func_cmd.extend(["--snip", snippet_co])

        with patch(
            f"{g_app_name}.cli_unlock.BackendType",
            return_value=inst,
        ):
            result = runner.invoke(create_links, func_cmd)

        logger.info(f"out&err: {result.output}")
        logger.info(f"exc: {result.exception}")
        tb = result.exc_info[2]
        # msg_info = f"traceback: {pprint(traceback.format_tb(tb))}"
        msg_info = f"traceback: {traceback.format_tb(tb)}"
        logger.info(msg_info)

        assert has_logging_occurred(caplog)

        #    prove symlinks created
        for unlock_relpath in seq_in:
            lnk_relpath = unlock_relpath.replace(".in", ".lnk")
            path_lnk = path_tmp_dir.joinpath(lnk_relpath)
            if is_win():
                # Poor symlink support; no symlink, file copied
                is_file = path_lnk.exists() and path_lnk.is_file()
                assert is_file
            else:
                is_symlink = path_lnk.is_symlink()
                is_suffix_match = path_lnk.resolve().suffix == from_suffix
                assert (
                    is_suffix_match
                ), f"{path_lnk} does not resolve to a {from_suffix} file"
                # assert has_logging_occurred(caplog)
                assert is_symlink

        assert result.exit_code == expected


@pytest.mark.parametrize(
    "path_pyproject_toml, seq_in, seq_unlock, seq_lock, set_lock, snippet_co, expected",
    testdata_create_links_set_lock,
    ids=ids_create_links_set_lock,
)
def test_create_links_missing_files(
    path_pyproject_toml,
    seq_in,
    seq_unlock,
    seq_lock,
    set_lock,
    snippet_co,
    expected,
    caplog,
    tmp_path,
    prep_pyproject_toml,
    has_logging_occurred,
    prepare_folders_files,
):
    """Test create .lnk symlinks. Missing files."""
    # pytest --showlocals --log-level INFO -k "test_create_links_missing_files" tests
    LOGGING["loggers"][g_app_name]["propagate"] = True
    logging.config.dictConfig(LOGGING)
    logger = logging.getLogger(name=g_app_name)
    logger.addHandler(hdlr=caplog.handler)
    caplog.handler.level = logger.level

    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as tmp_dir_path:
        path_tmp_dir = Path(tmp_dir_path)
        # prepare
        path_config = prep_pyproject_toml(path_pyproject_toml, path_tmp_dir)

        #    .in
        prepare_folders_files(seq_in, path_tmp_dir)
        #    try without .unlock and .lock files --> MissingRequirementsFoldersFiles(6)
        inst = BackendType(
            path_config,
            parent_dir=tmp_dir_path,
        )
        for in_ in inst.in_files():
            assert in_.exists()

        #    cmd
        #    Defaults to None, but can't pass in None explicitly
        func_cmd = [
            "--path",
            tmp_dir_path,
        ]
        if set_lock is not None and isinstance(set_lock, str):
            func_cmd.extend(["--set-lock", set_lock])

        expected_exit_code = 6
        with patch(
            f"{g_app_name}.cli_unlock.BackendType",
            return_value=inst,
        ):
            result = runner.invoke(create_links, func_cmd)
            actual_exit_code = result.exit_code
            assert actual_exit_code == expected_exit_code
