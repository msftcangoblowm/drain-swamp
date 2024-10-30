"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

Shared testdata

Imported by test module ``tests/test_lock_inspect.py``
"""

from pathlib import Path

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

__all__ = (
    "testdata_resolve_resolvable_conflicts",
    "ids_resolve_resolvable_conflicts",
)
