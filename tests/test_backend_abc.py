"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

..

Unittest for module, drain_swamp.backend_setupttools

.. code-block:: shell

   pytest --showlocals --log-level INFO tests/test_backend_abc.py
   pytest --showlocals --cov="drain_swamp" --cov-report=term-missing tests/test_backend_abc.py

"""

import logging
import logging.config
import sys
from pathlib import (
    Path,
    PurePath,
)
from unittest.mock import MagicMock

import pytest

from drain_swamp._run_cmd import run_cmd
from drain_swamp.backend_abc import (
    BackendType,
    ensure_folder,
    folders_additional_init,
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
from drain_swamp.exceptions import PyProjectTOMLReadError
from drain_swamp.parser_in import TomlParser
from drain_swamp.snip import ReplaceResult

if sys.version_info >= (3, 9):  # pragma: no cover
    from collections.abc import Sequence
else:  # pragma: no cover
    from typing import Sequence

testdata_fix_suffix = [
    ("md", ".md"),
    (".md", ".md"),
]
ids_fix_suffix = [
    "without prefix period",
    "with prefix period",
]


@pytest.mark.parametrize(
    "suffix, expected",
    testdata_fix_suffix,
    ids=ids_fix_suffix,
)
def test_fix_suffix(suffix, expected):
    """Does not barf given multiple suffixes e.g. .tar.gz"""
    # pytest --showlocals --log-level INFO -k "test_fix_suffix" tests
    actual = BackendType.fix_suffix(suffix)
    assert actual == expected


testdata_determine_backend = [
    (
        Path(__file__).parent.joinpath("_good_files", "backend-only.pyproject_toml"),
        "setuptools",
    ),
    (
        Path(__file__).parent.joinpath("_good_files", "complete.pyproject_toml"),
        "setuptools",
    ),
    (
        Path(__file__).parent.joinpath("_good_files", "requires-none.pyproject_toml"),
        "setuptools",
    ),
    (
        Path(__file__).parent.joinpath("_good_files", "nonsense-keys.pyproject_toml"),
        "setuptools",
    ),
    (
        Path(__file__).parent.joinpath(
            "_good_files", "thin-wrap-backend.pyproject_toml"
        ),
        "setuptools",
    ),
]
ids_determine_backend = [
    f"""{t_backend[0].name.rsplit(".", 1)[0]}{t_backend[1]}"""
    for t_backend in testdata_determine_backend
]


@pytest.mark.parametrize(
    "path, expected",
    testdata_determine_backend,
    ids=ids_determine_backend,
)
def test_determine_backend(path, expected):
    # pytest --showlocals --log-level INFO -k "test_determine_backend" tests
    tp = TomlParser(path)
    d_pyproject_toml = tp.d_pyproject_toml
    actual = BackendType.determine_backend(d_pyproject_toml)
    assert actual == expected


def test_try_dict_update(tmp_path, caplog, has_logging_occurred, prepare_folders_files):
    # pytest --showlocals --log-level INFO -k "test_try_dict_update" -v tests
    LOGGING["loggers"][g_app_name]["propagate"] = True
    logging.config.dictConfig(LOGGING)
    logger = logging.getLogger(name=g_app_name)
    logger.addHandler(hdlr=caplog.handler)
    caplog.handler.level = logger.level

    # is_bypass == True; skips validating exists and is_file
    target_x = "prod"
    relative_x_path = "requirements/prod.in"
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
        ("requirements/prod.in",),
        ("prod", Path("requirements/prod.in")),
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
):
    # pytest --showlocals --log-level INFO -k "test_get_required_pyproject_toml" -v tests
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


testdata_get_required_cli = [
    (
        ("requirements/prod.in",),
        ("prod", Path("requirements/prod.in")),
        ("prod", Path("requirements/prod.in")),
    ),
    (
        ("requirements/prod.in",),
        ("prod", "requirements/prod.in"),
        ("prod", Path("requirements/prod.in")),
    ),
    (
        ("requirements/prod.in",),
        ("prod", 1.2345),
        None,
    ),
    (
        ("requirements/prod.in",),
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
def test_get_required_cli(
    lst_create_it,
    t_required,
    t_expected,
    tmp_path,
    prepare_folders_files,
):
    # pytest --showlocals --log-level INFO -k "test_get_required_cli" -v tests
    # bypass True
    t_actual = get_required_cli(tmp_path, required=t_required, is_bypass=True)
    if t_actual is None:
        assert t_actual is None
    else:
        assert t_actual[0] == t_expected[0]
        assert t_actual[1] == tmp_path / t_expected[1]

    # bypass False
    #    prepare
    prepare_folders_files(lst_create_it, tmp_path)

    no_cheatings = (
        None,
        1.12345,
        False,
    )
    for is_bypass in no_cheatings:
        t_actual = get_required_cli(tmp_path, required=t_required, is_bypass=is_bypass)
        if t_actual is None:
            assert t_actual is None
        else:
            assert isinstance(t_actual, Sequence)
            assert t_actual[0] == t_expected[0]
            assert t_actual[1] == tmp_path / t_expected[1]


testdata_required = [
    (
        Path(__file__).parent.joinpath("_good_files", "complete.pyproject_toml"),
        None,
        ("requirements/prod.in",),
        ("prod", Path("requirements/prod.in")),
    ),
    (
        Path(__file__).parent.joinpath("_good_files", "complete.pyproject_toml"),
        "",
        ("requirements/prod.in",),
        ("prod", Path("requirements/prod.in")),
    ),
    (
        Path(__file__).parent.joinpath("_good_files", "complete.pyproject_toml"),
        "    ",
        ("requirements/prod.in",),
        ("prod", Path("requirements/prod.in")),
    ),
    (
        Path(__file__).parent.joinpath("_good_files", "complete.pyproject_toml"),
        1.12345,
        ("requirements/prod.in",),
        ("prod", Path("requirements/prod.in")),
    ),
    (
        Path(__file__).parent.joinpath("_good_files", "complete.pyproject_toml"),
        ("alt", "requirements/alt.in"),
        ("requirements/prod.in", "requirements/alt.in"),
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
        ("requirements/prod.in", "requirements/alt.in"),
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
    # pytest --showlocals --log-level INFO -k "test_get_required" -v tests
    LOGGING["loggers"][g_app_name]["propagate"] = True
    logging.config.dictConfig(LOGGING)
    logger = logging.getLogger(name=g_app_name)
    logger.addHandler(hdlr=caplog.handler)
    caplog.handler.level = logger.level

    # prepare
    prepare_folders_files(lst_create_it, tmp_path)

    tp = TomlParser(path)
    d_pyproject_toml = tp.d_pyproject_toml
    t_actual = BackendType.get_required(
        d_pyproject_toml, tmp_path, required=cli_required
    )
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
        5,
    ),
    (
        Path(__file__).parent.joinpath("_good_files", "requires-none.pyproject_toml"),
        5,
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
    # pytest --showlocals --log-level INFO -k "test_get_optionals_pyproject_toml" -v tests
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
    assert len(d_actual.keys()) == expected_count

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
        ("prod", "requirements/prod.in"),
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


testdata_folders_additional_init = (
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
ids_folders_additional_init = (
    "Folders contains all folders",
    "Folders contains just the additional folders",
)


@pytest.mark.parametrize(
    "s_folders_implied, t_additional_folders, s_expected",
    testdata_folders_additional_init,
    ids=ids_folders_additional_init,
)
def test_folders_additional_init(
    s_folders_implied,
    t_additional_folders,
    s_expected,
    tmp_path,
):
    # pytest --showlocals --log-level INFO -k "test_folders_additional_init" -v tests
    # prepare
    for path_dir_implied in s_folders_implied:
        abs_path = tmp_path / path_dir_implied
        abs_path.mkdir(parents=True, exist_ok=True)
    #    Actual code is not naive about existance of implied folders
    for path_dir_additional in t_additional_folders:
        abs_path = tmp_path / path_dir_additional
        abs_path.mkdir(parents=True, exist_ok=True)

    # Should contain relative paths. Which is normal situation / usage
    s_actual = folders_additional_init(
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

    s_actual = folders_additional_init(
        tmp_path,
        s_folders_implied,
        t_additional_folders_abspath,
    )
    assert s_actual == s_expected


def test_ensure_folder(tmp_path):
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


testdata_is_locked = (
    (
        "no_snippet_with_id_none.txt",
        None,
        "zzzzzzzzzzzzz\n# @@@ editable asdf\nblah blah blah\n# @@@ end\nzzzzzz\n# @@@ editable george\nhey there george\n# @@@ end\nzzzzzzz\n",
        ReplaceResult.NO_MATCH,
    ),
    (
        "no_snippet_with_that_id.txt",
        "ted",
        "zzzzzzzzzzzzz\n# @@@ editable asdf\nblah blah blah\n# @@@ end\nzzzzzz\n# @@@ editable george\nhey there george\n# @@@ end\nzzzzzzz\n",
        ReplaceResult.NO_MATCH,
    ),
    (
        "snippet_with_id_all_unlocked.txt",
        "ted",
        """zzzzzzzzzzzzz\n# @@@ editable ted\ndependencies = { file = ["requirements/prod.unlock"] }
