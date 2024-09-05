"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

Unit test -- Module

.. code-block:: shell

   python -m coverage run --source='drain_swamp.monkey.config_settings' -m pytest \
   --showlocals tests/test_config_settings.py && coverage report \
   --data-file=.coverage --include="**/monkey/config_settings.py"

Integration test

.. code-block:: shell

   make coverage
   pytest --showlocals --cov="drain_swamp" --cov-report=term-missing \
   --cov-config=pyproject.toml tests

"""

from collections.abc import Mapping

import pytest

from drain_swamp.monkey.config_settings import ConfigSettings

testdata_config_settings_malformed = (
    (
        (
            "[project]\n"
            """name = "great-package"\n"""
            """version = "99.99.99a1.dev6"\n"""
            "[tool.config-settings]\n"
            """kind="current"\n"""
            """set-lock="1"\n"""
            """snip-co={}\n\n"""
        ),
        "my_snippet_co",
        0,
    ),
)
ids_config_settings_malformed = ("Missing double quotes surroundeding snip-co",)


@pytest.mark.parametrize(
    "toml_contents, snippet_co, expected_count",
    testdata_config_settings_malformed,
    ids=ids_config_settings_malformed,
)
def test_config_settings_malformed(
    toml_contents,
    snippet_co,
    expected_count,
    tmp_path,
):
    """Malformed config_settings."""
    # pytest --showlocals --log-level INFO -k "test_config_settings_malformed" tests
    # prepare
    #    snippet contents
    contents = toml_contents.format(snippet_co)

    # act
    d_section = ConfigSettings.get_section_dict(tmp_path, contents)

    # verify
    assert isinstance(d_section, Mapping)
    key_count_actual = len(d_section.keys())
    assert key_count_actual == expected_count
