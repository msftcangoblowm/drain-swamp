"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

.. code-block:: shell

   pytest --showlocals --log-level INFO tests/test_snippet_sphinx_conf.py
   pytest --showlocals --cov="drain_swamp" --cov-report=term-missing tests/test_snippet_sphinx_conf.py

Needs a config file to specify exact files to include / omit from report.
Will fail with exit code 1 even with 100% coverage

"""

import subprocess
from datetime import datetime
from pathlib import (
    Path,
    PurePath,
)
from unittest.mock import patch

import pytest

from drain_swamp.constants import g_app_name
from drain_swamp.snippet_sphinx_conf import SnipSphinxConf

testdata_snip_sphinx_conf_init = (
    pytest.param(None, marks=pytest.mark.xfail(raises=NotADirectoryError)),
    pytest.param("doc", marks=pytest.mark.xfail(raises=FileNotFoundError)),
    pytest.param("docs", marks=pytest.mark.xfail(raises=FileNotFoundError)),
)
ids_snip_sphinx_conf_init = (
    "No doc/ or docs/ sub-folder",
    "doc/ sub-folder",
    "docs/ sub-folder",
)


@pytest.mark.parametrize(
    "a_folder",
    testdata_snip_sphinx_conf_init,
    ids=ids_snip_sphinx_conf_init,
)
def test_snip_sphinx_conf_init(a_folder, tmp_path):
    """Sphinx [sub-folder]/conf.py does not exist exceptions"""
    if a_folder is not None and isinstance(a_folder, str):
        path_docs = tmp_path.joinpath(a_folder)
        path_docs.mkdir()

    SnipSphinxConf(path=tmp_path)


testdata_now_to_str = (
    pytest.param(None, marks=pytest.mark.xfail(raises=TypeError)),
    pytest.param(1.2345, marks=pytest.mark.xfail(raises=TypeError)),
)
ids_now_to_str = (
    "None",
    "float",
)


@pytest.mark.parametrize(
    "format_str",
    testdata_now_to_str,
    ids=ids_now_to_str,
)
def test_now_to_str(format_str, path_project_base):
    assert isinstance(SnipSphinxConf.now(), datetime)
    # strftime / strptime format str
    SnipSphinxConf.now_to_str(format_str)


def test_snip_sphinx_conf_properties(path_project_base):
    sc = SnipSphinxConf(path=path_project_base)

    # SnipSphinxConf.now getter
    assert isinstance(SnipSphinxConf.now(), datetime)

    assert issubclass(type(sc.path_abs), PurePath)

    # SnipSphinxConf.path_abs getter
    #     contains a ``conf.py`` file
    assert sc.path_abs.exists() and sc.path_abs.is_file()

    # SnipSphinxConf.path_cwd getter
    doc_folders = list(sc.path_cwd.glob("doc?"))
    doc_folder_count = len(doc_folders)
    assert doc_folder_count == 1

    assert sc.SV is None
    assert sc.author_name_left is None


test_data_contents = (
    ("0.0.1", g_app_name, "1850", "0.0.1"),
    ("now", g_app_name, "1850", "0.0.1"),
    ("current", g_app_name, "1850", "0.0.1"),
    ("tag", g_app_name, "1850", "0.0.1"),
)
ids_data_contents = (
    "kind -- explicit version str",
    "kind -- current alias",
    "kind -- current",
    "kind -- tag, fallback current",
)


@pytest.mark.parametrize(
    "kind, package_name, copyright_start_year, sem_version_str",
    test_data_contents,
    ids=ids_data_contents,
)
def test_snip_sphinx_conf_contents(
    kind,
    package_name,
    copyright_start_year,
    sem_version_str,
    path_project_base,
):
    cmd = []
    sc = SnipSphinxConf(path=path_project_base)

    # properties; defang so doesn't change src/[proj name]/_version.py
    with (
        patch(
            "subprocess.run",
            return_value=subprocess.CompletedProcess(
                cmd,
                returncode=0,
                stdout=sem_version_str,
            ),
        ),
    ):
        sc.contents(
            kind,
            package_name,
            copyright_start_year,
        )
        actual = sc._contents

        assert actual is not None
        assert isinstance(actual, str)

        # From package metadata
        assert "Dave Faulkmore" in actual

        # Has and sets these Sphinx variables
        assert """copyright = \"""" in actual
        #    xyz version
        assert """version = \"""" in actual
        #    semantic version
        assert """release = \"""" in actual
        #    Terse datetime str intended for display
        assert """release_date = \"""" in actual

    # Could not get project name from git --> AssertionError
    """
    if kind == "tag":
        with (
            patch(
                f"{g_app_name}.version_semantic._get_app_name",
                side_effect=AssertionError,
            ),
            patch(
                "subprocess.run",
                return_value=subprocess.CompletedProcess(
                    cmd,
                    returncode=128,
                    stdout="",
                    stderr="fatal: No names found, cannot describe anything.",
                ),
            ),
            pytest.raises(AssertionError),
        ):
            sc.contents(
                kind,
                package_name,
                copyright_start_year,
            )
    """
    pass

    # Explicit version str bad --> ValueError
    kind = "nowhere boys alternative universe police state that knows about magic"
    with pytest.raises(ValueError):
        sc.contents(
            kind,
            package_name,
            copyright_start_year,
        )


testdata_snip_sphinx_conf_replace = (
    (
        Path(__file__).parent.joinpath(
            "test_snip",
            "test_snip_harden_one_snip__with_id_.txt",
        ),
        "0.0.1",
        g_app_name,
        "1850",
        "asdf",
        """zzzzzzzzzzzzz
# @@@ editable {}
{}
# @@@ end
zzzzzzzzzzzzz""",
    ),
)
ids_snip_sphinx_conf_replace = ("replace compare against template",)


@pytest.mark.parametrize(
    "path_example, kind, package_name, copyright_start_year, id_, skeleton",
    testdata_snip_sphinx_conf_replace,
    ids=ids_snip_sphinx_conf_replace,
)
def test_snip_sphinx_conf_replace(
    path_example,
    kind,
    package_name,
    copyright_start_year,
    id_,
    skeleton,
    tmp_path,
):
    path_dir = tmp_path.joinpath("docs")
    path_dir.mkdir()

    contents_orig = path_example.read_text()

    path_file = path_dir.joinpath("conf.py")
    path_file.write_text(contents_orig)

    sc = SnipSphinxConf(path=tmp_path)
    assert sc.path_abs == path_file

    cmd = []

    with (
        patch(
            "subprocess.run",
            return_value=subprocess.CompletedProcess(
                cmd,
                returncode=0,
                stdout=kind,
            ),
        ),
    ):
        sc.contents(
            kind,
            package_name,
            copyright_start_year,
        )
        contents = sc._contents

    expected = skeleton.format(id_, contents.rstrip())

    sc.replace(snippet_co=id_)
    actual = sc.path_abs.read_text()

    assert expected.rstrip() == actual.rstrip()
