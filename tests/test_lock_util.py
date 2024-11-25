"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

Unit test -- Module

.. code-block:: shell

   python -m coverage run --source='drain_swamp.lock_util' -m pytest \
   --showlocals tests/test_lock_util.py && coverage report \
   --data-file=.coverage --include="**/lock_util.py"

"""

import site
from contextlib import nullcontext as does_not_raise
from pathlib import (
    Path,
    PurePath,
)
from typing import cast

import pytest
from logging_strict.tech_niques import get_locals  # noqa: F401

from drain_swamp._safe_path import resolve_joinpath
from drain_swamp.constants import (  # g_app_name,  # noqa: F401
    SUFFIX_IN,
    SUFFIX_LOCKED,
    SUFFIX_SHARED_IN,
    SUFFIX_UNLOCKED,
)
from drain_swamp.lock_util import (
    abspath_relative_to_package_base_folder,
    check_relpath,
    is_shared,
    is_suffixes_ok,
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


testdata_is_suffixes_ok = (
    (
        "requirements/prod.shared",
        "prod.shared",
        pytest.raises(ValueError),
    ),
    (
        "requirements/prod",
        "prod",
        pytest.raises(ValueError),
    ),
    (
        "requirements/prod.shared.frog",
        "prod.shared",
        pytest.raises(ValueError),
    ),
    (
        "requirements/prod.frog",
        "prod",
        pytest.raises(ValueError),
    ),
    (
        7.4,
        "prod",
        pytest.raises(TypeError),
    ),
    (
        "requirements/prod.shared.in",
        "prod.shared.in",
        does_not_raise(),
    ),
    (
        Path("requirements/prod.shared.in"),
        "prod.shared.in",
        does_not_raise(),
    ),
)
ids_is_suffixes_ok = (
    "no ENDING",
    "No suffixes",
    ".shared then unknown ENDING",
    "not .shared then unknown ENDING",
    "unsupported type",
    "acceptable relative path",
    "acceptable relative Path",
)


@pytest.mark.parametrize(
    "relpath, stem, expectation",
    testdata_is_suffixes_ok,
    ids=ids_is_suffixes_ok,
)
def test_is_suffixes_ok(relpath, stem, expectation):
    """Test is_suffixes_ok. Demonstrate invalid relpath."""
    # pytest --showlocals --log-level INFO -k "test_is_suffixes_ok" tests
    with expectation:
        is_suffixes_ok(relpath)


testdata_check_relpath = (
    (
        Path("requirements/pip.in"),
        does_not_raise(),
    ),
)
ids_check_relpath = ("pip.in 1 constraint 3 requirements",)


@pytest.mark.parametrize(
    "relpath, expectation",
    testdata_check_relpath,
    ids=ids_check_relpath,
)
def test_check_relpath(
    relpath,
    expectation,
    path_project_base,
    tmp_path,
):
    """check_relpath is relpath relative to cwd"""
    # pytest --showlocals --log-level INFO -k "test_check_relpath" tests
    # prepare
    path_cwd = path_project_base()

    # prepare
    path_f_in_tmp = cast("Path", resolve_joinpath(tmp_path, "deleteme.txt"))
    path_f_in_tmp.touch()
    # no touch
    path_f_in_cwd = cast("Path", resolve_joinpath(path_cwd, "deleteme.txt"))

    # unsupported type --> TypeError
    invalids = (
        None,
        1.234,
    )
    for invalid in invalids:
        with pytest.raises(TypeError):
            check_relpath(path_cwd, invalid)

    # no such file --> FileNotFoundError
    with pytest.raises(FileNotFoundError):
        check_relpath(path_cwd, path_f_in_cwd)

    # not relative to base folder --> ValueError
    with pytest.raises(ValueError):
        check_relpath(path_cwd, path_f_in_tmp)

    # file exists relative to cwd. No exception raised
    with expectation:
        check_relpath(path_cwd, relpath)


testdata_abspath_relative_to_package_base_folder = (
    (
        Path(__file__).parent.parent.joinpath(
            "docs",
            "pip-tools.in",
        ),
        "../requirements/pins.shared.in",
        does_not_raise(),
        "requirements/pins.shared.in",
    ),
    (
        Path(__file__).parent.parent.joinpath(
            "docs",
            "pip-tools.in",
        ),
        "../requirements/dogfood.shared.in",
        pytest.raises(FileNotFoundError),
        "requirements/dogfood.shared.in",
    ),
    (
        Path(site.getuserbase()),
        "../requirements/dogfood.shared.in",
        pytest.raises(ValueError),
        "requirements/dogfood.shared.in",
    ),
)
ids_abspath_relative_to_package_base_folder = (
    "different folders",
    "impossible to resolve requirements file not found",
    "not subpath not relative to",
)


@pytest.mark.parametrize(
    "abspath_f, constraint_relpath, expectation, expected_relpath",
    testdata_abspath_relative_to_package_base_folder,
    ids=ids_abspath_relative_to_package_base_folder,
)
def test_abspath_relative_to_package_base_folder(
    abspath_f,
    constraint_relpath,
    expectation,
    expected_relpath,
    path_project_base,
):
    """Normalize requirement file constraint or requirement relpath to cwd"""
    # pytest --showlocals --log-level INFO -k "test_abspath_relative_to_package_base_folder" tests
    # prepare
    path_cwd = path_project_base()

    with expectation:
        abspath_actual = abspath_relative_to_package_base_folder(
            path_cwd,
            abspath_f,
            constraint_relpath,
        )
    if isinstance(expectation, does_not_raise):
        relpath_actual = abspath_actual.relative_to(path_cwd)
        assert str(relpath_actual) == expected_relpath
