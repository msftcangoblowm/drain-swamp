"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

.. code-block:: shell

   pytest --showlocals --log-level INFO tests/test_patch_pyproject_reading.py
   pytest --showlocals --cov="drain_swamp" --cov-report=term-missing tests/test_patch_pyproject_reading.py

"""

from pathlib import (
    Path,
    PurePath,
)

import pytest

from drain_swamp.monkey.patch_pyproject_reading import (
    PyProjectData,
    ReadPyproject,
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
    "From pyproject.toml confirm can get project name"
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
    # prepare
    prep_pyproject_toml(p_toml_file, tmp_path)

    data = ReadPyproject()(path=p_toml_file, tool_name=tool_name)
    assert issubclass(type(data.path), PurePath)
    assert isinstance(data.tool_name, str)
    assert isinstance(data.section, dict)
    assert isinstance(data.project, dict)
    assert data.path == p_toml_file
    assert data.tool_name == expected_tool_name


def test_read_pyproject_exception(tmp_path):
    # No pyproject.toml file and no such section
    tool_name = "Bob"
    p_toml_file = tmp_path.joinpath("pyproject.toml")
    with pytest.raises(LookupError):
        ReadPyproject()(path=p_toml_file, tool_name=tool_name)

    # no [tool.Bob] section
    p_toml_file = Path(__file__).parent.joinpath(
        "_good_files",
        "complete-manage-pip-prod-unlock.pyproject_toml",
    )
    with pytest.raises(LookupError):
        ReadPyproject()(path=p_toml_file, tool_name=tool_name)

    # str
    tool_name = "pipenv-unlock"
    data_0 = ReadPyproject()(path=p_toml_file, tool_name=tool_name)
    assert isinstance(data_0.project, dict)
    assert isinstance(data_0.section, dict)
    assert data_0.project_name == "complete-awesome-perfect"
    #    from section drain-swamp
    assert "copyright_start_year" not in data_0.section.keys()
    #    from section pipenv-unlock
    assert "version_file" in data_0.section.keys()

    # # Sequence[str]
    tool_name = ["drain-swamp", "pipenv-unlock"]
    data_1 = ReadPyproject()(path=p_toml_file, tool_name=tool_name)
    assert isinstance(data_1.project, dict)
    assert isinstance(data_1.section, dict)
    assert data_1.project_name == "complete-awesome-perfect"
    #    from section drain-swamp
    assert "copyright_start_year" in data_1.section.keys()
    #    from section pipenv-unlock
    assert "version_file" in data_1.section.keys()
