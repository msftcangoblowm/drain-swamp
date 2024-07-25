"""
.. code-block:: shell

   pytest --showlocals --log-level INFO tests/test_wrap_infer_version.py
   pytest --showlocals --cov="drain_swamp" --cov-report=term-missing tests/test_wrap_infer_version.py

.. seealso::

   https://github.com/pypa/setuptools_scm/blob/main/testing/test_integration.py
   https://github.com/pypa/setuptools_scm/blob/main/testing/wd_wrapper.py

"""

import logging
import logging.config
import os
import subprocess
import sys
from pathlib import Path

import pytest

from drain_swamp.constants import (
    LOGGING,
    g_app_name,
)
from drain_swamp.monkey.wrap_infer_version import _get_config_settings

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


def test_dist_get_cmdline_options(
    prep_pyproject_toml,
    prepare_folders_files,
    caplog,
    has_logging_occurred,
    wd: WorkDir,
    monkeypatch: pytest.MonkeyPatch,
):
    """Can access command line options using Distribution.get_cmdline_options

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
    logger.info(f"sys.executable: {sys.executable}")
    kind = "0.2.1"
    app_name = "complete_awesome_perfect"
    f_name = f"{app_name}-{kind}.tar.gz"

    # prepare
    #    .gitignore
    msg_gitignore = (
        "dist/*.whl\n"
        "dist/*.tar.gz\n"
        "requirements/*.lnk\n"
        "src/*.egg-info/*\n"
        "src/*/_version.py\n"
        "setuptools-build.toml\n\n"
    )
    wd.write(".gitignore", msg_gitignore)

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
        """__version__ = version = '0.2.0'\n"""
        """__version_tuple__ = version_tuple = (0, 2, 0)\n\n"""
    )
    path_f = path_dir_dest.joinpath("_version.py")
    path_f.write_text(str_version_file)

    wd.add_and_commit()
    wd("git tag --no-sign -m 'plz' 0.2.0")

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
    toml_path = str(p_base.joinpath("setuptools-build.toml"))
    toml_contents = (
        "[project]\n"
        f"""name = "{app_name}"\n"""
        """version = "99.99.99a1.dev6"\n"""
        "[tool.config-settings]\n"
        f"""kind="{kind}"\n"""
        """set-lock="0"\n\n"""
    )
    Path(toml_path).write_text(toml_contents)

    # plugins: refresh_links (needs set-lock), cli_scm_version.py (needs kind)
    env = os.environ.copy()
    env |= {"DS_CONFIG_SETTINGS": toml_path}
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
    logger.info(f"DS_CONFIG_SETTINGS: {env.get('DS_CONFIG_SETTINGS')}")
    try:
        proc = subprocess.run(cmd, cwd=cwd, env=env)
    except subprocess.CalledProcessError as e:
        logger.warn(f"ERROR build failed code {e.returncode} {e.output}")
        raise
    else:
        # logger.info(f"proc.stdout {proc.stdout!r}")
        # proc.stderr(f"proc.stderr {proc.stderr!r}")
        assert has_logging_occurred(caplog)
        assert proc.returncode == 0
        path_dist_dir = cwd.joinpath("dist", f_name)
        assert path_dist_dir.exists()


testdata_get_config_settings = (
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
            "[tool.config-settings]\n"
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
            "[tool.config-settings]\n"
        ),
        0,
        True,
    ),
)
ids_get_config_settings = (
    "Incorrect section title. Expecting tool.config-settings",
    "Has section 2 keys",
    "Has section 0 keys",
)


@pytest.mark.parametrize(
    "toml_contents, section_key_count, has_log_warning",
    testdata_get_config_settings,
    ids=ids_get_config_settings,
)
def test_get_config_settings(
    toml_contents,
    section_key_count,
    has_log_warning,
    tmp_path,
    caplog,
    has_logging_occurred,
):
    # pytest --showlocals --log-level INFO -k "test_get_config_settings" tests
    LOGGING["loggers"][g_app_name]["propagate"] = True
    logging.config.dictConfig(LOGGING)
    logger = logging.getLogger(name=g_app_name)
    logger.addHandler(hdlr=caplog.handler)
    caplog.handler.level = logger.level

    # prepare
    path_toml = tmp_path.joinpath("setuptools-build.toml")
    path_toml.write_text(toml_contents)
    assert path_toml.exists() and path_toml.is_file()

    env_key = "DS_CONFIG_SETTINGS"
    toml_path = str(path_toml)
    os.environ[env_key] = toml_path
    assert os.environ.get(env_key) == toml_path

    # act
    d_section = _get_config_settings()
    actual_count = len(d_section.keys())
    assert actual_count == section_key_count

    if has_log_warning:
        assert has_logging_occurred(caplog)
