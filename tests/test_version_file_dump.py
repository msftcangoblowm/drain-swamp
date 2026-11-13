"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

With coverage

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
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
from wreck._safe_path import fix_relpath

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

if TYPE_CHECKING:
    from collections.abc import (
        Callable,
        MutableSet,
        Sequence,
    )


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
    tmp_path: "Path",
    prepare_folders_files: "Callable[[Sequence[str | Path] | MutableSet[str | Path]], set[Path]]",
) -> None:
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


@pytest.mark.parametrize(
    "relpath_toml_file, app_name, kind",
    (
        pytest.param(
            Path("_project").joinpath("install_minimum.pyproject_toml"),
            "complete_awesome_perfect",
            "0.0.2",
            id="write-version-file-verify-version-str",
        ),
    ),
)
def test_write_to_file(
    relpath_toml_file: Path,
    app_name: str,
    kind: str,
    wd: WorkDir,
    prep_pyproject_toml: "Callable[[Path, Path, Path | None], Path | None]",
    prepare_folders_files: "Callable[[Sequence[str | Path] | MutableSet[str | Path]], set[Path]]",
    verify_tag_version: "Callable[[Path, str], bool]",
    request: pytest.FixtureRequest,
) -> None:
    """Test write_to_file. Assumes a real Python project skeleton."""
    # pytest --showlocals --log-level INFO -k "test_write_to_file" tests
    abspath_tests_dir = request.path.parent
    p_toml_file = abspath_tests_dir.joinpath(relpath_toml_file)

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
    path_dir_src = abspath_tests_dir.joinpath(
        "_project",
        "src",
        app_name,
    )
    path_dir_dest = wd.cwd / "src" / app_name
    path_f = path_dir_src.joinpath("__main__.py")
    prep_pyproject_toml(path_f, path_dir_dest, rename="__main__.py")

    # Act
    #    write to nonexistent version file
    write_to_file(p_config, kind, is_only_not_exists=True)
    #    None --> False
    write_to_file(p_config, kind, is_only_not_exists=None)

    # Verify version file contains "0.0.2"
    assert verify_tag_version(wd.cwd, kind)


def test_validate_template(
    tmp_path: "Path",
    prepare_folders_files: "Callable[[Sequence[str | Path] | MutableSet[str | Path]], set[Path]]",
) -> None:
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


@pytest.mark.parametrize(
    "relp_toml_file, app_name, kind, str_write_to, str_version_file",
    (
        pytest.param(
            Path("_project").joinpath("install_minimum.pyproject_toml"),
            "complete_awesome_perfect",
            "0.0.2",
            None,
            "src/{app_name}/_version.py",
            id="With-version_file",
        ),
        pytest.param(
            Path("_project").joinpath("install_minimum.pyproject_toml"),
            "complete_awesome_perfect",
            "0.0.2",
            "src/{app_name}/_version.py",
            None,
            id="With-write_to",
        ),
    ),
)
def test_write_version_files(
    relp_toml_file: Path,
    app_name: str,
    kind: str,
    str_write_to: str,
    str_version_file: str | None,
    wd: WorkDir,
    prep_pyproject_toml: "Callable[[Path, Path, Path | None], Path | None]",
    prepare_folders_files: "Callable[[Sequence[str | Path] | MutableSet[str | Path]], set[Path]]",
    verify_tag_version: "Callable[[Path, str], bool]",
    request: pytest.FixtureRequest,
) -> None:
    """Test write_version_files."""
    # pytest --showlocals --log-level INFO -k "test_write_version_files" tests
    abspath_tests_dir = request.path.parent
    p_toml_file = abspath_tests_dir.joinpath(relp_toml_file)

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
    assert not version_file_contents

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
        assert not version_file_contents_after

    #     None --> False. Write version file
    write_version_files(
        kind,
        root,
        write_to,
        version_file,
        is_only_not_exists=None,
    )
    assert verify_tag_version(wd.cwd, kind)


@pytest.mark.parametrize(
    "relp_toml_file, scm_str, expected",
    (
        pytest.param(
            Path("_project").joinpath("install_minimum.pyproject_toml"),
            None,
            SEM_VERSION_FALLBACK_SANE,
            id="_get_version-returns-None--sane-default",
        ),
        pytest.param(
            Path("_project").joinpath("install_minimum.pyproject_toml"),
            "0.0.2",
            "0.0.2",
            id="x.y.z--x.y.z",
        ),
    ),
)
def test_scm_version_fail(
    relp_toml_file: Path,
    scm_str: str | None,
    expected: str,
    wd: WorkDir,
    prep_pyproject_toml: "Callable[[Path, Path, Path | None], Path | None]",
    request: pytest.FixtureRequest,
    has_vcs_versioning: bool,
) -> None:
    """Test scm_version fail conditions."""
    # pytest --showlocals --log-level INFO -k "test_scm_version_fail" tests
    # pytest --showlocals --log-level INFO "tests/test_version_file_dump.py::test_scm_version_fail[_get_version-returns-None--sane-default]"
    abspath_tests_dir = request.path.parent
    p_toml_file = abspath_tests_dir.joinpath(relp_toml_file)

    # prepare
    #    pyproject.toml
    path_config = prep_pyproject_toml(p_toml_file, wd.cwd)
    config_abspath = str(path_config)

    # act
    if has_vcs_versioning:
        patch_target = "drain_swamp.monkey.wrap_get_version._scm_version_format"
    else:
        # setuptools_scm._get_version imported within module,
        #    drain_swamp.monkey.wrap_get_version
        patch_target = "drain_swamp.monkey.wrap_get_version._get_version"

    with patch(
        patch_target,
        return_value=scm_str,
    ):
        sem_ver_str = scm_version(config_abspath)

    # verify
    assert sem_ver_str == expected
