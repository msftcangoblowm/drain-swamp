"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

Unittest module :py:mod:`drain_swamp.monkey.wrap_infer_version`

Unit test -- Module

.. code-block:: shell

   python -m coverage run --source='drain_swamp.monkey.wrap_infer_version' -m pytest \
   --showlocals tests/test_wrap_infer_version.py && coverage report \
   --data-file=.coverage --include="**/monkey/wrap_infer_version.py"

Integration test

.. code-block:: shell

   make coverage
   pytest --showlocals --cov="drain_swamp" --cov-report=term-missing \
   --cov-config=pyproject.toml tests

.. seealso::

   https://github.com/pypa/setuptools_scm/blob/main/testing/test_integration.py
   https://github.com/pypa/setuptools_scm/blob/main/testing/wd_wrapper.py

"""

import logging
import logging.config
import shutil
import sys
from pathlib import Path

import pytest
from setuptools_scm._version_cls import _version_as_tuple

from drain_swamp._run_cmd import run_cmd
from drain_swamp.constants import (
    LOGGING,
    g_app_name,
)
from drain_swamp.monkey.config_settings import ConfigSettings
from drain_swamp.monkey.wrap_infer_version import _rage_quit

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


testdata_dist_get_cmdline_options = (
    (
        Path(__file__).parent.joinpath(
            "_project",
            "install_minimum.pyproject_toml",
        ),
        "complete_awesome_perfect",
        "0.2.0",
        "0.2.1",
    ),
)
ids_dist_get_cmdline_options = (
    "write config_settings .toml file to pass in kwargs to build plugins",
)


@pytest.mark.parametrize(
    "p_toml_file, app_name, commit_version_str, kind",
    testdata_dist_get_cmdline_options,
    ids=ids_dist_get_cmdline_options,
)
def test_dist_get_cmdline_options(
    p_toml_file,
    app_name,
    commit_version_str,
    kind,
    prep_pyproject_toml,
    prepare_folders_files,
    caplog,
    has_logging_occurred,
    wd: WorkDir,
    monkeypatch: pytest.MonkeyPatch,
    verify_tag_version,
):
    """Can access command line options using Distribution.get_cmdline_options.

    In tmp path

    .. code-block:: shell

       cd complete_awesome_perfect
       DS_CONFIG_SETTINGS=../setuptools-build.toml ~/Downloads/git_decimals/drain_swamp/.venv/bin/python -m build --no-isolation --sdist

    """
    # pytest --showlocals --log-level INFO -k "test_dist_get_cmdline_options" tests
    LOGGING["loggers"][g_app_name]["propagate"] = True
    logging.config.dictConfig(LOGGING)
    logger = logging.getLogger(name=g_app_name)
    logger.addHandler(hdlr=caplog.handler)
    caplog.handler.level = logger.level

    p_base = wd.cwd.parent
    logger.info(f"wd.cwd: {wd.cwd}")
    assert wd.cwd.exists() and wd.cwd.is_dir()

    logger.info(f"sys.executable: {sys.executable}")
    logger.info(f"""scm-version path: {shutil.which("scm-version")}""")

    f_name = f"{app_name}-{kind}.tar.gz"

    # prepare
    #    .gitignore
    msg_gitignore = (
        "dist/*.whl\n"
        "dist/*.tar.gz\n"
        "requirements/*.lnk\n"
        "src/*.egg-info/*\n"
        "src/*/_version.py\n"
        f"{ConfigSettings.FILE_NAME_DEFAULT}\n\n"
    )
    wd.write(".gitignore", msg_gitignore)

    #    empty files
    req_seq = (
        "dist/empty.txt",
        f"src/{app_name}/__init__.py",
        f"src/{app_name}/__main__.py",
        f"src/{app_name}/_version.py",
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

    #    src/complete_awesome_perfect/_version.py
    str_version_file = (
        f"""__version__ = version = '{commit_version_str}'\n"""
        "__version_tuple__ = version_tuple = "
        f"""{str(_version_as_tuple(commit_version_str))}\n\n"""
    )
    path_f = path_dir_dest.joinpath("_version.py")
    path_f.write_text(str_version_file)

    wd.add_and_commit()
    wd(f"git tag --no-sign -m 'skeleton package' {commit_version_str}")

    # monkeypatch.chdir(p_package_base)

    # export DIST_EXTRA_CONFIG=/tmp/setuptools-build.cfg
    # echo -e '[build_ext]\nparallel = 8\n[bdist_wheel]\npy_limited_api = cp311' > $DIST_EXTRA_CONFIG
    # export DS_CONFIG_SETTINGS=/tmp/setuptools-build.toml
    """cat <<-EOF > "$DS_CONFIG_SETTINGS"
    [project]
    name = "whatever"
    [tool.config-settings]
    kind="0.2.1"
    set-lock="0"
    EOF
    """
    toml_path = str(p_base.joinpath(ConfigSettings.FILE_NAME_DEFAULT))
    toml_contents = (
        "[project]\n"
        f"""name = "{app_name}"\n"""
        """version = "99.99.99a1.dev6"\n"""
        f"[tool.{ConfigSettings.SECTION_NAME}]\n"
        f"""kind="{kind}"\n"""
        """set-lock="0"\n\n"""
    )
    names = (
        ConfigSettings.FILE_NAME_DEFAULT,
        None,
        1.234,
    )
    for file_name in names:
        # modifies os.environ AND writes config settings file
        cs = ConfigSettings(file_name=file_name)
        cs.write(p_base, toml_contents)

    env = None
    assert ConfigSettings.get_abs_path() == toml_path

    cwd = wd.cwd
    cmd = (
        sys.executable,
        "-m",
        "build",
        "--no-isolation",
        "--sdist",
        f"-C--kind='{kind}'",  # unfortunately not passed on by setuptools
        "-C--set-lock='0'",  # unfortunately not passed on by setuptools
    )

    # prepare
    #    pyproject.toml
    prep_pyproject_toml(p_toml_file, wd.cwd)

    # plugins: refresh_links (needs set-lock), cli_scm_version.py (needs kind)
    t_ret = run_cmd(cmd, cwd=cwd, env=env)
    out, err, exit_code, exc = t_ret
    logger.info("WILL FAIL, with exit code 1, if in dependency hell")
    msg_info = (
        "Test deals with passing config_settings thru to build plugin "
        "subprocess. Cannot resolve or detect dependency hell"
    )
    logger.info(msg_info)
    msg_info = (
        "Advice on resolving dependency hell. In local virtual "
        "environment, each package, will have a 2nd meta data package. "
        "Within which is file, METADATA. In this file, edit the "
        "dependency versions. Run tests locally."
        "Once tests pass. Update requirements/ and docs/ .lock files. "
        "publish a release and install the release to your local virtual environment"
    )
    logger.info(msg_info)
    logger.info(f"out {out!r}")
    logger.info(f"err {err!r}")
    logger.info(list(cwd.glob("**/*.tar.gz")))

    assert has_logging_occurred(caplog)
    assert exc is None

    condition = "Missing dependencies" in out
    if condition:
        """Chicken and egg situation. drain-swamp may just need a
        release to resolve issue"""
        idx = out.index("Missing dependencies")
        whats_missing = out[idx:]
        whats_missing = whats_missing.replace("\n", " ")
        reason = (
            "Missing dependencies which might be resolvable by "
            f"publishing a release. {whats_missing}"
        )
        # If condition met, execution stops at xfail line
        pytest.xfail(reason)
    else:
        assert exit_code == 0
        path_dist_dir = cwd.joinpath("dist", f_name)
        assert path_dist_dir.exists()

        # logger.info(f"version file contents:\n{path_f.read_text()}")
        assert verify_tag_version(wd.cwd, kind) is True


testdata_infer_version_fail = (
    (
        "0.0.2",
        "0",
        1,
        "does not appear to be a Python project: no pyproject.toml or setup.py",
    ),
)
ids_infer_version_fail = ("missing pyproject.toml. build fails",)


@pytest.mark.parametrize(
    "kind, set_lock, exit_code_expected, msg_fragment_expected",
    testdata_infer_version_fail,
    ids=ids_infer_version_fail,
)
def test_infer_version_fail(
    kind,
    set_lock,
    exit_code_expected,
    msg_fragment_expected,
    wd,
    caplog,
    has_logging_occurred,
):
    """Situations where wrap_infer_version would fail."""
    # pytest --showlocals --log-level INFO -k "test_infer_version_fail" tests

    # missing pyproject.toml build calls infer_version. Which runs build plugins
    cmd = (
        sys.executable,
        "-m",
        "build",
        "--no-isolation",
        "--sdist",
        f"-C--kind='{kind}'",  # unfortunately not passed on by setuptools
        f"-C--set-lock='{set_lock}'",  # unfortunately not passed on by setuptools
    )
    t_ret = run_cmd(cmd, cwd=wd.cwd)
    out, err, exit_code, exc = t_ret
    assert exit_code == exit_code_expected
    assert out.endswith(msg_fragment_expected)

    # _rage_quit
    #    Called by drain_swamp.monkey.wrap_infer_version::infer_version
    #    If 1st arg is None, log a warning and quit
    msg = "Hello World"
    with pytest.raises(SystemExit):
        #    logs a warning
        _rage_quit(None, msg)
    _rage_quit("Not None", msg)


testdata_config_settings_read = (
    (
        (
            "[project]\n"
            """name = "great-package"\n"""
            """version = "99.99.99a1.dev6"\n"""
            "[tool.incorrect-section-name]\n"
            """kind="current"\n"""
            """set-lock="0"\n\n"""
        ),
        0,
        True,
    ),
    (
        (
            "[project]\n"
            """name = "great-package"\n"""
            """version = "99.99.99a1.dev6"\n"""
            f"[tool.{ConfigSettings.SECTION_NAME}]\n"
            """kind="current"\n"""
            """set-lock="0"\n\n"""
        ),
        2,
        False,
    ),
    (
        (
            "[project]\n"
            """name = "great-package"\n"""
            """version = "99.99.99a1.dev6"\n"""
            f"[tool.{ConfigSettings.SECTION_NAME}]\n"
        ),
        0,
        True,
    ),
)
ids_config_settings_read = (
    "Incorrect section title. Expecting tool.config-settings",
    "Has section 2 keys",
    "Has section 0 keys",
)


@pytest.mark.parametrize(
    "toml_contents, section_key_count, has_log_warning",
    testdata_config_settings_read,
    ids=ids_config_settings_read,
)
def test_config_settings_read(
    toml_contents,
    section_key_count,
    has_log_warning,
    tmp_path,
    caplog,
    has_logging_occurred,
):
    """Test ConfigSettings read."""
    # pytest --showlocals --log-level INFO -k "test_get_config_settings" tests
    LOGGING["loggers"][g_app_name]["propagate"] = True
    logging.config.dictConfig(LOGGING)
    logger = logging.getLogger(name=g_app_name)
    logger.addHandler(hdlr=caplog.handler)
    caplog.handler.level = logger.level

    # prepare
    cs = ConfigSettings()
    cs.write(tmp_path, toml_contents)

    path_toml = tmp_path.joinpath(ConfigSettings.FILE_NAME_DEFAULT)
    assert path_toml.exists() and path_toml.is_file()

    ConfigSettings.set_abs_path(path_toml)

    # act
    cs = ConfigSettings()
    d_section = cs.read()
    actual_count = len(d_section.keys())
    assert actual_count == section_key_count

    if has_log_warning:
        assert has_logging_occurred(caplog)


@pytest.mark.parametrize(
    "toml_contents, section_key_count, has_log_warning",
    testdata_config_settings_read,
    ids=ids_config_settings_read,
)
def test_config_settings_set_abs_path(
    toml_contents,
    section_key_count,
    has_log_warning,
    tmp_path,
    caplog,
    has_logging_occurred,
):
    """Test ConfigSettings set_abs_path."""
    # pytest --showlocals --log-level INFO -k "test_get_config_settings" tests
    # prepare
    ConfigSettings.remove_abs_path()

    path_toml = tmp_path.joinpath(ConfigSettings.FILE_NAME_DEFAULT)
    path_toml.write_text(toml_contents)
    assert path_toml.exists() and path_toml.is_file()

    toml_path = str(path_toml)

    invalids = (
        None,
        0.1234,
    )
    for invalid in invalids:
        ConfigSettings.set_abs_path(invalid)
        assert ConfigSettings.get_abs_path() is None

    valids = (path_toml, str(path_toml))
    for valid in valids:
        ConfigSettings.set_abs_path(valid)
        assert ConfigSettings.get_abs_path() == toml_path
