"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

Shared testdata

Imported by test module ``tests/test_lock_inspect.py``
"""

from contextlib import nullcontext as does_not_raise
from pathlib import Path

import pytest

__all__ = (
    "testdata_resolve_resolvable_conflicts",
    "ids_resolve_resolvable_conflicts",
    "testdata_lock_compile_live",
    "ids_lock_compile_live",
)

testdata_resolve_resolvable_conflicts = (
    (
        Path(__file__).parent.joinpath(
            "_req_files",
            "constraints-conflicts.pyproject_toml",
        ),
        ".venv",
        (),
        (
            Path(__file__).parent.joinpath(
                "_req_files",
                "constraints-conflicts.unlock",
            ),
            Path(__file__).parent.joinpath(
                "_req_files",
                "constraints-conflicts.lock",
            ),
            Path(__file__).parent.joinpath(
                "_req_files",
                "constraints-various.unlock",
            ),
            Path(__file__).parent.joinpath(
                "_req_files",
                "constraints-various.lock",
            ),
            Path(__file__).parent.joinpath(
                "_req_files",
                "prod.shared.unlock",
            ),
            Path(__file__).parent.joinpath(
                "_req_files",
                "prod.shared.lock",
            ),
        ),
        6,
        1,
    ),
)
ids_resolve_resolvable_conflicts = ("resolve or issue warnings",)

testdata_lock_compile_live = (
    pytest.param(
        Path(__file__).parent.joinpath("_req_files", "venvs_minimal.pyproject_toml"),
        ".tools",
        (
            "requirements/pins.shared.in",
            "requirements/pip.in",
            "requirements/pip-tools.in",
            "docs/pip-tools.in",
        ),
        "docs/pip-tools.in",
        "docs/pip-tools.out",
        does_not_raise(),
    ),
    pytest.param(
        Path(__file__).parent.joinpath("_req_files", "venvs_minimal.pyproject_toml"),
        ".venv",
        (
            "requirements/pins.shared.in",
            "requirements/pip.in",
            "requirements/pip-tools.in",
            "docs/pip-tools.in",
        ),
        "requirements/pip-tools.in",
        "requirements/pip-tools.out",
        does_not_raise(),
    ),
)
ids_lock_compile_live = (
    "recipe for docs/pip-tools.in --> docs/pip-tools.lock",
    "recipe for requirements/pip-tools.in --> requirements/pip-tools.lock",
)
