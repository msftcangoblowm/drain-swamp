"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

Unit test -- Module

.. code-block:: shell

   python -m coverage run --source='drain_swamp.monkey.plugins.ds_refresh_links' -m pytest \
   --showlocals tests/test_plugin_refresh_links.py && coverage report \
   --data-file=.coverage --include="**/monkey/plugins/ds_refresh_links.py"

Integration test

.. code-block:: shell

   make coverage
   pytest --showlocals --cov="drain_swamp" --cov-report=term-missing \
   --cov-config=pyproject.toml tests

"""

import logging
import logging.config
import shutil
from collections.abc import (
    Mapping,
    Sequence,
)
from pathlib import (
    Path,
    PurePath,
)
from unittest.mock import patch

import pytest

from drain_swamp import (
    PyProjectTOMLParseError,
    PyProjectTOMLReadError,
)
from drain_swamp.backend_abc import BackendType
from drain_swamp.backend_setuptools import BackendSetupTools  # noqa: F401
from drain_swamp.constants import (
    LOGGING,
    g_app_name,
)
from drain_swamp.monkey.config_settings import ConfigSettings
from drain_swamp.monkey.plugins.ds_refresh_links import (
    _is_set_lock,
    _parent_dir,
    _snippet_co,
    before_version_infer,
)
from drain_swamp.parser_in import TomlParser

testdata_is_set_lock = (
    (
        (
            "[project]\n"
            """name = "great-package"\n"""
            """version = "99.99.99a1.dev6"\n"""
            "[tool.incorrect-section-name]\n"
            """kind="current"\n"""
            """set-lock="0"\n\n"""
        ),
        None,
    ),
    (
        (
            "[project]\n"
            """name = "great-package"\n"""
            """version = "99.99.99a1.dev6"\n"""
            "[tool.config-settings]\n"
            """kind="current"\n"""
            """set-lock="0"\n\n"""
        ),
        False,
    ),
    (
        (
            "[project]\n"
            """name = "great-package"\n"""
            """version = "99.99.99a1.dev6"\n"""
            "[tool.config-settings]\n"
            """kind="current"\n"""
            """set-lock="1"\n\n"""
        ),
        True,
    ),
    (
        (
            "[project]\n"
            """name = "great-package"\n"""
            """version = "99.99.99a1.dev6"\n"""
            "[tool.config-settings]\n"
        ),
        None,
    ),
)
ids_is_set_lock = (
    "Incorrect section title. Expecting tool.config-settings",
    "set-lock provided. unlock",
    "set-lock provided. lock",
    "set-lock not provided. unlock",
)


@pytest.mark.parametrize(
    "toml_contents, is_lock_expected",
    testdata_is_set_lock,
    ids=ids_is_set_lock,
)
def test_is_set_lock(toml_contents, is_lock_expected, tmp_path):
    """Test is_set_lock."""
    # pytest --showlocals --log-level INFO -k "test_is_set_lock" tests
    # prepare
    d_section = ConfigSettings.get_section_dict(tmp_path, toml_contents)

    # default is unsupported type --> unlocked
    actual = _is_set_lock(d_section, default=None)
    assert actual == is_lock_expected

    # None --> indicates to get lock state from pyproject.toml
    actual = _is_set_lock(None)
    assert actual is None

    # unsupported default --> None
    actual = _is_set_lock(None, default="")
    assert actual is None

    actual = _is_set_lock(d_section)
    assert actual == is_lock_expected

    # From cli, but not going thru :code:`python -m build`
    d_section = {"--set-lock": "1"}
    actual = _is_set_lock(d_section)
    assert actual is True


testdata_snippet_co = (
    (
        {"--snip": "12345"},
        "--snip",
        "12345",
    ),
    (
        {"snip": "12345"},
        "snip",
        "12345",
    ),
    (
        {"--snip-co": "12345"},
        "--snip-co",
        "12345",
    ),
    (
        {"snip-co": "12345"},
        "snip-co",
        "12345",
    ),
    (
        ("snip-co", "12345"),
        "snip-co",
        None,
    ),
)
ids_snippet_co = (
    "with hyphens. snip",
    "without hyphens. snip",
    "with hyphens. snip-co",
    "without hyphens. snip-co",
    "config_settings is not a Mapping",
)


@pytest.mark.parametrize(
    "config_settings, key, expected_val",
    testdata_snippet_co,
    ids=ids_snippet_co,
)
def test_snippet_co(config_settings, key, expected_val):
    """Test _snippet_co."""
    # pytest --showlocals --log-level INFO -k "test_snippet_co" tests
    val_actual = _snippet_co(config_settings, default=None)
    if expected_val is None:
        assert val_actual is None
    else:
        assert val_actual is not None
        assert isinstance(val_actual, str)
        assert val_actual == expected_val


testdata_parent_dir = (
    (
        (
            "[project]\n"
            """name = "great-package"\n"""
            """version = "99.99.99a1.dev6"\n"""
            "[tool.config-settings]\n"
            """kind="current"\n"""
            """set-lock="0"\n\n"""
            """parent-dir="{}"\n"""
        )
    ),
)
ids_parent_dir = ("config_settings toml has placeholder for tmp_path",)


@pytest.mark.parametrize(
    "toml_contents",
    testdata_parent_dir,
    ids=ids_parent_dir,
)
def test_parent_dir(toml_contents, tmp_path):
    """Test _parent_dir."""
    # pytest --showlocals --log-level INFO -k "test_parent_dir" tests
    str_tmp_path = str(tmp_path)

    invalids = (
        None,
        1.2,
    )
    for invalid in invalids:
        # d_section not a dict; default unsupported
        actual = _parent_dir(invalid, default=invalid)
        assert actual is None

    valids = (
        ({"--parent-dir": str_tmp_path}, tmp_path),
        ({"parent-dir": str_tmp_path}, tmp_path),
        ({}, None),  # missing key parent-dir or --parent-dir
    )
    for d_section, expected in valids:
        actual = _parent_dir(d_section)
        assert actual == expected

    # normal usage
    contents_including_path = toml_contents.format(str_tmp_path)
    d_section = ConfigSettings.get_section_dict(tmp_path, contents_including_path)
    actual = _parent_dir(d_section)
    assert issubclass(type(actual), PurePath)
    assert actual == tmp_path


testdata_refresh = (
    (
        Path(__file__).parent.joinpath(
            "_good_files", "complete-manage-pip-prod-unlock.pyproject_toml"
        ),
        (
            "requirements/prod.in",
            "requirements/pins.in",
            "requirements/pip.in",
            "requirements/manage.in",
        ),
        (
            "requirements/prod.lock",
            "requirements/pip.lock",
            "requirements/manage.lock",
            "requirements/prod.unlock",
            "requirements/pip.unlock",
            "requirements/manage.unlock",
        ),
        (
            "requirements/prod.lnk",
            "requirements/pip.lnk",
            "requirements/manage.lnk",
        ),
        None,
        True,
    ),
    (
        Path(__file__).parent.joinpath(
            "_good_files", "complete-manage-pip-prod-unlock.pyproject_toml"
        ),
        (
            "requirements/prod.in",
            "requirements/pins.in",
            "requirements/tox.in",
            "requirements/manage.in",
        ),
        (
            "requirements/prod.lock",
            "requirements/tox.lock",
            "requirements/manage.lock",
            "requirements/prod.unlock",
            "requirements/tox.unlock",
            "requirements/manage.unlock",
        ),
        (
            "requirements/prod.lnk",
            "requirements/tox.lnk",
            "requirements/manage.lnk",
        ),
        None,
        False,
    ),
    (
        Path(__file__).parent.joinpath("_good_files", "complete.pyproject_toml"),
        (
            "requirements/prod.in",
            "requirements/pins.in",
            "requirements/pip.in",
            "requirements/pip-tools.in",
            "requirements/dev.in",
            "requirements/tox.in",
            "requirements/manage.in",
            "docs/requirements.in",
        ),
        (
            "requirements/prod.lock",
            "requirements/pip.lock",
            "requirements/pip-tools.lock",
            "requirements/dev.lock",
            "requirements/tox.lock",
            "requirements/manage.lock",
            "docs/requirements.lock",
            "requirements/prod.unlock",
            "requirements/pip.unlock",
            "requirements/pip-tools.unlock",
            "requirements/dev.unlock",
            "requirements/tox.unlock",
            "requirements/manage.unlock",
            "docs/requirements.unlock",
        ),
        (
            "requirements/prod.lnk",
            "requirements/pip.lnk",
            "requirements/pip-tools.lnk",
            "requirements/dev.lnk",
            "requirements/tox.lnk",
            "requirements/manage.lnk",
            "docs/requirements.lnk",
        ),
        None,
        False,
    ),
    (
        Path(__file__).parent.joinpath(
            "_good_files", "complete-manage-pip-prod-unlock.pyproject_toml"
        ),
        (
            "requirements/prod.in",
            "requirements/pins.in",
            "requirements/pip.in",
            "requirements/tox.in",
            "requirements/manage.in",
        ),
        (
            "requirements/prod.unlock",
            "requirements/pip.unlock",
            "requirements/tox.unlock",
            "requirements/manage.unlock",
            "requirements/prod.lock",
            "requirements/pip.lock",
            "requirements/tox.lock",
            "requirements/manage.lock",
        ),
        (
            "requirements/prod.lnk",
            "requirements/pip.lnk",
            "requirements/tox.lnk",
            "requirements/manage.lnk",
        ),
        "nonexistent_snippet",
        True,
    ),
    (
        Path(__file__).parent.joinpath("_bad_files", "snippet-nested.pyproject_toml"),
        (
            "requirements/prod.in",
            "requirements/pins.in",
            "requirements/pip.in",
            "requirements/tox.in",
            "requirements/manage.in",
            "requirements/pip-tools.in",
            "requirements/dev.in",
            "docs/requirements.in",
        ),
        (
            "requirements/prod.unlock",
            "requirements/pip.unlock",
            "requirements/tox.unlock",
            "requirements/manage.unlock",
            "requirements/pip-tools.unlock",
            "requirements/dev.unlock",
            "docs/requirements.unlock",
            "requirements/prod.lock",
            "requirements/pip.lock",
            "requirements/tox.lock",
            "requirements/manage.lock",
            "requirements/pip-tools.lock",
            "requirements/dev.lock",
            "docs/requirements.lock",
        ),
        (
            "requirements/prod.lnk",
            "requirements/pip.lnk",
            "requirements/tox.lnk",
            "requirements/manage.lnk",
            "requirements/pip-tools.lnk",
            "requirements/dev.lnk",
            "docs/requirements.lnk",
        ),
        None,
        True,
    ),
)
ids_refresh = (
    "missing tox (MissingRequirementsFoldersFiles)",
    "manage and tox",
    "constraint path needs to be resolved",
    "dependencies ok. snippet_co no match. Cannot update snippet",
    "dependencies ok. snippet malformed. Cannot update snippet",
)


@pytest.mark.parametrize(
    "path_pyproject_toml, seq_create_in_files, seq_create_lock_files, seq_expected, snippet_co, str_returned",
    testdata_refresh,
    ids=ids_refresh,
)
def test_plugin_refresh_links_normal(
    path_pyproject_toml,
    seq_create_in_files,
    seq_create_lock_files,
    seq_expected,
    snippet_co,
    str_returned,
    tmp_path,
    prepare_folders_files,
    prep_pyproject_toml,
    path_project_base,
    caplog,
    has_logging_occurred,
):
    """Test before_version_infer normal usage."""
    # pytest --showlocals --log-level INFO -k "test_plugin_refresh_links_normal" tests
    LOGGING["loggers"][g_app_name]["propagate"] = True
    logging.config.dictConfig(LOGGING)
    logger = logging.getLogger(name=g_app_name)
    logger.addHandler(hdlr=caplog.handler)
    caplog.handler.level = logger.level

    path_config = prep_pyproject_toml(path_pyproject_toml, tmp_path)

    # prepare
    assert isinstance(seq_create_in_files, Sequence)
    assert isinstance(seq_create_lock_files, Sequence)
    #    makes both folders and files, but blank files
    prepare_folders_files(seq_create_in_files, tmp_path)
    prepare_folders_files(seq_create_lock_files, tmp_path)

    #    move real files, no need to create folders
    path_cwd = path_project_base()
    for p_f in seq_create_in_files:
        abspath_src = path_cwd.joinpath(p_f)
        abspath_dest = tmp_path.joinpath(p_f)
        shutil.copy2(abspath_src, abspath_dest)
        # abspath_files.append(abspath_dest)
        pass

    for p_f in seq_create_lock_files:
        abspath_src = path_cwd.joinpath(p_f)
        abspath_dest = tmp_path.joinpath(p_f)
        shutil.copy2(abspath_src, abspath_dest)
        # abspath_files.append(abspath_dest)
        pass

    configs = (
        (
            "[project]\n"
            """name = "great-package"\n"""
            """version = "99.99.99a1.dev6"\n"""
            "[tool.config-settings]\n"
            """kind = "current"\n"""
            """set-lock = "0"\n"""
        ),
        (
            "[project]\n"
            """name = "great-package"\n"""
            """version = "99.99.99a1.dev6"\n"""
            "[tool.config-settings]\n"
            """kind = "current"\n"""
            """set-lock = "1"\n"""
        ),
    )
    for toml_contents in configs:
        if snippet_co is not None:
            toml_contents += f"""snip-co = "{snippet_co}"\n"""

        d_section = ConfigSettings.get_section_dict(tmp_path, toml_contents)

        inst = BackendType.load_factory(
            path_config,
            parent_dir=tmp_path,
        )
        assert inst.parent_dir == tmp_path

        """
        with patch(
            "drain_swamp.monkey.plugins.ds_refresh_links.Path.cwd",
            return_value=tmp_path,
        ):
        """
        with (
            patch(
                f"{g_app_name}.monkey.plugins.ds_refresh_links.BackendType.load_factory",
                return_value=inst,
            ),
            patch(
                "drain_swamp.monkey.plugins.ds_refresh_links.Path.cwd",
                return_value=tmp_path,
            ),
        ):
            str_msg = before_version_infer(d_section)
            if str_returned:
                # returns error message
                assert str_msg is not None
                assert isinstance(str_msg, str)
                logger.info(str_msg)
                assert has_logging_occurred(caplog)
            else:
                # success
                assert str_msg is None
                # verify symlinks -- created, w/o resolve
                for relpath_expected in seq_expected:
                    abspath_expected = tmp_path.joinpath(relpath_expected)
                    assert abspath_expected.exists() and abspath_expected.is_symlink()
                    # clean up symlink
                    abspath_expected.unlink()
                    assert not abspath_expected.exists()


def test_plugin_refresh_links_exceptions(
    tmp_path,
    prep_pyproject_toml,
    caplog,
    has_logging_occurred,
):
    """Test before_version_infer exceptions."""
    # pytest --showlocals --log-level INFO -k "test_plugin_refresh_links_exceptions" tests
    LOGGING["loggers"][g_app_name]["propagate"] = True
    logging.config.dictConfig(LOGGING)
    logger = logging.getLogger(name=g_app_name)
    logger.addHandler(hdlr=caplog.handler)
    caplog.handler.level = logger.level
    configs = (
        (
            "[project]\n"
            """name = "great-package"\n"""
            """version = "99.99.99a1.dev6"\n"""
            "[tool.config-settings]\n"
            """kind="current"\n"""
            """set-lock="0"\n\n"""
            f"""parent-dir="{str(tmp_path)}"\n"""
        ),
        (
            "[project]\n"
            """name = "great-package"\n"""
            """version = "99.99.99a1.dev6"\n"""
            "[tool.config-settings]\n"
            """kind="current"\n"""
            """set-lock="1"\n\n"""
            f"""parent-dir="{str(tmp_path)}"\n"""
        ),
    )

    path_config = None
    for toml_contents in configs:
        d_section = ConfigSettings.get_section_dict(tmp_path, toml_contents)
        if path_config is not None and path_config.exists():
            path_config.unlink()

        with patch(
            "drain_swamp.monkey.plugins.ds_refresh_links.Path.cwd",
            return_value=tmp_path,
        ):
            # No pyproject.toml --> PyProjectTOMLReadError msg
            str_msg = before_version_infer(d_section)
            assert str_msg is not None

            if path_config is not None and path_config.exists():
                path_config.unlink()

            # Malformed pyproject.toml
            path_pyproject_toml = Path(__file__).parent.joinpath(
                "_bad_files",
                "backend_only.pyproject_toml",
            )
            path_config = prep_pyproject_toml(path_pyproject_toml, tmp_path)
            str_msg = before_version_infer(d_section)
            assert str_msg is not None
            if path_config is not None and path_config.exists():
                path_config.unlink()

    pyproject_tomls = (
        (
            Path(__file__).parent.joinpath(
                "_good_files",
                "complete-manage-pip-prod-unlock.pyproject_toml",
            ),
            None,
        ),
    )
    for path_pyproject_toml, expected_error_msg in pyproject_tomls:
        for toml_contents in configs:
            # prepare
            d_section = ConfigSettings.get_section_dict(tmp_path, toml_contents)
            path_config = prep_pyproject_toml(path_pyproject_toml, tmp_path)
            assert path_config.exists() and path_config.is_file()
            with patch(
                "drain_swamp.monkey.plugins.ds_refresh_links.Path.cwd",
                return_value=tmp_path,
            ):
                try:
                    d_pyproject_toml, path_f = TomlParser.read(tmp_path)
                except (PyProjectTOMLParseError, PyProjectTOMLReadError):
                    d_pyproject_toml = None
                assert d_pyproject_toml is not None
                assert isinstance(d_pyproject_toml, Mapping)

                """BackendNotSupportedError
                Don't replace BackendType.load_factory, into config_settings
                provide parent-dir
                """
                with (
                    patch(
                        "drain_swamp.backend_abc.BackendType.determine_backend",
                        return_value="maniac_into_squats",
                    ),
                ):
                    before_version_infer(d_section)

                # normal execution
                str_error = before_version_infer(d_section)
                if expected_error_msg is None:
                    assert str_error is None
                else:
                    assert str_error is not None and str_error.startswith(
                        expected_error_msg
                    )

            if path_config is not None and path_config.exists():
                path_config.unlink()

        # prepare
        # no set-lock in config_settings --> get set-lock from pyproject.toml --> AssertionError
        toml_contents = (
            "[project]\n"
            """name = "great-package"\n"""
            """version = "99.99.99a1.dev6"\n"""
            "[tool.config-settings]\n"
            """kind="current"\n"""
            f"""parent-dir="{str(tmp_path)}"\n"""
        )
        path_pyproject_toml = Path(__file__).parent.joinpath(
            "_bad_files",
            "static_dependencies.pyproject_toml",
        )
        expected_err = (
            "Either no pyproject.toml section, tool.setuptools.dynamic "
            "or no dependencies key"
        )
        d_section = ConfigSettings.get_section_dict(tmp_path, toml_contents)
        if path_config is not None and path_config.exists():
            path_config.unlink()

        path_config = prep_pyproject_toml(path_pyproject_toml, tmp_path)
        assert path_config.exists() and path_config.is_file()
        with patch(
            "drain_swamp.monkey.plugins.ds_refresh_links.Path.cwd",
            return_value=tmp_path,
        ):
            str_error = before_version_infer(d_section)
            assert has_logging_occurred(caplog)
            assert str_error == expected_err