optional-dependencies.pip = { file = ["requirements/pip.unlock"] }
optional-dependencies.pip_tools = { file = ["requirements/pip-tools.unlock"] }
optional-dependencies.dev = { file = ["requirements/dev.unlock"] }
optional-dependencies.manage = { file = ["requirements/manage.unlock"] }
optional-dependencies.docs = { file = ["docs/requirements.unlock"] }\n# @@@ end\nzzzzzz\n# @@@ editable george\nhey there george\n# @@@ end\nzzzzzzz\n""",
        False,
    ),
    (
        "snippet_with_id_all_locked.txt",
        "ted",
        """zzzzzzzzzzzzz\n# @@@ editable ted\ndependencies = { file = ["requirements/prod.lock"] }
optional-dependencies.pip = { file = ["requirements/pip.lock"] }
optional-dependencies.pip_tools = { file = ["requirements/pip-tools.lock"] }
optional-dependencies.dev = { file = ["requirements/dev.lock"] }
optional-dependencies.manage = { file = ["requirements/manage.lock"] }
optional-dependencies.docs = { file = ["docs/requirements.lock"] }\n# @@@ end\nzzzzzz\n# @@@ editable george\nhey there george\n# @@@ end\nzzzzzzz\n""",
        True,
    ),
    (
        "snippet_with_id_unlocked_no_matches.txt",
        "ted",
        """zzzzzzzzzzzzz\n# @@@ editable ted\ndependencies = { file = ["requirements/prod.pip"] }
optional-dependencies.pip = { file = ["requirements/pip.pip"] }
optional-dependencies.pip_tools = { file = ["requirements/pip-tools.pip"] }
optional-dependencies.dev = { file = ["requirements/dev.pip"] }
optional-dependencies.manage = { file = ["requirements/manage.pip"] }
optional-dependencies.docs = { file = ["docs/requirements.pip"] }\n# @@@ end\nzzzzzz\n# @@@ editable george\nhey there george\n# @@@ end\nzzzzzzz\n""",
        False,
    ),
)
testdata_is_locked2 = (
    (
        Path(__file__).parent.joinpath(
            "_good_files",
            "complete.pyproject_toml",
        ),
        True,
    ),
    (
        Path(__file__).parent.joinpath(
            "_good_files",
            "complete-manage-pip-prod-unlock.pyproject_toml",
        ),
        False,
    ),
    pytest.param(
        Path(__file__).parent.joinpath(
            "_bad_files",
            "static_dependencies.pyproject_toml",
        ),
        None,
        marks=pytest.mark.xfail(raises=AssertionError),
    ),
)
ids_is_locked2 = (
    "Locked",
    "Unlocked",
    "static dependencies. no tool.setuptools.dynamic section",
)


