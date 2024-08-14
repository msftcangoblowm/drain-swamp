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
    ),
)
ids_config_settings_malformed = ("Missing double quotes surroundeding snip-co",)


@pytest.mark.parametrize(
    "toml_contents, snippet_co",
    testdata_config_settings_malformed,
    ids=ids_config_settings_malformed,
)
def test_config_settings_malformed(tmp_path, toml_contents, snippet_co):
    """malformed config_settings"""
    # pytest --showlocals --log-level INFO -k "test_config_settings_malformed" tests
    contents = toml_contents.format(snippet_co)
    d_section = ConfigSettings.get_section_dict(tmp_path, contents)
    assert isinstance(d_section, Mapping)
    assert len(d_section.keys()) == 0
