"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

Unittest for repr helper module

With coverage

.. code-block:: shell

   python -m coverage run --source='drain_swamp._repr' -m pytest \
   --showlocals tests/test_repr.py && coverage report \
   --data-file=.coverage --include="**/_repr.py"

Integration test

.. code-block:: shell

   make coverage
   pytest --showlocals --cov="drain_swamp" --cov-report=term-missing \
   --cov-config=pyproject.toml tests

"""

from contextlib import nullcontext as does_not_raise
from pathlib import PurePath
from typing import TYPE_CHECKING

import pytest

from drain_swamp._repr import (
    repr_dict_str_path,
    repr_path,
    repr_set_path,
)

if TYPE_CHECKING:
    from pathlib import Path

    from .typing_only import DOES_NOT_OR_DOES


@pytest.mark.parametrize(
    "key, path, is_last, expectation, has_comma",
    (
        pytest.param(
            "path_goodies",
            None,
            None,
            pytest.raises(TypeError),
            False,
            id="path-is-None--TypeError",
        ),
        pytest.param(
            "path_goodies",
            1.213,
            None,
            pytest.raises(TypeError),
            False,
            id="path-unsupported-type--TypeError",
        ),
        pytest.param(
            None,
            PurePath("/etc/passwd"),
            None,
            pytest.raises(TypeError),
            False,
            id="k-is-None--TypeError",
        ),
        pytest.param(
            1.213,
            PurePath("/etc/passwd"),
            None,
            pytest.raises(TypeError),
            False,
            id="k-is-unsupported-type--TypeError",
        ),
        pytest.param(
            "path_goodies",
            PurePath("/etc/passwd"),
            None,
            does_not_raise(),
            True,
            id="None--False--has-comma",
        ),
        pytest.param(
            "path_goodies",
            PurePath("/etc/passwd"),
            1.2345,
            does_not_raise(),
            True,
            id="Unsupported-type--False--has-comma",
        ),
        pytest.param(
            "path_goodies",
            PurePath("/etc/passwd"),
            False,
            does_not_raise(),
            True,
            id="False--has-comma",
        ),
        pytest.param(
            "path_goodies",
            PurePath("/etc/passwd"),
            True,
            does_not_raise(),
            False,
            id="True--no-comma",
        ),
    ),
)
def test_repr_path(
    key: str | float | None,
    path: "Path | float | None",
    is_last: bool | float | None,
    expectation: "DOES_NOT_OR_DOES",
    has_comma: bool,
) -> None:
    """Check repr_path exceptions.

    .. code-block:: shell

       pytest --showlocals --cov=drain_swamp --cov-report=term-missing \
       --cov-config=pyproject.toml -k test_repr_path tests

    .. seealso::

       from contextlib import nullcontext as does_not_raise
       https://docs.pytest.org/en/7.1.x/example/parametrize.html#parametrizing-conditional-raising

    """
    # pytest --showlocals --log-level INFO -k "test_repr_path" tests
    with expectation:
        out = repr_path(key, path, is_last=is_last)
    if isinstance(expectation, does_not_raise):
        end_token = ", "
        actual = out.endswith(end_token)
        assert actual == has_comma


@pytest.mark.parametrize(
    "key, set_0, is_last, expectation, has_comma",
    (
        pytest.param(
            "path_goodies",
            None,
            None,
            pytest.raises(TypeError),
            False,
            id="path-is-None--TypeError",
        ),
        pytest.param(
            "path_goodies",
            1.213,
            None,
            pytest.raises(TypeError),
            False,
            id="path-unsupported-type--TypeError",
        ),
        pytest.param(
            None,
            {
                PurePath("/etc/passwd"),
            },
            None,
            pytest.raises(TypeError),
            False,
            id="k-is-None--TypeError",
        ),
        pytest.param(
            1.213,
            {
                PurePath("/etc/passwd"),
            },
            None,
            pytest.raises(TypeError),
            False,
            id="k-is-unsupported-type--TypeError",
        ),
        pytest.param(
            "path_goodies",
            {
                PurePath("/etc/passwd"),
            },
            None,
            does_not_raise(),
            True,
            id="None--False--has-comma",
        ),
        pytest.param(
            "path_goodies",
            {
                PurePath("/etc/passwd"),
            },
            1.2345,
            does_not_raise(),
            True,
            id="Unsupported-type--False--has-comma",
        ),
        pytest.param(
            "path_goodies",
            {PurePath("/etc/passwd"), PurePath("/etc/skel/.bashrc")},
            False,
            does_not_raise(),
            True,
            id="False--has-comma",
        ),
        pytest.param(
            "path_goodies",
            {PurePath("/etc/passwd"), PurePath("/etc/skel/.bashrc")},
            True,
            does_not_raise(),
            False,
            id="True--no-comma",
        ),
    ),
)
def test_repr_set_path(
    key: str | None,
    set_0: "set[Path] | float | None",
    is_last: bool | float | None,
    expectation: "DOES_NOT_OR_DOES",
    has_comma: bool,
) -> None:
    """Given a set which contain Path, check produced repr lines."""
    # pytest --showlocals --log-level INFO -k "test_repr_set_path" tests
    with expectation:
        out = repr_set_path(key, set_0, is_last=is_last)

    if isinstance(expectation, does_not_raise):
        end_token = ", "
        actual = out.endswith(end_token)
        assert actual == has_comma


@pytest.mark.parametrize(
    "key, d_paths, is_last, expectation, has_comma",
    (
        pytest.param(
            "path_goodies",
            None,
            None,
            pytest.raises(TypeError),
            False,
            id="path-is-None--TypeError",
        ),
        pytest.param(
            "path_goodies",
            1.213,
            None,
            pytest.raises(TypeError),
            False,
            id="path-unsupported-type--TypeError",
        ),
        pytest.param(
            None,
            {"dev": PurePath("/etc/passwd")},
            None,
            pytest.raises(TypeError),
            False,
            id="k-is-None--TypeError",
        ),
        pytest.param(
            1.213,
            {"dev": PurePath("/etc/passwd")},
            None,
            pytest.raises(TypeError),
            False,
            id="k-is-unsupported-type--TypeError",
        ),
        pytest.param(
            "path_goodies",
            {"dev": PurePath("/etc/passwd")},
            None,
            does_not_raise(),
            True,
            id="None--False--has-comma",
        ),
        pytest.param(
            "path_goodies",
            {"dev": PurePath("/etc/passwd")},
            1.2345,
            does_not_raise(),
            True,
            id="Unsupported-type--False--has-comma",
        ),
        pytest.param(
            "path_goodies",
            {"dev": PurePath("/etc/passwd"), "prod": PurePath("/etc/skel/.bashrc")},
            False,
            does_not_raise(),
            True,
            id="False--has-comma",
        ),
        pytest.param(
            "path_goodies",
            {"dev": PurePath("/etc/passwd"), "prod": PurePath("/etc/skel/.bashrc")},
            True,
            does_not_raise(),
            False,
            id="True--no-comma",
        ),
    ),
)
def test_repr_dict_str_path(
    key: str | float | None,
    d_paths: "dict[str, Path] | float | None",
    is_last: bool | float | None,
    expectation: "DOES_NOT_OR_DOES",
    has_comma: bool,
) -> None:
    """Given a dict which has value Path, check produced repr lines."""
    # pytest --showlocals --log-level INFO -k "test_repr_dict_str_path" tests
    with expectation:
        out = repr_dict_str_path(
            key,  # type: ignore[arg-type]
            d_paths,  # type: ignore[arg-type]
            is_last=is_last,  # type: ignore[arg-type]
        )
    if isinstance(expectation, does_not_raise):
        end_token = ", "
        actual = out.endswith(end_token)
        assert actual == has_comma