@pytest.mark.parametrize(
    "path_config, expected",
    testdata_is_locked2,
    ids=ids_is_locked2,
)
def test_is_locked(path_config, expected, tmp_path, prep_pyproject_toml):
    # pytest --showlocals --log-level INFO -k "test_is_locked" -v tests
    # path_config invalids. Must be: pathlib.Path, absolute, to a file
    invalids = (
        1.1234,
        1,
        None,
    )
    for invalid in invalids:
        with pytest.raises(PyProjectTOMLReadError):
            BackendType.is_locked(invalid)

    # is_file_ok fails --> PyProjectTOMLReadError
    with pytest.raises(PyProjectTOMLReadError):
        BackendType.is_locked(tmp_path)

    # prepare
    #    does not check existance of requirements files
    path_config_in_tmp = prep_pyproject_toml(path_config, tmp_path)

    actual = BackendType.is_locked(path_config_in_tmp)
    assert actual is expected


def test_resolve_symlinks(tmp_path, prep_pyproject_toml, prepare_folders_files):
    # pytest --showlocals --log-level INFO -k "test_resolve_symlinks" -v tests
    path_config_src = Path(__file__).parent.joinpath(
        "_good_files",
        "complete-lnk-files.pyproject_toml",
    )
    path_f = prep_pyproject_toml(path_config_src, tmp_path)

    d_ins = {
        "prod": "requirements/prod.in",
        "pip": "requirements/pip.in",
        "tox": "requirements/tox.in",
        "manage": "requirements/manage.in",
    }
    seq_ins = list(d_ins.values())
    prepare_folders_files(seq_ins, tmp_path)

    seq_unlocks = (
        "requirements/prod.unlock",
        "requirements/pip.unlock",
        "requirements/tox.unlock",
        "requirements/manage.unlock",
        "requirements/prod.lock",
        "requirements/pip.lock",
        "requirements/tox.lock",
        "requirements/manage.lock",
    )
    prepare_folders_files(seq_unlocks, tmp_path)

    # order matters
    cmds = (
        (
            ("pipenv-unlock", "refresh", "--path", str(tmp_path), "--set-lock", "0"),
            False,
        ),
        (
            ("pipenv-unlock", "refresh", "--path", str(tmp_path), "--set-lock", "1"),
            True,
        ),
    )
    for cmd, expected in cmds:
        run_cmd(cmd, cwd=tmp_path)
        actual = BackendType.is_locked(path_f)
        assert actual is expected
