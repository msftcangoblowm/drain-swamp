"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

Unit test -- Module

.. code-block:: shell

   python -m coverage run --source='drain_swamp.version_file.dump_version' -m pytest \
   --showlocals tests/test_version_file_dump.py && coverage report \
   --data-file=.coverage --include="**/version_file/dump_version.py"

Integration test

.. code-block:: shell

   make coverage
   pytest --showlocals --cov="drain_swamp" --cov-report=term-missing \
   --cov-config=pyproject.toml tests

"""

from pathlib import (
    Path,
    PurePath,
)
from unittest.mock import patch

import pytest

from drain_swamp._safe_path import fix_relpath
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
    """Fixture modifies WorkDir.

    - Change cwd to be a package folder

    - Initializes git

    - Set the git add and commit commands

    .. seealso::

       Credit
       `[Author] <https://github.com/pypa/setuptools-scm/blob/main/pyproject.toml>`_
       `[Source] <https://github.com/pypa/setuptools_scm/blob/main/testing/wd_wrapper.py>`_
       `[License: MIT] <https://github.com/pypa/setuptools-scm/blob/main/LICENSE>`_

    """
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
    """Test dump version file."""
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
    """Test write_to_file. Assumes a real Python project skeleton."""
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
    """Test _validate_template."""
    # pytest --showlocals --log-level INFO -k "test_validate_template" tests

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


testdata_write_version_files = (
    (
        Path(__file__).parent.joinpath(
            "_project",
            "install_minimum.pyproject_toml",
        ),
        "complete_awesome_perfect",
        "0.0.2",
        None,
        "src/{app_name}/_version.py",
    ),
    (
        Path(__file__).parent.joinpath(
            "_project",
            "install_minimum.pyproject_toml",
        ),
        "complete_awesome_perfect",
        "0.0.2",
        "src/{app_name}/_version.py",
        None,
    ),
)
ids_write_version_files = (
    "With version_file",
    "With write_to",
)


@pytest.mark.parametrize(
    "p_toml_file, app_name, kind, str_write_to, str_version_file",
    testdata_write_version_files,
    ids=ids_write_version_files,
)
def test_write_version_files(
    p_toml_file,
    app_name,
    kind,
    str_write_to,
    str_version_file,
    wd,
    prep_pyproject_toml,
    prepare_folders_files,
    verify_tag_version,
):
    """Test write_version_files."""
    # pytest --showlocals --log-level INFO -k "test_write_version_files" tests
    p_ver_file = wd.cwd.joinpath("src", app_name, "_version.py")
    p_empty_txt = wd.cwd.joinpath("dist", "empty.txt")
    root = wd.cwd

    d_args = {"app_name": app_name}
    if str_version_file is not None:
        version_file = str_version_file.format(**d_args)
    else:
        version_file = str_version_file

    # write_to must be abspath
    if str_write_to is not None:
        write_to_relpath = str_write_to.format(**d_args)
        write_to = fix_relpath(write_to_relpath)
    else:
        write_to = str_write_to

    # prepare
    #    pyproject.toml
    prep_pyproject_toml(p_toml_file, root)

    #    empty files
    req_seq = (
        fix_relpath("dist/empty.txt"),
        fix_relpath(f"src/{app_name}/__init__.py"),
        fix_relpath(f"src/{app_name}/__main__.py"),
        fix_relpath(f"src/{app_name}/_version.py"),
    )
    prepare_folders_files(req_seq, root)
    #   Only wanted the folder
    p_empty_txt.unlink()
    version_file_contents = p_ver_file.read_text()
    assert len(version_file_contents) == 0

    # Act
    #     version file exist, so write is skipped
    write_version_files(
        kind,
        root,
        write_to,
        version_file,
        is_only_not_exists=True,
    )
    # Verify
    #     version file exists and is empty. Cuz exists, write skipped
    version_file_contents_after = p_ver_file.read_text()
    if version_file is not None:
        assert len(version_file_contents_after) == 0

    #     None --> False. Write version file
    write_version_files(
        kind,
        root,
        write_to,
        version_file,
        is_only_not_exists=None,
    )
    assert verify_tag_version(wd.cwd, kind) is True


testdata_scm_version_fail = (
    (
        Path(__file__).parent.joinpath(
            "_project",
            "install_minimum.pyproject_toml",
        ),
        None,
        SEM_VERSION_FALLBACK_SANE,
    ),
    (
        Path(__file__).parent.joinpath(
            "_project",
            "install_minimum.pyproject_toml",
        ),
        "0.0.2",
        "0.0.2",
    ),
)
ids_scm_version_fail = (
    "_get_version returns None --> sane default",
    "x.y.z --> x.y.z",
)


@pytest.mark.parametrize(
    "p_toml_file, scm_str, expected",
    testdata_scm_version_fail,
    ids=ids_scm_version_fail,
)
def test_scm_version_fail(
    p_toml_file,
    scm_str,
    expected,
    wd,
    prep_pyproject_toml,
):
    """Test scm_version fail conditions."""
    # pytest --showlocals --log-level INFO -k "test_scm_version_fail" tests

    # prepare
    #    pyproject.toml
    path_config = prep_pyproject_toml(p_toml_file, wd.cwd)
    config_abspath = str(path_config)

    # act
    with patch(
        "drain_swamp.monkey.wrap_get_version._get_version",
        return_value=scm_str,
    ):
        sem_ver_str = scm_version(config_abspath)

    # verify
    assert sem_ver_str == expected
