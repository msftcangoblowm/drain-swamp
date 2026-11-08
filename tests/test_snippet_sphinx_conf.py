"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

With coverage

.. code-block:: shell

   python -m coverage run --source='drain_swamp.snippet_sphinx_conf' -m pytest \
   --showlocals tests/test_snippet_sphinx_conf.py && coverage report \
   --data-file=.coverage --include="**/snippet_sphinx_conf.py"

Integration test

.. code-block:: shell

   make coverage
   pytest --showlocals --cov="drain_swamp" --cov-report=term-missing \
   --cov-config=pyproject.toml tests

"""

import subprocess
from contextlib import nullcontext as does_not_raise
from datetime import datetime
from pathlib import (
    Path,
    PurePath,
)
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

from drain_swamp.constants import g_app_name
from drain_swamp.snippet_sphinx_conf import SnipSphinxConf

if TYPE_CHECKING:
    from collections.abc import Callable

    from .typing_only import DOES_NOT_OR_DOES


@pytest.mark.parametrize(
    "a_folder, expectation",
    (
        pytest.param(
            None,
            pytest.raises(NotADirectoryError),
            id="No-doc-or-docs-sub-folder",
        ),
        pytest.param(
            "doc",
            pytest.raises(FileNotFoundError),
            id="doc-sub-folder",
        ),
        pytest.param(
            "docs",
            pytest.raises(FileNotFoundError),
            id="docs-sub-folder",
        ),
    ),
)
def test_snip_sphinx_conf_init(
    a_folder: str | None,
    expectation: "DOES_NOT_OR_DOES",
    tmp_path: "Path",
) -> None:
    """Sphinx [sub-folder]/conf.py does not exist exceptions."""
    # pytest --showlocals --log-level INFO -k "test_snip_sphinx_conf_init" tests
    if a_folder is not None and isinstance(a_folder, str):
        path_docs = tmp_path.joinpath(a_folder)
        path_docs.mkdir()

    with expectation:
        SnipSphinxConf(path=tmp_path)


@pytest.mark.parametrize(
    "format_str, expectation",
    (
        pytest.param(
            None,
            pytest.raises(TypeError),
            id="None",
        ),
        pytest.param(
            1.2345,
            pytest.raises(TypeError),
            id="float",
        ),
        pytest.param(
            "%T",
            does_not_raise(),
            id="Windows-issue.-Aggregate-equivalent-to-%H:%M:%S",
        ),
        pytest.param(
            "%D",
            does_not_raise(),
            id="MacOS-issue.-Aggregate-equivalent-to-%m/%d/%Y",
        ),
        pytest.param(
            "%-d",
            does_not_raise(),
            id="Linux-flavor-only.-Day-without-leading-zero",
        ),
    ),
)
def test_now_to_str(
    format_str: str | float | None,
    expectation: "DOES_NOT_OR_DOES",
    path_project_base: "Callable[[], Path]",
) -> None:
    """Test now_to_str. Patched, so should never fail."""
    # pytest --showlocals --log-level INFO -k "test_now_to_str" tests
    assert isinstance(SnipSphinxConf.now(), datetime)
    # strftime / strptime format str
    with expectation:
        SnipSphinxConf.now_to_str(
            format_str,  # type: ignore[arg-type]
        )


@pytest.mark.parametrize(
    "dodgy, expectation",
    (
        pytest.param(
            "%T",
            does_not_raise(),
            id="Windows-issue",
        ),
        pytest.param(
            "%D",
            does_not_raise(),
            id="MacOS-issue",
        ),
        pytest.param(
            "%-d",
            does_not_raise(),
            id="linux-only-flavor",
        ),
    ),
)
def test_now_to_str_split(
    dodgy: str,
    expectation: "DOES_NOT_OR_DOES",
) -> None:
    """Test now_to_str_split."""
    # pytest --showlocals --log-level INFO -k "test_now_to_str_split" tests
    assert isinstance(SnipSphinxConf.now(), datetime)
    with expectation:
        assert isinstance(SnipSphinxConf.now_to_str(dodgy), str)


def test_snip_sphinx_conf_properties(
    path_project_base: "Callable[[], Path]",
) -> None:
    """SnipSphinxConf properties."""
    # pytest --showlocals --log-level INFO -k "test_snip_sphinx_conf_properties" tests
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


@pytest.mark.parametrize(
    "kind, package_name, copyright_start_year, sem_version_str",
    (
        pytest.param(
            "0.0.1",
            g_app_name,
            "1850",
            "0.0.1",
            id="kind--explicit-version-str",
        ),
        pytest.param(
            "now",
            g_app_name,
            "1850",
            "0.0.1",
            id="kind--current-alias",
        ),
        pytest.param(
            "current",
            g_app_name,
            "1850",
            "0.0.1",
            id="kind--current",
        ),
        pytest.param(
            "tag",
            g_app_name,
            "1850",
            "0.0.1",
            id="kind--tag,-fallback-current",
        ),
    ),
)
def test_snip_sphinx_conf_contents(
    kind: str,
    package_name: str,
    copyright_start_year: str,
    sem_version_str: str,
    path_project_base: "Callable[[], Path]",
) -> None:
    """Test SnipSphinxConf.contents."""
    # pytest --showlocals --log-level INFO -k "test_snip_sphinx_conf_contents" tests
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

    # Explicit version str bad --> ValueError
    kind = "nowhere boys alternative universe police state that knows about magic"
    with pytest.raises(ValueError):
        sc.contents(
            kind,
            package_name,
            copyright_start_year,
        )


@pytest.mark.parametrize(
    "relpath_example, kind, package_name, copyright_start_year, id_, skeleton",
    (
        pytest.param(
            Path("_good_snips").joinpath("test_snip_harden_one_snip__with_id_.txt"),
            "0.0.1",
            g_app_name,
            "1850",
            "asdf",
            """zzzzzzzzzzzzz
# @@@ editable {}
{}
# @@@ end
zzzzzzzzzzzzz""",
            id="replace-compare-against-template",
        ),
    ),
)
def test_snip_sphinx_conf_replace(
    relpath_example: "Path",
    kind: str,
    package_name: str,
    copyright_start_year: str,
    id_: str,
    skeleton: str,
    tmp_path: "Path",
    request: pytest.FixtureRequest,
) -> None:
    """Test SnipSphinxConf.replace."""
    # pytest --showlocals --log-level INFO -k "test_snip_sphinx_conf_replace" tests
    abspath_tests_dir = request.path.parent
    abspath_example = abspath_tests_dir.joinpath(relpath_example)

    path_dir = tmp_path.joinpath("docs")
    path_dir.mkdir()

    contents_orig = abspath_example.read_text()

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
