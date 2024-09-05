"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

Unit test -- Module

.. code-block:: shell

   python -m coverage run --source='drain_swamp.monkey.patch_pyproject_reading' -m pytest \
   --showlocals tests/test_patch_pyproject_reading.py && coverage report \
   --data-file=.coverage --include="**/monkey/patch_pyproject_reading.py"

Integration test

.. code-block:: shell

   make coverage
   pytest --showlocals --cov="drain_swamp" --cov-report=term-missing \
   --cov-config=pyproject.toml tests

"""

from contextlib import nullcontext as does_not_raise
from pathlib import (
    Path,
    PurePath,
)

import pytest

from drain_swamp.monkey.patch_pyproject_reading import (
    PyProjectData,
    ReadPyproject,
    ReadPyprojectStrict,
)

testdata_pyproject_data = (
    (
        "hope",
        {},
        {"name": "bob"},
        "bob",
    ),
)
ids_pyproject_data = ("empty section, pyproject.toml contains only name",)


@pytest.mark.parametrize(
    "tool_name, section, project, expected",
    testdata_pyproject_data,
    ids=ids_pyproject_data,
)
def test_pyproject_data(tool_name, section, expected, project, tmp_path):
    """From pyproject.toml confirm can get project name."""
    data = PyProjectData(tmp_path, tool_name, project, section)
    assert data.project_name == expected


testdata_read_pyproject = (
    (
        Path(__file__).parent.joinpath(
            "_good_files",
            "complete-manage-pip-prod-unlock.pyproject_toml",
        ),
        "drain-swamp",
        "drain-swamp",
    ),
    (
        Path(__file__).parent.joinpath(
            "_good_files",
            "complete-manage-pip-prod-unlock.pyproject_toml",
        ),
        ("drain-swamp", "pipenv-unlock"),
        "drain-swamp",
    ),
)
ids_read_pyproject = (
    "tool_name str",
    "tool_name Sequence[str]",
)


@pytest.mark.parametrize(
    "p_toml_file, tool_name, expected_tool_name",
    testdata_read_pyproject,
    ids=ids_read_pyproject,
)
def test_read_pyproject(
    p_toml_file, tool_name, expected_tool_name, tmp_path, prep_pyproject_toml
):
    """Call ReadPyproject __call__. Pass in kwargs."""
    # prepare
    prep_pyproject_toml(p_toml_file, tmp_path)

    data = ReadPyproject()(path=p_toml_file, tool_name=tool_name)
    assert issubclass(type(data.path), PurePath)
    assert isinstance(data.tool_name, str)
    assert isinstance(data.section, dict)
    assert isinstance(data.project, dict)
    assert data.path == p_toml_file
    assert data.tool_name == expected_tool_name


testdata_read_pyproject_exception = (
    (
        "Bob",
        Path(__file__).parent.joinpath(
            "_good_files",
            "full-course-meal-and-shower.pyproject_toml",
        ),
        pytest.raises(LookupError),
        False,
        False,
    ),
    (
        "Bob",
        Path(__file__).parent.joinpath(
            "_good_files",
            "complete-manage-pip-prod-unlock.pyproject_toml",
        ),
        pytest.raises(LookupError),
        False,
        False,
    ),
    (
        "pipenv-unlock",
        Path(__file__).parent.joinpath(
            "_good_files",
            "complete-manage-pip-prod-unlock.pyproject_toml",
        ),
        does_not_raise(),
        True,
        False,
    ),
    (
        ["drain-swamp", "pipenv-unlock"],
        Path(__file__).parent.joinpath(
            "_good_files",
            "complete-manage-pip-prod-unlock.pyproject_toml",
        ),
        does_not_raise(),
        True,
        True,
    ),
)
ids_read_pyproject_exception = (
    "Nonexistant pyproject.toml",
    "No such section [tool.Bob]",
    "str",
    "Sequence[str]",
)


@pytest.mark.parametrize(
    "tool_name, p_toml_file, expectation, in_keys_version_file, in_keys_copyright",
    testdata_read_pyproject_exception,
    ids=ids_read_pyproject_exception,
)
def test_read_pyproject_exception(
    tool_name,
    p_toml_file,
    expectation,
    in_keys_version_file,
    in_keys_copyright,
):
    """ReadPyproject __call__ exceptions."""
    # pytest --showlocals -vv --log-level INFO -k "test_read_pyproject_exception" tests
    with expectation:
        data_1 = ReadPyproject()(path=p_toml_file, tool_name=tool_name)
    if isinstance(expectation, does_not_raise):
        assert isinstance(data_1.project, dict)
        assert isinstance(data_1.section, dict)
        assert data_1.project_name == "complete-awesome-perfect"
        keys = data_1.section.keys()
        #    from section drain-swamp
        assert in_keys_copyright == ("copyright_start_year" in keys)
        #    from section pipenv-unlock
        assert in_keys_version_file == ("version_file" in keys)


def test_update_dict_strict():
    """Update a ReadPyprojectStrict dict."""
    # pytest --showlocals -vv --log-level INFO -k "test_update_dict_strict" tests
    d_a = {"root": "the root"}
    d_b = {"dist_name": "george"}
    ReadPyprojectStrict().update(d_a, d_b)
    assert "dist_name" in d_a.keys()
