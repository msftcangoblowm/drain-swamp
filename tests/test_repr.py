"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

..

Unittest for repr helper module

Unit test -- Module

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

import pytest

from drain_swamp._repr import (
    repr_dict_str_path,
    repr_path,
    repr_set_path,
)

testdata_repr_path = (
    (
        "path_goodies",
        None,
        None,
        pytest.raises(TypeError),
        False,
    ),
    (
        "path_goodies",
        1.213,
        None,
        pytest.raises(TypeError),
        False,
    ),
    (
        None,
        PurePath("/etc/passwd"),
        None,
        pytest.raises(TypeError),
        False,
    ),
    (
        1.213,
        PurePath("/etc/passwd"),
        None,
        pytest.raises(TypeError),
        False,
    ),
    (
        "path_goodies",
        PurePath("/etc/passwd"),
        None,
        does_not_raise(),
        True,
    ),
    (
        "path_goodies",
        PurePath("/etc/passwd"),
        1.2345,
        does_not_raise(),
        True,
    ),
    (
        "path_goodies",
        PurePath("/etc/passwd"),
        False,
        does_not_raise(),
        True,
    ),
    (
        "path_goodies",
        PurePath("/etc/passwd"),
        True,
        does_not_raise(),
        False,
    ),
)
ids_repr_path = (
    "path is None --> TypeError",
    "path unsupported type --> TypeError",
    "k is None --> TypeError",
    "k is unsupported type --> TypeError",
    "None --> False --> has comma",
    "Unsupported type --> False --> has comma",
    "False --> has comma",
    "True --> no comma",
)


@pytest.mark.parametrize(
    "key, path, is_last, exceptation, has_comma",
    testdata_repr_path,
    ids=ids_repr_path,
)
def test_repr_path(key, path, is_last, exceptation, has_comma):
    """Check repr_path exceptions.

    .. code-block:: shell

       pytest --showlocals --cov=drain_swamp --cov-report=term-missing \
       --cov-config=pyproject.toml -k test_repr_path tests

    .. seealso::

       from contextlib import nullcontext as does_not_raise
       https://docs.pytest.org/en/7.1.x/example/parametrize.html#parametrizing-conditional-raising

    """
    # pytest --showlocals --log-level INFO -k "test_repr_path" tests
    with exceptation:
        out = repr_path(key, path, is_last=is_last)

    if isinstance(exceptation, does_not_raise):
        end_token = ", "
        actual = out.endswith(end_token)
        assert actual == has_comma


testdata_repr_set_path = (
    (
        "path_goodies",
        None,
        None,
        pytest.raises(TypeError),
        False,
    ),
    (
        "path_goodies",
        1.213,
        None,
        pytest.raises(TypeError),
        False,
    ),
    (
        None,
        {
            PurePath("/etc/passwd"),
        },
        None,
        pytest.raises(TypeError),
        False,
    ),
    (
        1.213,
        {
            PurePath("/etc/passwd"),
        },
        None,
        pytest.raises(TypeError),
        False,
    ),
    (
        "path_goodies",
        {
            PurePath("/etc/passwd"),
        },
        None,
        does_not_raise(),
        True,
    ),
    (
        "path_goodies",
        {
            PurePath("/etc/passwd"),
        },
        1.2345,
        does_not_raise(),
        True,
    ),
    (
        "path_goodies",
        {PurePath("/etc/passwd"), PurePath("/etc/skel/.bashrc")},
        False,
        does_not_raise(),
        True,
    ),
    (
        "path_goodies",
        {PurePath("/etc/passwd"), PurePath("/etc/skel/.bashrc")},
        True,
        does_not_raise(),
        False,
    ),
)


@pytest.mark.parametrize(
    "key, set_0, is_last, exceptation, has_comma",
    testdata_repr_set_path,
    ids=ids_repr_path,
)
def test_repr_set_path(key, set_0, is_last, exceptation, has_comma):
    """Given a set which contain Path, check produced repr lines."""
    # pytest --showlocals --log-level INFO -k "test_repr_set_path" tests
    with exceptation:
        out = repr_set_path(key, set_0, is_last=is_last)

    if isinstance(exceptation, does_not_raise):
        end_token = ", "
        actual = out.endswith(end_token)
        assert actual == has_comma


testdata_repr_dict_str_path = (
    (
        "path_goodies",
        None,
        None,
        pytest.raises(TypeError),
        False,
    ),
    (
        "path_goodies",
        1.213,
        None,
        pytest.raises(TypeError),
        False,
    ),
    (
        None,
        {"dev": PurePath("/etc/passwd")},
        None,
        pytest.raises(TypeError),
        False,
    ),
    (
        1.213,
        {"dev": PurePath("/etc/passwd")},
        None,
        pytest.raises(TypeError),
        False,
    ),
    (
        "path_goodies",
        {"dev": PurePath("/etc/passwd")},
        None,
        does_not_raise(),
        True,
    ),
    (
        "path_goodies",
        {"dev": PurePath("/etc/passwd")},
        1.2345,
        does_not_raise(),
        True,
    ),
    (
        "path_goodies",
        {"dev": PurePath("/etc/passwd"), "prod": PurePath("/etc/skel/.bashrc")},
        False,
        does_not_raise(),
        True,
    ),
    (
        "path_goodies",
        {"dev": PurePath("/etc/passwd"), "prod": PurePath("/etc/skel/.bashrc")},
        True,
        does_not_raise(),
        False,
    ),
)


@pytest.mark.parametrize(
    "key, d_paths, is_last, exceptation, has_comma",
    testdata_repr_dict_str_path,
    ids=ids_repr_path,
)
def test_repr_dict_str_path(key, d_paths, is_last, exceptation, has_comma):
    """Given a dict which has value Path, check produced repr lines."""
    # pytest --showlocals --log-level INFO -k "test_repr_dict_str_path" tests
    with exceptation:
        out = repr_dict_str_path(key, d_paths, is_last=is_last)

    if isinstance(exceptation, does_not_raise):
        end_token = ", "
        actual = out.endswith(end_token)
        assert actual == has_comma
