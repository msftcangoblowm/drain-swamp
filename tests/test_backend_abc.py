"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

..

Unittest for module, drain_swamp.backend_abc

Unit test -- Module

.. code-block:: shell

   python -m coverage run --source='drain_swamp.backend_abc' -m pytest \
   --showlocals tests/test_backend_abc.py && coverage report \
   --data-file=.coverage --include="**/backend_abc.py"

Integration test

.. code-block:: shell

   make coverage
   pytest --showlocals --cov="drain_swamp" --cov-report=term-missing \
   --cov-config=pyproject.toml tests

"""

import logging
import logging.config
import sys
from pathlib import (
    Path,
    PurePath,
)
from unittest.mock import (
    MagicMock,
    patch,
)

import pytest

from drain_swamp._safe_path import resolve_joinpath
from drain_swamp.backend_abc import (
    BackendType,
    ensure_folder,
    folders_additional_cli,
    folders_implied_init,
    get_optionals_cli,
    get_optionals_pyproject_toml,
    get_required_cli,
    get_required_pyproject_toml,
    try_dict_update,
)
from drain_swamp.constants import (
    LOGGING,
    g_app_name,
)
from drain_swamp.parser_in import TomlParser

if sys.version_info >= (3, 9):  # pragma: no cover
    from collections.abc import Sequence
else:  # pragma: no cover
    from typing import Sequence


def test_try_dict_update(tmp_path, caplog, has_logging_occurred, prepare_folders_files):
    """Test try_dict_update."""
    # pytest --showlocals --log-level INFO -k "test_try_dict_update" -v tests
    LOGGING["loggers"][g_app_name]["propagate"] = True
    logging.config.dictConfig(LOGGING)
    logger = logging.getLogger(name=g_app_name)
    logger.addHandler(hdlr=caplog.handler)
    caplog.handler.level = logger.level

    # is_bypass == True; skips validating exists and is_file
    target_x = "prod"
    relative_x_path = "requirements/prod.shared.in"
    dict_cli = dict()
    try_dict_update(dict_cli, tmp_path, target_x, Path(relative_x_path), is_bypass=True)
    assert len(dict_cli.keys()) == 1
    assert dict_cli[target_x] == tmp_path / Path(relative_x_path)

    # is_bypass None of unsupported type --> False
    prepare_folders_files((relative_x_path,), tmp_path)

    no_cheatings = (
        None,
        1.12345,
        False,
    )
    for is_bypass in no_cheatings:
        dict_cli_actual = dict()
        try_dict_update(
            dict_cli_actual,
            tmp_path,
            target_x,
            Path(relative_x_path),
            is_bypass=is_bypass,
        )
        # assert has_logging_occurred(caplog)
        assert len(dict_cli_actual.keys()) == 1
        assert dict_cli_actual[target_x] == tmp_path / Path(relative_x_path)


testdata_get_required_pyproject_toml = [
    (
        Path(__file__).parent.joinpath("_good_files", "complete.pyproject_toml"),
        ("requirements/prod.shared.in",),
        ("prod", Path("requirements/prod.shared.in")),
    ),
]
ids_get_required_pyproject_toml = ("is_bypass True and False",)


@pytest.mark.parametrize(
    "path, lst_create_it, t_expected",
    testdata_get_required_pyproject_toml,
    ids=ids_get_required_pyproject_toml,
)
def test_get_required_pyproject_toml(
    path,
    lst_create_it,
    t_expected,
    tmp_path,
    prepare_folders_files,
    caplog,
    has_logging_occurred,
):
    """Test get_required_pyproject_toml."""
    # pytest -vv --showlocals --log-level INFO -k "test_get_required_pyproject_toml" tests
    LOGGING["loggers"][g_app_name]["propagate"] = True
    logging.config.dictConfig(LOGGING)
    logger = logging.getLogger(name=g_app_name)
    logger.addHandler(hdlr=caplog.handler)
    caplog.handler.level = logger.level

    tp = TomlParser(path)
    d_pyproject_toml = tp.d_pyproject_toml
    # is_bypass == True; skips validating exists and is_file
    # tuple[str, Path] | None
    t_actual = get_required_pyproject_toml(
        d_pyproject_toml,
        tmp_path,
        is_bypass=True,
    )
    if t_actual is None:
        assert t_actual is None
    else:
        assert isinstance(t_actual, Sequence)
        assert t_actual[0] == t_expected[0]
        assert t_actual[1] == tmp_path / t_expected[1]

    # prepare
    prepare_folders_files(lst_create_it, tmp_path)

    # is_bypass == False
    no_cheatings = (
        None,
        1.12345,
        False,
    )
    for is_bypass in no_cheatings:
        t_actual = get_required_pyproject_toml(
            d_pyproject_toml,
            tmp_path,
            is_bypass=is_bypass,
        )

        if t_actual is None:
            assert t_actual is None
        else:
            assert isinstance(t_actual, Sequence)
            assert t_actual[0] == t_expected[0]
            assert t_actual[1] == tmp_path / t_expected[1]
    assert has_logging_occurred(caplog)


testdata_get_required_cli = [
    (
        ("requirements/prod.shared.in",),
        ("prod", Path("requirements/prod.shared.in")),
        ("prod", Path("requirements/prod.shared.in")),
    ),
    (
        ("requirements/prod.shared.in",),
        ("prod", "requirements/prod.shared.in"),
        ("prod", Path("requirements/prod.shared.in")),
    ),
    (
        ("requirements/prod.shared.in",),
        ("prod", 1.2345),
        None,
    ),
    (
        ("requirements/prod.shared.in",),
        None,
        None,
    ),
]
ids_get_required_cli = (
    "relative_path is Path",
    "relative_path is str",
    "relative_path is float",
    "None rather than Sequence",
)


@pytest.mark.parametrize(
    "lst_create_it, t_required, t_expected",
    testdata_get_required_cli,
    ids=ids_get_required_cli,
)
@pytest.mark.parametrize(
    "is_prepare, is_bypass",
    [
        (
            False,
            True,
        ),
        (
            True,
            None,
        ),
        (
            True,
            1.2345,
        ),
        (
            True,
            False,
        ),
    ],
    ids=[
        "is_prepare=False, is_bypass=True",
        "is_prepare=True, is_bypass=None",
        "is_prepare=True, is_bypass=1.2345",
        "is_prepare=True, is_bypass=False",
    ],
)
def test_get_required_cli(
    lst_create_it,
    t_required,
    t_expected,
    is_prepare,
    is_bypass,
    tmp_path,
    prepare_folders_files,
):
    """Test get_required_cli."""
    # pytest --showlocals --log-level INFO -k "test_get_required_cli" -v tests
    if is_prepare:
        prepare_folders_files(lst_create_it, tmp_path)

    t_actual = get_required_cli(tmp_path, required=t_required, is_bypass=is_bypass)
    if t_actual is None:
        assert t_actual is None
    else:
        assert t_actual[0] == t_expected[0]
        assert t_actual[1] == tmp_path / t_expected[1]


testdata_required = [
    (
        Path(__file__).parent.joinpath("_good_files", "complete.pyproject_toml"),
        None,
        ("requirements/prod.shared.in",),
        ("prod", Path("requirements/prod.shared.in")),
    ),
    (
        Path(__file__).parent.joinpath("_good_files", "complete.pyproject_toml"),
        "",
        ("requirements/prod.shared.in",),
        ("prod", Path("requirements/prod.shared.in")),
    ),
    (
        Path(__file__).parent.joinpath("_good_files", "complete.pyproject_toml"),
        "    ",
        ("requirements/prod.shared.in",),
        ("prod", Path("requirements/prod.shared.in")),
    ),
    (
        Path(__file__).parent.joinpath("_good_files", "complete.pyproject_toml"),
        1.12345,
        ("requirements/prod.shared.in",),
        ("prod", Path("requirements/prod.shared.in")),
    ),
    (
        Path(__file__).parent.joinpath("_good_files", "complete.pyproject_toml"),
        ("alt", "requirements/alt.in"),
        ("requirements/prod.shared.in", "requirements/alt.in"),
        ("alt", Path("requirements/alt.in")),
    ),
    (
        Path(__file__).parent.joinpath("_good_files", "complete.pyproject_toml"),
        ("alt", "requirements/alt.in"),
        [],
        None,
    ),
    (
        Path(__file__).parent.joinpath("_good_files", "complete.pyproject_toml"),
        ("alt", Path("requirements/alt.in")),
        [],
        None,
    ),
    (
        Path(__file__).parent.joinpath("_good_files", "complete.pyproject_toml"),
        ("alt", Path("requirements/alt.in")),
        ("requirements/prod.shared.in", "requirements/alt.in"),
        ("alt", Path("requirements/alt.in")),
    ),
]
ids_required = (
    "cli None",
    "cli empty string",
    "cli excessive whitespace",
    "cli unsupported type",
    "prioritize cli over pyproject.toml",
    "no required file exists",
    "cli relative path is Path; no actual file",
    "cli relative path is Path; actual file",
)


@pytest.mark.parametrize(
    "path, cli_required, lst_create_it, t_expected",
    testdata_required,
    ids=ids_required,
)
def test_get_required(
    path,
    cli_required,
    lst_create_it,
    t_expected,
    tmp_path,
    prepare_folders_files,
    caplog,
    has_logging_occurred,
):
    """Test BackendType.get_required."""
    # pytest --showlocals --log-level INFO -k "test_get_required" -v tests
    LOGGING["loggers"][g_app_name]["propagate"] = True
    logging.config.dictConfig(LOGGING)
    logger = logging.getLogger(name=g_app_name)
    logger.addHandler(hdlr=caplog.handler)
    caplog.handler.level = logger.level

    # prepare
    prepare_folders_files(lst_create_it, tmp_path)

    # act
    tp = TomlParser(path)
    d_pyproject_toml = tp.d_pyproject_toml
    t_actual = BackendType.get_required(
        d_pyproject_toml, tmp_path, required=cli_required
    )
    # verify
    if t_actual is None:
        # assert has_logging_occurred(caplog)
        assert t_actual == t_expected
    else:
        target_a, abspath_a = t_actual
        relpath_a = abspath_a.relative_to(tmp_path)
        # assert has_logging_occurred(caplog)
        assert (target_a, relpath_a) == t_expected


testdata_get_optionals_cli = (
    (
        {},
        {},
    ),
    (
        {"tox": Path("requirements/tox.in"), "kit": Path("requirements/kit.in")},
        {"tox": Path("requirements/tox.in"), "kit": Path("requirements/kit.in")},
    ),
    (
        {"tox": "requirements/tox.in", "kit": "requirements/kit.in"},
        {"tox": Path("requirements/tox.in"), "kit": Path("requirements/kit.in")},
    ),
    (
        {"tox": None, "kit": 1.1234, "prod": 1},
        {},
    ),
    (
        {"tox": None, "kit": None},
        {},
    ),
)
ids_get_optionals_cli = (
    "empty dict",
    "values relative Path",
    "values relative path str",
    "values unsupported types",
    "values None",
)


@pytest.mark.parametrize(
    "d_pairs, d_expected",
    testdata_get_optionals_cli,
    ids=ids_get_optionals_cli,
)
def test_get_optionals_cli(d_pairs, d_expected, tmp_path, prepare_folders_files):
    """Test get_optionals_cli."""
    # pytest --showlocals --log-level INFO -k "test_get_optionals_cli" -v tests

    # seq_rel_paths not a Sequence
    invalids = (
        {"tox": None},
        {"kit": 1.2345},
        {"prod": 1},
    )
    d_invalids_expected = dict()
    for d_invalid in invalids:
        get_optionals_cli(
            d_invalids_expected,
            tmp_path,
            d_invalid,
        )
        assert len(d_invalids_expected.keys()) == 0

    # prepare
    if isinstance(d_pairs, dict):
        #    dict_values --> list
        seq_prepare_these = list(d_pairs.values())
        prepare_folders_files(seq_prepare_these, tmp_path)

    # act
    d_cli_actual = dict()

    get_optionals_cli(
        d_cli_actual,
        tmp_path,
        d_pairs,
    )

    # d_expected_abs_paths -- target/path_rel --> target / abs path
    # d_cli_actual         -- target / abs path
    d_expected_abs_paths = dict()
    for target, path_rel in d_expected.items():
        abs_path = tmp_path / path_rel
        d_expected_abs_paths.update({target: abs_path})

    assert d_cli_actual == d_expected_abs_paths


testdata_get_optionals_pyproject_toml = (
    (
        Path(__file__).parent.joinpath("_good_files", "complete.pyproject_toml"),
        5,
    ),
    (
        Path(__file__).parent.joinpath("_good_files", "nonsense-keys.pyproject_toml"),
        0,
    ),
    (
        Path(__file__).parent.joinpath("_good_files", "requires-none.pyproject_toml"),
        0,
    ),
)
ids_get_optionals_pyproject_toml = [
    f"""{t_backend[0].name.rsplit(".", 1)[0]}{t_backend[1]}"""
    for t_backend in testdata_get_optionals_pyproject_toml
]


@pytest.mark.parametrize(
    "path, expected_count",
    testdata_get_optionals_pyproject_toml,
    ids=ids_get_optionals_pyproject_toml,
)
def test_get_optionals_pyproject_toml(
    path,
    expected_count,
    tmp_path,
    caplog,
    has_logging_occurred,
    prepare_folders_files,
):
    """Test get_optionals_pyproject_toml."""
    # pytest  -vv --showlocals --log-level INFO -k "test_get_optionals_pyproject_toml" tests
    LOGGING["loggers"][g_app_name]["propagate"] = True
    logging.config.dictConfig(LOGGING)
    logger = logging.getLogger(name=g_app_name)
    logger.addHandler(hdlr=caplog.handler)
    caplog.handler.level = logger.level

    tp = TomlParser(path)
    d_pyproject_toml = tp.d_pyproject_toml

    # is_bypass True
    d_actual = dict()
    get_optionals_pyproject_toml(
        d_actual,
        d_pyproject_toml,
        tmp_path,
        is_bypass=True,
    )
    # assert has_logging_occurred(caplog)
    actual_count = len(d_actual.keys())
    assert actual_count == expected_count

    """prepare

    seq_expected contains rel path need abs paths. Create folders and files
    """
    d_prepare_these = {
        "pip": "requirements/pip.in",
        "pip_tools": "requirements/pip-tools.in",
        "dev": "requirements/dev.in",
        "manage": "requirements/manage.in",
        "docs": "docs/requirements.in",
    }
    seq_prepare_these = list(d_prepare_these.values())
    prepare_folders_files(seq_prepare_these, tmp_path)

    d_expected_abspaths = dict()

    # is_bypass unsupported type --> False
    is_bypasses = (
        None,
        1.2345,
        1,
        False,
    )
    d_expected_abspaths = dict()
    for target, rel_path in d_prepare_these.items():
        path_abs = tmp_path / rel_path
        d_expected_abspaths.update({target: path_abs})

    for is_bypass in is_bypasses:
        d_actual = dict()
        get_optionals_pyproject_toml(
            d_actual,
            d_pyproject_toml,
            tmp_path,
            is_bypass=is_bypass,
        )
        # assert has_logging_occurred(caplog)

        d_actual == d_expected_abspaths


testdata_get_optional = [
    (
        Path(__file__).parent.joinpath("_good_files", "complete.pyproject_toml"),
        {"tox": Path("requirements/tox.in"), "kit": Path("requirements/kit.in")},
    ),
    (
        Path(__file__).parent.joinpath("_good_files", "nonsense-keys.pyproject_toml"),
        {"tox": Path("requirements/tox.in"), "kit": Path("requirements/kit.in")},
    ),
]
ids_get_optional = (
    "Path cli supplied tox and kit",
    "pyproject.toml nonsense-keys",
)


@pytest.mark.parametrize(
    "path, d_cli",
    testdata_get_optional,
    ids=ids_get_optional,
)
def test_get_optionals_both(
    path,
    d_cli,
    tmp_path,
    prepare_folders_files,
):
    """Test get_optionals_pyproject_toml."""
    # pytest --showlocals --log-level INFO -k "test_get_optionals" -v tests
    tp = TomlParser(path)
    d_pyproject_toml = tp.d_pyproject_toml

    # Prepare -- cli
    seq_prepare_these = list(d_cli.values())
    prepare_folders_files(seq_prepare_these, tmp_path)

    # Prepare -- pyproject.toml
    d_pypro = dict()
    get_optionals_pyproject_toml(
        d_pypro,
        d_pyproject_toml,
        tmp_path,
        is_bypass=True,
    )
    seq_prepare_these = list(d_pypro.values())
    prepare_folders_files(seq_prepare_these, tmp_path)

    # cli suppliments pyproject.toml
    for target, rel_path in d_cli.items():
        is_pathlike = isinstance(rel_path, str) or issubclass(type(rel_path), PurePath)
        if is_pathlike:
            d_pypro[target] = tmp_path.joinpath(rel_path)

    d_actual = BackendType.get_optionals(
        d_pyproject_toml,
        tmp_path,
        d_cli,
    )
    assert d_actual == d_pypro


testdata_folders_implied_init = (
    (
        {
            "pip": "requirements/pip.in",
            "pip_tools": "requirements/pip-tools.in",
            "dev": "requirements/dev.in",
            "manage": "requirements/manage.in",
            "docs": "docs/requirements.in",
        },
        ("prod", "requirements/prod.shared.in"),
        {Path("requirements"), Path("docs")},
    ),
)
ids_folders_implied_init = ("normal optionals and required",)


@pytest.mark.parametrize(
    "d_optionals, t_required, s_expected",
    testdata_folders_implied_init,
    ids=ids_folders_implied_init,
)
def test_folders_implied_init(
    d_optionals,
    t_required,
    s_expected,
    tmp_path,
    prepare_folders_files,
):
    """Test folders_implied_init."""
    # pytest --showlocals --log-level INFO -k "test_folders_implied_init" -v tests
    # input lacks abs path. Including expected

    # prepare
    seq_prepare_these = list(d_optionals.values())
    prepare_folders_files(seq_prepare_these, tmp_path)
    if t_required is not None:
        seq_prepare_these = (t_required[1],)
    else:
        seq_prepare_these = t_required
    prepare_folders_files(seq_prepare_these, tmp_path)

    # act
    d_optionals_abspath = {}
    for key, value in d_optionals.items():
        d_optionals_abspath[key] = tmp_path / value

    if t_required is not None:
        t_required_abs_path = (t_required[0], tmp_path / t_required[1])
    else:
        t_required_abs_path = None

    s_actual = folders_implied_init(tmp_path, d_optionals_abspath, t_required_abs_path)
    assert s_actual == s_expected


testdata_folders_additional_cli = (
    (
        {Path("requirements"), Path("docs")},
        (Path("requirements"), Path("docs"), Path("ci")),
        {Path("ci")},
    ),
    (
        {Path("requirements"), Path("docs")},
        (Path("ci"),),
        {Path("ci")},
    ),
)
ids_folders_additional_cli = (
    "Folders contains all folders",
    "Folders contains just the additional folders",
)


@pytest.mark.parametrize(
    "s_folders_implied, t_additional_folders, s_expected",
    testdata_folders_additional_cli,
    ids=ids_folders_additional_cli,
)
def test_folders_additional_cli(
    s_folders_implied,
    t_additional_folders,
    s_expected,
    tmp_path,
):
    """Test folders_additional_cli."""
    # pytest --showlocals --log-level INFO -k "test_folders_additional_cli" -v tests
    # prepare
    for path_dir_implied in s_folders_implied:
        abs_path = tmp_path / path_dir_implied
        abs_path.mkdir(parents=True, exist_ok=True)
    #    Actual code is not naive about existance of implied folders
    for path_dir_additional in t_additional_folders:
        abs_path = tmp_path / path_dir_additional
        abs_path.mkdir(parents=True, exist_ok=True)

    # Should contain relative paths. Which is normal situation / usage
    s_actual = folders_additional_cli(
        tmp_path,
        s_folders_implied,
        t_additional_folders,
    )
    assert s_actual == s_expected

    # Absolute paths. This is abnormal usage. Academic use case
    lst_additional_folders = []
    if t_additional_folders is not None:
        for additional_folders_relpath in t_additional_folders:
            lst_additional_folders.append(tmp_path / additional_folders_relpath)
        t_additional_folders_abspath = tuple(lst_additional_folders)
    else:
        t_additional_folders_abspath = t_additional_folders

    s_actual = folders_additional_cli(
        tmp_path,
        s_folders_implied,
        t_additional_folders_abspath,
    )
    assert s_actual == s_expected


def test_ensure_folder(tmp_path):
    """Test ensure_folder."""
    # pytest --showlocals --log-level INFO -k "test_ensure_folder" -v tests
    # folder
    path_actual = ensure_folder(tmp_path)
    assert issubclass(type(path_actual), PurePath)

    # file
    path_file = tmp_path.joinpath("todd.in")
    path_file.touch()
    path_actual = ensure_folder(path_file)
    assert path_actual.is_dir() and path_actual == tmp_path

    # symlink (by someone with a grudge against todd and a fondness for harrassment)
    p = tmp_path.joinpath("todd_wears_drag_and_drinks_bud_lite.in")
    p.symlink_to(path_file)
    with pytest.raises(NotADirectoryError):
        ensure_folder(p)

    # MagicMock with a return_value which isn't a Path
    mock = MagicMock(wraps=ensure_folder)
    with pytest.raises(TypeError):
        mock("Hello World!")

    # unsupported type
    invalids = (
        None,
        1.2345,
        "Hello World!",
    )
    for invalid in invalids:
        with pytest.raises(TypeError):
            ensure_folder(invalid)

    # MagicMock with a return_value
    path_config = Path(__file__).parent.joinpath(
        "_good_files", "requires-none.pyproject_toml"
    )
    parent_dir = Path(__file__).parent.joinpath("conftest.py")
    with patch(
        f"{g_app_name}.backend_abc.BackendType.path_config",
        return_value=tmp_path,
    ):
        inst = BackendType(path_config, parent_dir=parent_dir)
        # folder
        ensure_folder(inst.parent_dir)
        # file. Will get it's parent
        ensure_folder(inst.path_config)


testdata_backend_abc_repr_edge_cases = (
    Path(__file__).parent.joinpath(
        "_bad_files",
        "static_dependencies.pyproject_toml",
    ),
    Path(__file__).parent.joinpath(
        "_good_files",
        "complete.pyproject_toml",
    ),
)
ids_backend_abc_repr_edge_cases = (
    "static dependencies have no required nor optionals",
    "with required",
)


@pytest.mark.parametrize(
    "path_config_src",
    testdata_backend_abc_repr_edge_cases,
    ids=ids_backend_abc_repr_edge_cases,
)
def test_backend_abc_repr_edge_cases(
    path_config_src,
    tmp_path,
    prep_pyproject_toml,
    prepare_folders_files,
    caplog,
    has_logging_occurred,
):
    """Double check BackendType.__repr__ when only static dependencies."""
    # pytest --showlocals --log-level INFO -k "test_backend_abc_repr_edge_cases" -v tests
    LOGGING["loggers"][g_app_name]["propagate"] = True
    logging.config.dictConfig(LOGGING)
    logger = logging.getLogger(name=g_app_name)
    logger.addHandler(hdlr=caplog.handler)
    caplog.handler.level = logger.level

    # prepare
    #    pyproject.toml
    path_f = prep_pyproject_toml(path_config_src, tmp_path)

    #    additional folder: ``ci/``
    prepare_folders_files(("ci/empty.txt",), tmp_path)
    path_empty_file = resolve_joinpath(tmp_path, "ci/empty.txt")
    path_empty_file.unlink()

    inst = BackendType(path_f, parent_dir=tmp_path)

    tp = TomlParser(path_f)
    d_pyproject_toml = tp.d_pyproject_toml

    # required file exists will fail. No requirement file; not copied into tmp_path
    invalids = (
        None,
        1.2345,
    )
    for invalid in invalids:
        t_c = BackendType.get_required(
            d_pyproject_toml,
            tmp_path,
            required=None,
            is_bypass=invalid,
        )
    assert t_c is None

    # bypass file exists check
    t_c = BackendType.get_required(
        d_pyproject_toml,
        tmp_path,
        required=None,
        is_bypass=True,
    )
    logger.info(f"t_c: {t_c!r}")

    logger.info(f"folders_implied: {inst.folders_implied}")
    logger.info(f"folders_additional: {inst.folders_additional}")
    logger.info(f"inst.required: {inst.required!r}")

    str_repr = repr(inst)
    assert isinstance(str_repr, str)

    logger.info(f"str_repr: {str_repr!r}")

    assert has_logging_occurred(caplog)
