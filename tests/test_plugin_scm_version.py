"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

Unit test -- Module

.. code-block:: shell

   python -m coverage run \
   --source='drain_swamp.monkey.plugins.ds_scm_version' -m pytest \
   --showlocals tests/test_plugin_scm_version.py && coverage report \
   --data-file=.coverage --include="**/monkey/plugins/ds_scm_version.py"

Integration test

.. code-block:: shell

   make coverage
   pytest --showlocals --cov="drain_swamp" --cov-report=term-missing \
   --cov-config=pyproject.toml tests

"""

import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from drain_swamp.monkey.config_settings import ConfigSettings
from drain_swamp.monkey.plugins.ds_scm_version import (
    _kind,
    on_version_infer,
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


testdata_kind_arg_filter_normal = (
    (
        (
            "[project]\n"
            """name = "great-package"\n"""
            """version = "99.99.99a1.dev6"\n"""
            "[tool.config-settings]\n"
            """kind="current"\n"""
            """set-lock="0"\n\n"""
        ),
        "tag",
        "current",
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
        None,
        "current",
    ),
    (
        (
            "[project]\n"
            """name = "great-package"\n"""
            """version = "99.99.99a1.dev6"\n"""
            "[tool.config-settings]\n"
        ),
        "tag",
        "tag",
    ),
)
ids_kind_arg_filter_normal = (
    "kind current fallback tag",
    "kind current fallback None",
    "no kind",
)


@pytest.mark.parametrize(
    "toml_contents, fallback, expected_kind",
    testdata_kind_arg_filter_normal,
    ids=ids_kind_arg_filter_normal,
)
def test_kind_arg_filter_normal(toml_contents, fallback, expected_kind, tmp_path):
    """Test _kind."""
    # pytest --showlocals --log-level INFO -k "test_kind_arg_filter_normal" tests
    # d_section not a dict
    invalids = (
        None,
        1.2,
    )
    for invalid in invalids:
        fallback_clean = fallback if fallback is not None else "tag"
        actual_kind = _kind(invalid, fallback=fallback_clean)
        assert actual_kind == fallback_clean

    d_section = ConfigSettings.get_section_dict(tmp_path, toml_contents)
    actual_kind = _kind(d_section, fallback=fallback)
    assert actual_kind == expected_kind

    # not used thru :code:`python -m build`
    d_section = {"--kind": "0.0.1"}
    actual_kind = _kind(d_section, fallback=fallback)
    assert actual_kind == "0.0.1"


testdata_kind_arg_filter_whitespace = (
    (
        (
            "[project]\n"
            """name = "great-package"\n"""
            """version = "99.99.99a1.dev6"\n"""
            "[tool.config-settings]\n"
            """kind="   "\n"""
            """set-lock="0"\n\n"""
        ),
        "nonsense",
        "nonsense",
    ),
    (
        (
            "[project]\n"
            """name = "great-package"\n"""
            """version = "99.99.99a1.dev6"\n"""
            "[tool.config-settings]\n"
            """kind=""\n"""
            """set-lock="0"\n\n"""
        ),
        "nonsense",
        "nonsense",
    ),
)
ids_kind_arg_filter_whitespace = (
    "kind is just whitespace --> fallback",
    "kind is empty --> fallback",
)


@pytest.mark.parametrize(
    "toml_contents, fallback, expected_kind",
    testdata_kind_arg_filter_whitespace,
    ids=ids_kind_arg_filter_whitespace,
)
def test_kind_arg_filter_whitespace(toml_contents, fallback, expected_kind, tmp_path):
    """Test _kind expected user warning."""
    # pytest --showlocals --log-level INFO -k "test_kind_arg_filter_whitespace" tests
    d_section = ConfigSettings.get_section_dict(tmp_path, toml_contents)
    with pytest.warns(UserWarning) as record:
        actual_kind = _kind(d_section, fallback=fallback)
        warn_msg_expected = (
            "-C--kind expected to be: tag, current, now, or a version str. Got"
        )
        warn_msg = str(record[0].message)
        assert isinstance(warn_msg, str)
        assert warn_msg.startswith(warn_msg_expected)
        assert actual_kind == expected_kind


def test_on_version_infer(
    wd: WorkDir,
    prep_pyproject_toml,
    prepare_folders_files,
):
    """Test on_version_infer."""
    # pytest --showlocals --log-level INFO -k "test_on_version_infer" tests
    # tag. Does not modify the version file
    kind = "tag"
    d_config_settings = {"kind": "tag"}
    actual = on_version_infer(d_config_settings)
    assert actual is None

    # if drain swamp not installed, could only test against drain_swamp package
    pass

    # current now and version str acts modifies a package, so act against a fake package
    # test_wrap_infer_version.py creates a fake package environment

    # prepare
    app_name = "complete_awesome_perfect"

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
    path_pyproject_toml = prep_pyproject_toml(p_toml_file, wd.cwd)

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
    #    monkeypatch.chdir(p_package_base)

    # act
    kinds = (
        "now",
        "current",
        "0.2.1.dev4",
    )
    with patch(
        "drain_swamp._run_cmd.Path.cwd",
        return_value=wd.cwd,
    ):
        if not path_pyproject_toml.exists():
            prep_pyproject_toml(p_toml_file, wd.cwd)
            assert path_pyproject_toml.exists()

        # valids
        for kind in kinds:
            d_config_settings = {"kind": kind}
            actual_msg = on_version_infer(d_config_settings)
            # msg is none if no error occurred
            assert actual_msg is None

        # invalid semantic str. Should not be able to write
        # [venv bin path]/scm-version write "golf balls are not good eating"
        invalids = (
            "golf balls are not good eating",
            "   ",
            "",
        )
        for invalid in invalids:
            d_config_settings = {"kind": invalid}
            actual_golf_balls = on_version_infer(d_config_settings)
            assert actual_golf_balls is not None
            assert isinstance(actual_golf_balls, str)

        """error during subprocess call to :code:`scm-version get` or
        :code:`scm-version write`. Reason timeout too slow"""
        with (
            patch(
                "drain_swamp._run_cmd.subprocess.run",
                side_effect=subprocess.TimeoutExpired(
                    cmd=["the", "cmd"],
                    timeout=1,
                    output=None,
                    stderr="go faster next time",
                ),
            ),
            pytest.warns() as record,
        ):
            d_config_settings = {"kind": kind}
            actual_msg = on_version_infer(d_config_settings)
            assert actual_msg is None
            str_warn = str(record[0].message)
            assert str_warn is not None
            assert isinstance(str_warn, str)

        # kind==current. scm-version get cause error
        kind_cause_error = "current"
        code = 3
        cmd = ["scm-version", "get", "--is-write"]
        stderr = "not blank means subprocess call failed"
        with (
            patch(
                "drain_swamp._run_cmd.subprocess.run",
                side_effect=subprocess.CalledProcessError(
                    code,
                    cmd,
                    output=None,
                    stderr=stderr,
                ),
            ),
            pytest.warns() as record,
        ):
            d_config_settings = {"kind": kind_cause_error}
            actual_msg = on_version_infer(d_config_settings)
            assert actual_msg is None
            str_warn = str(record[0].message)
            assert str_warn is not None
            assert isinstance(str_warn, str)

        # Cause LookupError in subprocess by removing the pyproject.toml file
        path_pyproject_toml.unlink()
        assert not path_pyproject_toml.exists()
        for kind in kinds:
            d_config_settings = {"kind": kind}
            actual_msg = on_version_infer(d_config_settings)
            assert actual_msg is not None
            assert isinstance(actual_msg, str)
