"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

.. code-block:: shell

   pytest --showlocals --log-level INFO tests/test_version_file_dump.py
   pytest --showlocals --cov="drain_swamp" --cov-report=term-missing tests/test_version_file_dump.py

"""

from pathlib import (
    Path,
    PurePath,
)
from unittest.mock import patch

import pytest

from drain_swamp.monkey.wrap_get_version import (
    SEM_VERSION_FALLBACK_SANE,
    scm_version,
    write_to_file,
)
from drain_swamp.version_file.dump_version import (
    _validate_template,
    dump_version,
    write_version_files,
)

from .wd_wrapper import WorkDir


@pytest.fixture()
def wd(wd: WorkDir) -> WorkDir:
    # Create project base folder with project name
    path_new = wd.cwd / "complete_awesome_perfect"
    path_new.mkdir()
    wd.cwd = path_new

    wd("git init")
    wd("git config user.email test@example.com")
    wd('git config user.name "a test"')
    wd.add_command = "git add ."
    wd.commit_command = "git commit --no-verify --no-gpg-sign -m test-{reason}"
    return wd


def test_dump_version(
    tmp_path,
    prepare_folders_files,
):
    # pytest --showlocals --log-level INFO -k "test_dump_version" tests
    # prepare
    seq_rel_paths = ("_version.py",)
    prepare_folders_files(seq_rel_paths, tmp_path)

    version = "0.0.1a.dev1"
    # absolute path obsolete --> DeprecationWarning
    write_to = tmp_path / "_version.py"
    with pytest.deprecated_call():
        dump_version(tmp_path, version, write_to)


testdata_write_to_file = (
    (
        Path(__file__).parent.joinpath(
            "_project",
            "install_minimum.pyproject_toml",
        ),
        "complete_awesome_perfect",
        "0.0.2",
    ),
)
ids_write_to_file = ("write version file verify version str",)


@pytest.mark.parametrize(
    "p_toml_file, app_name, kind",
    testdata_write_to_file,
    ids=ids_write_to_file,
)
def test_write_to_file(
    p_toml_file,
    app_name,
    kind,
    wd,
    prep_pyproject_toml,
    prepare_folders_files,
    verify_tag_version,
):
    """Assumes a real Python project skeleton"""
    # pytest --showlocals --log-level INFO -k "test_write_to_file" tests
    assert wd.cwd.exists() and wd.cwd.is_dir()

    # prepare
    #    .gitignore
    msg_gitignore = (
        "dist/*.whl\n"
        "dist/*.tar.gz\n"
        "requirements/*.lnk\n"
        "src/*.egg-info/*\n"
        "src/*/_version.py\n"
    )
    wd.write(".gitignore", msg_gitignore)

    #    pyproject.toml
    p_config = prep_pyproject_toml(p_toml_file, wd.cwd)

    #    empty files
    req_seq = (
        "dist/empty.txt",
        f"src/{app_name}/__init__.py",
        f"src/{app_name}/__main__.py",
        # f"src/{app_name}/_version.py",
        "requirements/prod.in",
        "requirements/pip.in",
        "requirements/manage.in",
        "requirements/prod.unlock",
        "requirements/pip.unlock",
        "requirements/manage.unlock",
        "README.rst",
        "LICENSE",
    )
    prepare_folders_files(req_seq, wd.cwd)
    #   Only wanted the folder
    wd.cwd.joinpath("dist", "empty.txt").unlink()

    #    src/complete_awesome_perfect/__main__.py
    path_dir_src = Path(__file__).parent.joinpath(
        "_project",
        "src",
        app_name,
    )
    path_dir_dest = wd.cwd / "src" / app_name
    path_f = path_dir_src.joinpath("__main__.py")
    prep_pyproject_toml(path_f, path_dir_dest, rename="__main__.py")

    # Act
    #    write to nonexistant version file
    write_to_file(p_config, kind, is_only_not_exists=True)
    #    None --> False
    write_to_file(p_config, kind, is_only_not_exists=None)

    # Verify version file contains "0.0.2"
    assert verify_tag_version(wd.cwd, kind) is True


def test_validate_template(tmp_path, prepare_folders_files):
    # prepare
    target = Path("_version.py")
    assert issubclass(type(target), PurePath)
    seq_rel_paths = (target,)
    prepare_folders_files(seq_rel_paths, tmp_path)

    # supplying a nonsense template
    invalids = (
        "",
        "   ",
    )
    for template in invalids:
        with pytest.warns(Warning):
            actual = _validate_template(target, template)
            assert actual is not None
            assert isinstance(actual, str)
            assert len(actual) != 0

    template = None
    # unsupported target suffix type --> ValueError
    target = Path("_version.rst")
    with pytest.raises(ValueError):
        _validate_template(target, template)

    # supported target suffix
    target = Path("_version.py")
    actual = _validate_template(target, template)
    assert actual is not None
    assert isinstance(actual, str)
    assert len(actual) != 0

    # supply a template
    template_rst = {".rst": "{version}"}
    target = Path("_version.rst")
    actual = _validate_template(target, template_rst)
    assert actual is not None
    assert isinstance(actual, dict)


def test_write_version_files(
    wd,
    prep_pyproject_toml,
    prepare_folders_files,
    verify_tag_version,
):
    # pytest --showlocals --log-level INFO -k "test_write_version_files" tests
    kind = "0.0.2"
    app_name = "complete_awesome_perfect"

    # prepare
    #    pyproject.toml
    p_toml_file = Path(__file__).parent.joinpath(
        "_project",
        "install_minimum.pyproject_toml",
    )
    prep_pyproject_toml(p_toml_file, wd.cwd)

    #    empty files
    req_seq = (
        "dist/empty.txt",
        f"src/{app_name}/__init__.py",
        f"src/{app_name}/__main__.py",
        f"src/{app_name}/_version.py",
    )
    prepare_folders_files(req_seq, wd.cwd)
    #   Only wanted the folder
    wd.cwd.joinpath("dist", "empty.txt").unlink()

    # Act
    #     version file exist, so write is skipped
    p_ver_file = wd.cwd.joinpath("src", app_name, "_version.py")
    assert len(p_ver_file.read_text()) == 0
    write_version_files(
        kind,
        wd.cwd,
        None,
        f"src/{app_name}/_version.py",
        is_only_not_exists=True,
    )
    # Verify
    #     version file exists and is empty. Cuz exists, write skipped
    assert len(p_ver_file.read_text()) == 0

    #     None --> False. Write version file
    write_version_files(
        kind,
        wd.cwd,
        None,
        f"src/{app_name}/_version.py",
        is_only_not_exists=None,
    )
    assert verify_tag_version(wd.cwd, kind) is True


testdata_scm_version_fail = (
    (
        Path(__file__).parent.joinpath(
            "_project",
            "install_minimum.pyproject_toml",
        )
    ),
)
ids_scm_version_fail = ("_get_version returns None --> sane default",)


@pytest.mark.parametrize(
    "p_toml_file",
    testdata_scm_version_fail,
    ids=ids_scm_version_fail,
)
def test_scm_version_fail(
    p_toml_file,
    wd,
    prep_pyproject_toml,
):
    # pytest --showlocals --log-level INFO -k "test_scm_version_fail" tests
    # prepare
    #    pyproject.toml
    path_config = prep_pyproject_toml(p_toml_file, wd.cwd)
    config_abspath = str(path_config)

    valids = (
        (None, SEM_VERSION_FALLBACK_SANE),
        ("0.0.2", "0.0.2"),
    )
    for valid, expected in valids:
        with patch(
            "drain_swamp.monkey.wrap_get_version._get_version",
            return_value=valid,
        ):
            sem_ver_str = scm_version(config_abspath)
            assert sem_ver_str == expected
