"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

Unit test -- Module

.. code-block:: shell

   python -m coverage run --source='drain_swamp.lock_util' -m pytest \
   --showlocals tests/test_lock_util.py && coverage report \
   --data-file=.coverage --include="**/lock_util.py"

"""

from contextlib import nullcontext as does_not_raise
from pathlib import PurePath

import pytest
from logging_strict.tech_niques import get_locals  # noqa: F401

from drain_swamp.constants import (  # g_app_name,  # noqa: F401
    SUFFIX_IN,
    SUFFIX_LOCKED,
    SUFFIX_SHARED_IN,
    SUFFIX_UNLOCKED,
)
from drain_swamp.lock_util import (
    is_shared,
    replace_suffixes_last,
)

testdata_is_shared = (
    (
        f"dog{SUFFIX_IN}",
        does_not_raise(),
        False,
    ),
    (
        f"dog{SUFFIX_SHARED_IN}",
        does_not_raise(),
        True,
    ),
    (
        f"dog{SUFFIX_LOCKED}",
        does_not_raise(),
        False,
    ),
    (
        f"dog.shared{SUFFIX_LOCKED}",
        does_not_raise(),
        True,
    ),
    (
        f"dog{SUFFIX_UNLOCKED}",
        does_not_raise(),
        False,
    ),
    (
        f"dog.shared{SUFFIX_UNLOCKED}",
        does_not_raise(),
        True,
    ),
    (
        "dog",
        does_not_raise(),
        False,
    ),
    (
        "dog.shared",
        does_not_raise(),
        True,
    ),
    (
        None,
        pytest.raises(ValueError),
        False,
    ),
    (
        "",
        pytest.raises(ValueError),
        False,
    ),
    (
        "   ",
        pytest.raises(ValueError),
        False,
    ),
    (
        1.2345,
        pytest.raises(ValueError),
        False,
    ),
)
ids_is_shared = (
    SUFFIX_IN,
    SUFFIX_SHARED_IN,
    SUFFIX_LOCKED,
    f".shared{SUFFIX_LOCKED}",
    SUFFIX_UNLOCKED,
    f".shared{SUFFIX_UNLOCKED}",
    "no suffixes",
    "no ending .shared",
    "None",
    "empty str",
    "just whitespace",
    "unsupported type",
)


@pytest.mark.parametrize(
    "file_name, expectation, expected_is_shared",
    testdata_is_shared,
    ids=ids_is_shared,
)
def test_lock_util_is_shared(file_name, expectation, expected_is_shared):
    """Test is_shared."""
    # pytest --showlocals --log-level INFO -k "test_lock_util_is_shared" tests
    with expectation:
        actual = is_shared(file_name)
    if isinstance(expectation, does_not_raise):
        # func_path = f"{g_app_name}.lock_util.is_shared"
        # args = (file_name,)
        # kwargs = {}
        # t_ret = get_locals(func_path, is_shared, *args, **kwargs)
        pass

        assert actual is expected_is_shared


testdata_replace_suffixes_last = (
    (
        "dog",
        SUFFIX_IN,
        does_not_raise(),
        f"dog{SUFFIX_IN}",
    ),
    (
        "dog.shared",
        SUFFIX_IN,
        does_not_raise(),
        f"dog{SUFFIX_SHARED_IN}",
    ),
    (
        f"dog.shared{SUFFIX_UNLOCKED}",
        SUFFIX_IN,
        does_not_raise(),
        f"dog{SUFFIX_SHARED_IN}",
    ),
)
ids_replace_suffixes_last = (
    "No suffix",
    f"add suffix {SUFFIX_IN}",
    f".shared{SUFFIX_UNLOCKED} --> {SUFFIX_SHARED_IN}",
)


@pytest.mark.parametrize(
    "file_name, suffix, expectation, expected_file_name",
    testdata_replace_suffixes_last,
    ids=ids_replace_suffixes_last,
)
def test_replace_suffixes_last(
    file_name,
    suffix,
    expectation,
    expected_file_name,
    tmp_path,
    prepare_folders_files,
):
    """Test replace_suffixes_last."""
    # pytest --showlocals --log-level INFO -k "test_replace_suffixes_last" tests
    # prepare
    prepare_these = (file_name,)
    set_files_dest = prepare_folders_files(prepare_these, tmp_path)

    # Act
    for abspath_f in set_files_dest:
        with expectation:
            actual_f = replace_suffixes_last(abspath_f, suffix)
        if isinstance(expectation, does_not_raise):
            # Verify
            actual_file_name = actual_f.name
            assert actual_file_name == expected_file_name

        # PurePath
        with pytest.raises(TypeError):
            replace_suffixes_last(PurePath(abspath_f), suffix)

        # Not a Path
        with pytest.raises(TypeError):
            replace_suffixes_last(1.2345, suffix)

        # relative path --> ValueError
        with pytest.raises(ValueError):
            relpath_f = abspath_f.relative_to(tmp_path)
            replace_suffixes_last(relpath_f, suffix)
