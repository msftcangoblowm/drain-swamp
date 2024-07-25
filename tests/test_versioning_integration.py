"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

Build environment for taking current or tag version

.. code-block:: shell

   pytest --showlocals --log-level INFO tests/test_versioning_integration.py
   pytest --showlocals --cov="drain_swamp" --cov-report=term-missing tests/test_versioning_integration.py

"""

import logging
import logging.config
from pathlib import Path

import pytest

from drain_swamp.constants import (
    LOGGING,
    g_app_name,
)
from drain_swamp.version_file.dump_version import write_version_files
from drain_swamp.version_semantic import _tag_version

testdata_version_file_read_normal = (
    (
        Path(__file__).parent.joinpath(
            "_good_files",
            "complete-manage-pip-prod-unlock.pyproject_toml",
        ),
        "src/complete_awesome_perfect/_version.py",
        "0.0.5",
    ),
    (
        Path(__file__).parent.joinpath(
            "_good_files",
            "complete-version-txt.pyproject_toml",
        ),
        "VERSION.txt",
        "0.0.5",
    ),
    pytest.param(
        Path(__file__).parent.joinpath(
            "_bad_files",
            "complete-version-other.pyproject_toml",
        ),
        "VERSION.rst",
        None,
        marks=pytest.mark.xfail(raises=ValueError),
    ),
)
ids_version_file_read_normal = (
    "tool.setuptools.dynamic.version attr key",
    "tool.setuptools.dynamic.version file key",
    "unsupported version file type. rst",
)


@pytest.mark.parametrize(
    "path_config_src, version_file_relpath, kind_expected",
    testdata_version_file_read_normal,
    ids=ids_version_file_read_normal,
)
def test_version_file_read_normal(
    path_config_src,
    version_file_relpath,
    kind_expected,
    tmp_path,
    prep_pyproject_toml,
    prepare_folders_files,
    caplog,
    has_logging_occurred,
):
    """version_file contains the tag version, retrieve it

    Does not depend on git
    """
    # pytest --showlocals --log-level INFO -k "test_version_file_read_normal" tests
    LOGGING["loggers"][g_app_name]["propagate"] = True
    logging.config.dictConfig(LOGGING)
    logger = logging.getLogger(name=g_app_name)
    logger.addHandler(hdlr=caplog.handler)
    caplog.handler.level = logger.level

    kind = "0.0.5"

    relpath_version_file = Path(version_file_relpath)
    write_to = relpath_version_file

    # prepare
    #    base package folder
    path_cwd = tmp_path / "complete_awesome_perfect"
    path_cwd.mkdir()

    #    package code folder
    path_dir_dest = path_cwd.joinpath("src", "complete_awesome_perfect")
    path_dir_dest.mkdir(parents=True)

    path_f = path_cwd / relpath_version_file

    #    pyproject.toml
    prep_pyproject_toml(path_config_src, path_cwd)

    # get tag version, but no existing file
    next_versions = (
        None,
        "",
        "   ",  # whitespace only
        0.1234,  # unsupported version
    )
    for next_version in next_versions:
        with pytest.warns(UserWarning) as w:
            # static dependency would be read from pyproject.toml
            # so actual is not always None
            actual = _tag_version(
                next_version=next_version,
                path=path_cwd,
            )
            assert len(w) == 1
            assert str(w[0].message) != 0
            assert actual is None

    #    _version.py|VERSION.txt -- empty file
    seq_empties = (version_file_relpath,)
    prepare_folders_files(seq_empties, path_cwd)

    # act
    write_version_files(kind, path_cwd, write_to, None)

    # confirm
    contents_actual = path_f.read_text()
    if kind_expected is None:
        assert contents_actual is None
    else:
        assert kind in contents_actual

    # next_version empty str | just whitespace | None --> no write to version_file
    for next_version in next_versions:
        actual = _tag_version(
            next_version=next_version,
            path=path_cwd,
        )
        assert isinstance(actual, str)

    # assert has_logging_occurred(caplog)
    pass


testdata_version_file_read_special = (
    (
        Path(__file__).parent.joinpath(
            "_bad_files",
            "static-version.pyproject_toml",
        ),
        "src/complete_awesome_perfect/_version.py",
        "0.0.5",
    ),
)
ids_version_file_read_special = ("project.version, not dynamic",)


@pytest.mark.parametrize(
    "path_config_src, version_file_relpath, kind_expected",
    testdata_version_file_read_special,
    ids=ids_version_file_read_special,
)
def test_version_file_read_special(
    path_config_src,
    version_file_relpath,
    kind_expected,
    tmp_path,
    prep_pyproject_toml,
    prepare_folders_files,
    caplog,
    has_logging_occurred,
):
    # pytest --showlocals --log-level INFO -k "test_version_file_read_special" tests
    kind = "0.0.5"
    relpath_version_file = Path(version_file_relpath)
    write_to = relpath_version_file

    # prepare
    #    base package folder
    path_cwd = tmp_path / "complete_awesome_perfect"
    path_cwd.mkdir()

    #    package code folder
    path_dir_dest = path_cwd.joinpath("src", "complete_awesome_perfect")
    path_dir_dest.mkdir(parents=True)

    path_f = path_cwd / relpath_version_file

    #    pyproject.toml
    prep_pyproject_toml(path_config_src, path_cwd)

    #    _version.py|VERSION.txt -- empty file
    seq_empties = (version_file_relpath,)
    prepare_folders_files(seq_empties, path_cwd)

    # act
    write_version_files(kind, path_cwd, write_to, None)

    # confirm
    contents_actual = path_f.read_text()
    if kind_expected is None:
        assert contents_actual is None
    else:
        assert kind in contents_actual

    next_versions = (
        None,
        "",
        "   ",  # whitespace only
        0.1234,  # unsupported version
    )
    for next_version in next_versions:
        actual = _tag_version(
            next_version=next_version,
            path=path_cwd,
        )
        assert isinstance(actual, str)


def test_version_file_read_invalid(
    tmp_path,
    prep_pyproject_toml,
    prepare_folders_files,
):
    # pytest --showlocals --log-level INFO -k "test_version_file_read_invalid" tests
    path_config_src = Path(__file__).parent.joinpath(
        "_good_files",
        "backend-only.pyproject_toml",
    )
    # prepare

    #    base package folder
    path_cwd = tmp_path / "complete_awesome_perfect"
    path_cwd.mkdir()

    #    pyproject.toml
    prep_pyproject_toml(path_config_src, path_cwd)

    next_versions = (
        None,
        "",
        "   ",  # whitespace only
        0.1234,  # unsupported version
    )
    for next_version in next_versions:
        with pytest.warns(UserWarning) as w:
            actual = _tag_version(
                next_version=next_version,
                path=path_cwd,
            )
            assert len(w) == 1
            assert str(w[0].message) != 0
            assert actual is None
