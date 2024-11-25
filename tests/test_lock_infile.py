"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

Unittest for lock_infile

Unit test -- Module

.. code-block:: shell

   python -m coverage run --source='drain_swamp.lock_infile' -m pytest \
   --showlocals tests/test_lock_infile.py && coverage report \
   --data-file=.coverage --include="**/lock_infile.py"

"""

import logging
import logging.config
import operator
import shutil
from collections.abc import Sequence
from contextlib import nullcontext as does_not_raise
from pathlib import (
    Path,
    PurePath,
)
from typing import cast

import pytest

from drain_swamp._safe_path import (
    fix_relpath,
    resolve_joinpath,
)
from drain_swamp.constants import (
    LOGGING,
    g_app_name,
)
from drain_swamp.exceptions import MissingRequirementsFoldersFiles
from drain_swamp.lock_datum import InFileType
from drain_swamp.lock_infile import (
    InFile,
    InFiles,
)
from drain_swamp.lock_util import replace_suffixes_last

testdata_resolve_one_iteration = (
    (
        (
            Path("requirements/prod.shared.in"),
            Path("requirements/pins.shared.in"),
            Path("requirements/pip.in"),
        ),
        0,
    ),
    (
        (
            Path("requirements/manage.in"),
            Path("requirements/tox.in"),
            Path("requirements/prod.shared.in"),
            Path("requirements/pins.shared.in"),
        ),
        1,
    ),
    (
        (Path("docs/pip-tools.in"),),
        1,
    ),
    (
        (
            Path("docs/pip-tools.in"),
            Path("requirements/pins.shared.in"),
        ),
        0,
    ),
)
ids_resolve_one_iteration = (
    "resolves within one loop",
    "takes two loops. After one loop, manage.in not resolved yet",
    "missing constraint requirements/pins.shared.in",
    "supplied missing contraint",
)


@pytest.mark.parametrize(
    "relpath_files, expected_unresolved",
    testdata_resolve_one_iteration,
    ids=ids_resolve_one_iteration,
)
def test_resolve_one_iteration(
    relpath_files,
    expected_unresolved,
    path_project_base,
    tmp_path,
    caplog,
    has_logging_occurred,
):
    """Does one loop iteration. Unresolved constraints are expected"""
    # pytest -vv --showlocals --log-level INFO -k "test_resolve_one_iteration" tests
    LOGGING["loggers"][g_app_name]["propagate"] = True
    logging.config.dictConfig(LOGGING)
    logger = logging.getLogger(name=g_app_name)
    logger.addHandler(hdlr=caplog.handler)
    caplog.handler.level = logger.level

    path_cwd = path_project_base()

    # prepare
    #    folders
    create_these = ("docs", "requirements")
    for create_relpath in create_these:
        path_dir = resolve_joinpath(tmp_path, create_relpath)
        path_dir.mkdir(parents=True, exist_ok=True)

    #    copy -t tmp_path relpath_files
    abspath_files = []
    for p_f in relpath_files:
        abspath_src = path_cwd.joinpath(p_f)
        abspath_dest = resolve_joinpath(tmp_path, p_f)
        logger.info(f"abspath_src: {abspath_src}")
        shutil.copy2(abspath_src, abspath_dest)
        logger.info(f"abspath_dest: {abspath_dest} {abspath_dest.is_file()}")
        abspath_files.append(abspath_dest)

    # act
    #    no attempt to resolve yet
    files = InFiles(tmp_path, abspath_files)
    files.move_zeroes()
    unresolved_before = files._files
    unresolved_before_count = len(unresolved_before)
    #    Check this test is non-trivial. There is resolving work to be done
    assert unresolved_before_count != 0

    # Only InFiles.resolution_loop raises MissingRequirementsFoldersFiles
    files.resolve_zeroes()
    unresolved_after = files._files
    unresolved_after_count = len(unresolved_after)
    #    Check resolve resolved everything
    assert unresolved_after_count == expected_unresolved


testdata_resolve_loop = (
    (
        (
            Path("requirements/prod.shared.in"),
            Path("requirements/pins.shared.in"),
            Path("requirements/pins-cffi.in"),
            Path("requirements/pip.in"),
        ),
        does_not_raise(),
    ),
    (
        (
            Path("requirements/manage.in"),
            Path("requirements/tox.in"),
            Path("requirements/prod.shared.in"),
            Path("requirements/pins.shared.in"),
            Path("requirements/pins-cffi.in"),
        ),
        does_not_raise(),
    ),
    (
        (
            Path("requirements/manage.in"),
            Path("requirements/prod.shared.in"),
            Path("requirements/pins.shared.in"),
            Path("requirements/pins-cffi.in"),
        ),
        does_not_raise(),
    ),
)
ids_resolve_loop = (
    "prod 0 pins 0 pip 1",
    "prod 0 pins 0 tox 1 manage 3",
    "discovers during resolution missing constraint",
)


@pytest.mark.parametrize(
    "relpath_files, expectation",
    testdata_resolve_loop,
    ids=ids_resolve_loop,
)
def test_resolve_loop(
    relpath_files,
    expectation,
    path_project_base,
    caplog,
    has_logging_occurred,
):
    """Resolve constraints raising error is unresolvable constraints."""
    # pytest --showlocals --log-level INFO -k "test_resolve_loop" tests
    LOGGING["loggers"][g_app_name]["propagate"] = True
    logging.config.dictConfig(LOGGING)
    logger = logging.getLogger(name=g_app_name)
    logger.addHandler(hdlr=caplog.handler)
    caplog.handler.level = logger.level

    assert isinstance(relpath_files, Sequence)

    # prepare
    abspath_files = []
    path_cwd = path_project_base()
    for p_f in relpath_files:
        abspath = path_cwd.joinpath(p_f)
        abspath_files.append(abspath)

    # act
    files = InFiles(path_cwd, abspath_files)
    with expectation:
        files.resolution_loop()
    # verify
    if isinstance(expectation, does_not_raise):
        #  No remaining InFile with unresolved constraints
        assert len(files._files) == 0
        zeroes_gen = files.zeroes
        zeroes = list(zeroes_gen)
        zeroes_count = len(zeroes)
        assert zeroes_count != 0

        # assert has_logging_occurred(caplog)
        pass


testdata_infile_instance = (
    (
        Path("requirements/pip.in"),
        ("requirements/pins.shared.in",),
        ("pip", "setuptools", "setuptools-scm"),
    ),
)
ids_infile_instance = ("pip.in 1 constraint 3 requirements",)


@pytest.mark.parametrize(
    "relpath, constraints, requirements",
    testdata_infile_instance,
    ids=ids_infile_instance,
)
def test_infile_instance(
    relpath,
    constraints,
    requirements,
    path_project_base,
):
    """InFiles calls check_relpath before call to InFile, which does no checks"""
    # pytest --showlocals --log-level INFO -k "test_infile_instance" tests
    # prepare
    path_cwd = path_project_base()
    set_constraints = {cons for cons in constraints}
    set_requirements = {reqs for reqs in requirements}

    # successful call
    in_ = InFile(relpath, relpath.stem, set_constraints, set_requirements)

    # act
    path_abs = in_.abspath(path_cwd)
    assert path_abs.is_absolute()
    assert path_abs.relative_to(path_cwd) == Path(in_.relpath)

    # eq -- str
    assert in_ == relpath
    assert in_ == str(relpath)

    # eq -- InFile
    set_ins = set()
    set_ins.add(in_)
    assert in_ == set_ins.pop()

    # eq -- unsupported type
    assert in_ != 1.1234


testdata_infile_badies = (
    (
        "requirements/prod.shared",
        "prod.shared",
    ),
    (
        "requirements/prod",
        "prod",
    ),
    (
        "requirements/prod.shared.frog",
        "prod.shared",
    ),
    (
        "requirements/prod.frog",
        "prod",
    ),
    (
        "requirements/prod.in",
        "george.shared",
    ),
    (
        "requirements/prod.shared.in",
        "prod.shared.in",
    ),
)
ids_infile_badies = (
    "no ENDING",
    "No suffixes",
    ".shared then unknown ENDING",
    "not .shared then unknown ENDING",
    "stem unrelated to relpath",
    "stem is not a stem. In relpath",
)


@pytest.mark.parametrize(
    "relpath, stem",
    testdata_infile_badies,
    ids=ids_infile_badies,
)
def test_infile_badies(relpath, stem):
    """Test InFile. Demonstrate invalid relpath.
    Much of this is redundant and covered by tests.test_lock_util:test_is_suffixes_ok
    """
    # pytest --showlocals --log-level INFO -k "test_infile_badies" tests
    with pytest.raises(ValueError):
        InFile(relpath, stem)


def test_cls_infiles_exceptions(
    tmp_path,
    path_project_base,
):
    """Verify InFiles exceptions."""
    # pytest --showlocals --log-level INFO -k "test_cls_infiles" tests
    path_cwd = path_project_base()
    # None or non-Sequence --> TypeError
    invalids_types = (
        None,
        1.2345,
    )
    for invalid in invalids_types:
        with pytest.raises(TypeError):
            InFiles(tmp_path, invalid)

    file_0_relpath = "does-not-exist.in"
    relpath_file_0 = Path(file_0_relpath)
    abspath_file_0 = resolve_joinpath(tmp_path, file_0_relpath)
    abspath_files_in = (abspath_file_0,)
    in_files = InFiles(tmp_path, abspath_files_in)
    assert relpath_file_0 not in in_files

    # file not relative to package base folder, won't be added
    abspath_file_0.touch()
    in_files = (abspath_file_0,)
    in_files = InFiles(path_cwd, in_files)
    assert relpath_file_0 not in in_files

    # constraints file does not exist
    abspath_file_0.write_text("-r requirements/secrets-to-time-travel.in\n\n")
    in_files = (abspath_file_0,)
    # Missing constraint file will not cause issue until InFiles.resolution_loop
    in_files = InFiles(tmp_path, in_files)


testdata_methods_infiles = (
    (
        Path("requirements/manage.in"),
        Path("requirements/tox.in"),
        Path("requirements/prod.shared.in"),
        Path("requirements/pins.shared.in"),
    ),
)
ids_methods_infiles = ("resolvable requirements constraints",)


@pytest.mark.parametrize(
    "relpath_files",
    testdata_methods_infiles,
    ids=ids_methods_infiles,
)
def test_methods_infiles(
    relpath_files,
    path_project_base,
    caplog,
    has_logging_occurred,
):
    """Verify InFiles methods."""
    # pytest --showlocals --log-level INFO -k "test_methods_infiles" tests
    LOGGING["loggers"][g_app_name]["propagate"] = True
    logging.config.dictConfig(LOGGING)
    logger = logging.getLogger(name=g_app_name)
    logger.addHandler(hdlr=caplog.handler)
    caplog.handler.level = logger.level

    assert isinstance(relpath_files, Sequence)

    # prepare
    #    Absolute path to requirements .in files
    abspath_files = []
    path_cwd = path_project_base()
    for relpath_f in relpath_files:
        assert issubclass(type(relpath_f), PurePath)
        abspath_f = path_cwd / relpath_f
        abspath_files.append(abspath_f)

    #    Parses .in files
    files = InFiles(path_cwd, abspath_files)

    check_files = (
        None,
        InFileType.FILES,
    )
    check_fors = (
        fix_relpath("requirements/tox.in"),
        Path(fix_relpath("requirements/tox.in")),
    )
    for checks_files in check_files:
        for check_for in check_fors:
            # InFiles.in_generic
            assert files.in_generic(check_for, set_name=checks_files) is True
            # InFiles.__contains__
            assert check_for in files
            # InFiles.get_by_relpath
            in_ = files.get_by_relpath(check_for, set_name=checks_files)
            assert isinstance(in_, InFile)

        # unsupported type
        invalids = (
            None,
            (fix_relpath("requirements/goose-meat.in"),),
        )
        for invalid in invalids:
            with pytest.raises(ValueError):
                files.get_by_relpath(invalid, set_name=checks_files)

        # nonexistent file
        check_for = fix_relpath("requirements/goose-meat.in")
        in_ = files.get_by_relpath(check_for, set_name=checks_files)
        assert in_ is None
    # assert has_logging_occurred(caplog)
    pass


def test_infiletype():
    """Explore InFileType enum."""
    # pytest --showlocals --log-level INFO -k "test_infiletype" tests
    # __eq__
    ift = InFileType.FILES
    assert ift == InFileType.FILES
    assert ift != InFileType.ZEROES
    # __str__
    #    InFiles._files instance attribute
    infiles_attr_name = "_files"
    assert str(InFileType.FILES) == infiles_attr_name


testdata_infiles_write = (
    (
        (Path(__file__).parent.joinpath("_req_files", "prod.shared.in"),),
        (Path(__file__).parent.joinpath("_req_files", "prod.shared.unlock"),),
        (),
        "requirements",
        does_not_raise(),
        1,
    ),
    (
        (Path(__file__).parent.parent.joinpath("requirements", "manage.in"),),
        (Path(__file__).parent.parent.joinpath("requirements", "manage.unlock"),),
        (),
        "requirements",
        pytest.raises(MissingRequirementsFoldersFiles),
        0,
    ),
    (
        (Path(__file__).parent.parent.joinpath("requirements", "manage.in"),),
        (Path(__file__).parent.parent.joinpath("requirements", "manage.unlock"),),
        (
            "requirements/pins.shared.in",
            "requirements/pins-cffi.in",
            "requirements/prod.shared.in",
            "requirements/tox.in",
        ),
        "requirements",
        does_not_raise(),
        4,
    ),
)
ids_infiles_write = (
    "Create an .shared.unlock file",
    "missing requirements and constraints files",
    "create only manage.unlock",
)


@pytest.mark.parametrize(
    (
        "abspath_ins, abspath_outs, support_relpaths, dest_relpath, "
        "expectation, unlock_count_expected"
    ),
    testdata_infiles_write,
    ids=ids_infiles_write,
)
def test_infiles_write(
    abspath_ins,
    abspath_outs,
    support_relpaths,
    dest_relpath,
    expectation,
    unlock_count_expected,
    path_project_base,
    prep_pyproject_toml,
    tmp_path,
    caplog,
):
    """Convert .in --> .unlock file(s)."""
    # pytest --showlocals --log-level INFO -k "test_infiles_write" tests
    # pytest --showlocals tests/test_lock_infile.py::test_infiles_write[create\ only\ manage.unlock]

    LOGGING["loggers"][g_app_name]["propagate"] = True
    logging.config.dictConfig(LOGGING)
    logger = logging.getLogger(name=g_app_name)
    logger.addHandler(hdlr=caplog.handler)
    caplog.handler.level = logger.level

    path_cwd = path_project_base()

    # prepare
    #    dest folder
    abspath_dest_dir = cast("Path", resolve_joinpath(tmp_path, dest_relpath))
    abspath_dest_dir.mkdir()

    #    InFiles
    in_files = []
    for abspath_in in abspath_ins:
        src_abspath = str(abspath_in)
        abspath_dest = cast("Path", resolve_joinpath(abspath_dest_dir, abspath_in.name))
        in_files.append(abspath_dest)
        shutil.copy(src_abspath, abspath_dest)
    # in_files_count = len(in_files)
    pass

    # support .in files
    for support_relpath in support_relpaths:
        abspath_src_support = cast("Path", resolve_joinpath(path_cwd, support_relpath))
        abspath_src_support_in = replace_suffixes_last(abspath_src_support, ".in")
        src_support_in_abspath = str(abspath_src_support_in)
        abspath_dest_support = cast("Path", resolve_joinpath(tmp_path, support_relpath))
        abspath_dest_support_in = replace_suffixes_last(abspath_dest_support, ".in")
        shutil.copy(src_support_in_abspath, abspath_dest_support_in)

    # Act
    with expectation:
        files = InFiles(tmp_path, in_files)
        files.resolution_loop()
    if isinstance(expectation, does_not_raise):
        gen = files.write()
        # Verify
        lst_called = list(gen)
        unlock_count_actual = len(lst_called)
        assert unlock_count_expected == unlock_count_actual
        #    confirm file exists
        for abspath_unlock in lst_called:
            assert abspath_unlock.exists() and abspath_unlock.is_file()
        # No check yet for file regression
        pass


testdata_infile_sort = (
    (
        (
            "requirements/pip-tools.in",
            "doc/pip-tools.in",
            "requirements/pip.in",
            "requirements/prod.shared.in",
            "requirements/dev.in",
        ),
        (
            "requirements/dev.in",
            "requirements/pip.in",
            "doc/pip-tools.in",
            "requirements/pip-tools.in",
            "requirements/prod.shared.in",
        ),
    ),
)
ids_infile_sort = ("requirements files from multiple folders",)


@pytest.mark.parametrize(
    "relpaths, expected_order",
    testdata_infile_sort,
    ids=ids_infile_sort,
)
def test_infile_sort(relpaths, expected_order, tmp_path, caplog):
    """On InFile, test built-in function sorted."""
    # pytest --showlocals --log-level INFO -k "test_infile_sort" tests
    LOGGING["loggers"][g_app_name]["propagate"] = True
    logging.config.dictConfig(LOGGING)
    logger = logging.getLogger(name=g_app_name)
    logger.addHandler(hdlr=caplog.handler)
    caplog.handler.level = logger.level

    # Compares hash(stem, relpath)
    in_a = InFile("docs/pip-tools.in", "pip-tools")
    in_b = InFile("requirements/pip-tools.in", "pip-tools")
    assert in_a < in_b

    """Unsupported type comparisons --> TypeError. Eventhough
    InFile.__gt__ is not implemented"""
    a_and_b = (
        (4, in_b, operator.lt),
        (in_b, 4, operator.gt),
    )
    for a, b, oper in a_and_b:
        with pytest.raises(TypeError):
            oper(a, b)

    # right is not an InFile --> TypeError
    invalids = (
        None,
        1.2345,
    )
    for right in invalids:
        with pytest.raises(TypeError):
            in_a.__lt__(right)

    # prepare
    # empty InFiles
    in_files = InFiles(tmp_path, [])

    for f_relpath in relpaths:
        abspath_f = cast("Path", resolve_joinpath(tmp_path, f_relpath))
        abspath_f_in = replace_suffixes_last(abspath_f, ".in")
        abspath_f_in.parent.mkdir(parents=True, exist_ok=True)
        abspath_f.touch()
        stem_f = abspath_f_in.stem

        relpath_f_in = abspath_f_in.relative_to(tmp_path)

        in_ = InFile(relpath_f_in, stem_f)
        # append an InFile to InFiles
        in_files.file = in_

    # act
    #    Requires InFile to implement __hash__, __eq__, and __lt__
    ins_sorted = sorted(in_files.files)
    assert isinstance(ins_sorted, Sequence)
    assert not isinstance(ins_sorted, InFiles)
    # verify
    #    In expected order. Not possible for there to have been duplicates
    for idx, in_ in ins_sorted:
        relpath_expected = expected_order[idx]
        abspath_g = cast("Path", resolve_joinpath(tmp_path, relpath_expected))
        abspath_g_in = replace_suffixes_last(abspath_g, ".in")
        relpath_g_in = abspath_g_in.relative_to(tmp_path)
        assert Path(in_.relpath) == relpath_g_in
