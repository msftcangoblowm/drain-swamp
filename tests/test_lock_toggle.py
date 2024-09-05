"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

..

Unittest for module, drain_swamp.lock_toggle

Unit test -- Module

.. code-block:: shell

   python -m coverage run --source='drain_swamp.lock_toggle' -m pytest \
   --showlocals tests/test_lock_toggle.py && coverage report \
   --data-file=.coverage --include="**/lock_toggle.py"

Integration test

.. code-block:: shell

   make coverage
   pytest --showlocals --cov="drain_swamp" --cov-report=term-missing \
   --cov-config=pyproject.toml tests

"""

import importlib.util
import logging
import logging.config
import shutil
from collections.abc import Sequence
from contextlib import nullcontext as does_not_raise
from pathlib import (
    Path,
    PurePath,
)
from unittest.mock import patch

import pytest

from drain_swamp._safe_path import resolve_path
from drain_swamp.backend_abc import BackendType
from drain_swamp.backend_setuptools import BackendSetupTools  # noqa: F401
from drain_swamp.constants import (
    LOGGING,
    g_app_name,
)
from drain_swamp.exceptions import MissingRequirementsFoldersFiles
from drain_swamp.lock_toggle import (
    InFile,
    InFiles,
    InFileType,
    _create_symlinks_relative,
    _maintain_symlink,
    _postprocess_abspath_to_relpath,
    lock_compile,
    refresh_links,
    unlock_compile,
)


@pytest.fixture
def cleanup_symlinks(tmp_path):
    """Fixture to cleanup .lnk symlinks."""

    def func(seq_expected, is_verify):
        """Verify symlinks optional.

        :param seq_expected: Sequence of relative path
        :type seq_expected: collections.abc.Sequence[pathlib.Path]
        :param is_verify: True to first assert symlink exists
        :type is_verify: bool
        """
        for relpath_expected in seq_expected:
            abspath_expected = tmp_path.joinpath(relpath_expected)
            is_symlinks_exist = (
                abspath_expected.exists() and abspath_expected.is_symlink()
            )
            is_very_verify = (
                is_verify is not None
                and isinstance(is_verify, bool)
                and is_verify is True
            )
            if is_very_verify:
                assert is_symlinks_exist
            if is_symlinks_exist:
                # clean up symlink
                abspath_expected.unlink()
                assert not abspath_expected.exists()

    return func


testdata_lock_compile = (
    (
        Path(__file__).parent.joinpath("_good_files", "complete.pyproject_toml"),
        (
            "requirements/prod.in",
            "requirements/pip.in",
            "requirements/pip-tools.in",
            "requirements/dev.in",
            "requirements/manage.in",
            "docs/requirements.in",
        ),
        (),
    ),
    (
        Path(__file__).parent.joinpath("_good_files", "complete.pyproject_toml"),
        (
            "requirements/prod.in",
            "requirements/pip.in",
            "requirements/pip-tools.in",
            "requirements/dev.in",
            "requirements/manage.in",
            "docs/requirements.in",
            "ci/tox.in",
        ),
        (Path("ci"),),
    ),
)
ids_lock_compile = (
    "Without extra folders",
    "With additional folder, ci",
)


@pytest.mark.skipif(
    importlib.util.find_spec("piptools") is None,
    reason="uses pip-compile part of pip-tools",
)
@pytest.mark.parametrize(
    "path_config, seq_create_these, additional_folders",
    testdata_lock_compile,
    ids=ids_lock_compile,
)
def test_lock_compile(
    path_config,
    seq_create_these,
    additional_folders,
    tmp_path,
    prepare_folders_files,
    prep_pyproject_toml,
    caplog,
    has_logging_occurred,
):
    """Test creating dependency lock file."""
    # pytest --showlocals --log-level INFO -k "test_lock_compile" tests
    LOGGING["loggers"][g_app_name]["propagate"] = True
    logging.config.dictConfig(LOGGING)
    logger = logging.getLogger(name=g_app_name)
    logger.addHandler(hdlr=caplog.handler)
    caplog.handler.level = logger.level

    # prepare (required and optionals .in files)
    prepare_folders_files(seq_create_these, tmp_path)
    path_config_dest = prep_pyproject_toml(path_config, tmp_path)

    inst = BackendType.load_factory(
        path_config_dest,
        parent_dir=tmp_path,
        additional_folders=additional_folders,
    )

    expected = list(inst.in_files())
    expected_count = len(expected)

    # dry run. Thank you /bin/true
    with patch(
        f"{g_app_name}.lock_toggle.resolve_path",
        return_value=resolve_path("true"),
    ):
        gen_lock_files = lock_compile(inst)
        actual_count = len(list(gen_lock_files))
        assert actual_count == 0

    # lock_compile
    gen_lock_files = lock_compile(inst)
    actual_count = len(list(gen_lock_files))
    # assert has_logging_occurred(caplog)
    assert expected_count == actual_count


testdata_resolve_one_iteration = (
    (
        (
            Path("requirements/prod.in"),
            Path("requirements/pins.in"),
            Path("requirements/pip.in"),
        ),
        0,
    ),
    (
        (
            Path("requirements/manage.in"),
            Path("requirements/tox.in"),
            Path("requirements/prod.in"),
            Path("requirements/pins.in"),
        ),
        1,
    ),
)
ids_resolve_one_iteration = (
    "resolves within one loop",
    "takes two loops. After one loop, manage.in not resolved yet",
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
    caplog,
    has_logging_occurred,
):
    """Does one loop iteration. Unresolved constraints are expected"""
    # pytest --showlocals --log-level INFO -k "test_resolve_one_iteration" tests
    LOGGING["loggers"][g_app_name]["propagate"] = True
    logging.config.dictConfig(LOGGING)
    logger = logging.getLogger(name=g_app_name)
    logger.addHandler(hdlr=caplog.handler)
    caplog.handler.level = logger.level

    # prepare
    abspath_files = []
    path_cwd = path_project_base()
    for p_f in relpath_files:
        abspath = path_cwd.joinpath(p_f)
        abspath_files.append(abspath)

    # act
    files = InFiles(path_cwd, abspath_files)

    #    no resolution has been attempted yet
    files.move_zeroes()

    unresolved_before_count = len(files._files)

    #    Check this test is non-trivial. There is resolving work to be done
    assert unresolved_before_count != 0

    files.resolve_zeroes()
    unresolved_after_count = len(files._files)

    #    Check resolve resolved everything
    assert unresolved_after_count == expected_unresolved

    # assert has_logging_occurred(caplog)
    pass


testdata_resolve_loop = (
    (
        (
            Path("requirements/prod.in"),
            Path("requirements/pins.in"),
            Path("requirements/pip.in"),
        ),
        does_not_raise(),
    ),
    (
        (
            Path("requirements/manage.in"),
            Path("requirements/tox.in"),
            Path("requirements/prod.in"),
            Path("requirements/pins.in"),
        ),
        does_not_raise(),
    ),
    (
        (
            Path("requirements/manage.in"),
            Path("requirements/prod.in"),
            Path("requirements/pins.in"),
        ),
        pytest.raises(MissingRequirementsFoldersFiles),
    ),
)
ids_resolve_loop = (
    "prod 0 pins 0 pip 1",
    "prod 0 pins 0 tox 1 manage 3",
    "tox constraint file missing",
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
    with expectation:
        files = InFiles(path_cwd, abspath_files)
        files.resolution_loop()
    # verify
    if isinstance(expectation, does_not_raise):
        #  No remaining InFile with unresolved constraints
        assert len(files._files) == 0

        # assert has_logging_occurred(caplog)
        pass


testdata_infile = (
    (
        Path("requirements/pip.in"),
        ("requirements/pins.in",),
        ("pip", "setuptools", "setuptools-scm"),
    ),
)
ids_infile = ("pip.in 1 constraint 3 requirements",)


@pytest.mark.parametrize(
    "relpath, constraints, requirements",
    testdata_infile,
    ids=ids_infile,
)
def test_infile(
    relpath,
    constraints,
    requirements,
    path_project_base,
):
    """InFiles calls check_path before call to InFile, which does no checks"""
    # pytest --showlocals --log-level INFO -k "test_infile" tests
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


def test_cls_infiles_exceptions(
    tmp_path,
    path_project_base,
):
    """Verify InFiles exceptions."""
    # pytest --showlocals --log-level INFO -k "test_cls_infiles" tests
    path_cwd = path_project_base()
    # Expecting a sequence or sequence contains unsupported type
    invalids_types = (
        None,
        1.2345,
        (None,),
        (1.2345,),
        ("Hello World!",),
    )
    for invalid in invalids_types:
        with pytest.raises(TypeError):
            InFiles(tmp_path, invalid)

    abspath_file_0 = tmp_path.joinpath("does-not-exist.in")
    with pytest.raises(FileNotFoundError):
        in_files = (abspath_file_0,)
        InFiles(tmp_path, in_files)

    # file not relative to package base folder
    abspath_file_0.touch()
    with pytest.raises(ValueError):
        in_files = (abspath_file_0,)
        InFiles(path_cwd, in_files)

    # constraints file does not exist
    abspath_file_0.write_text("-r requirements/secrets-to-time-travel.in\n\n")
    in_files = (abspath_file_0,)
    with pytest.raises(MissingRequirementsFoldersFiles):
        InFiles(tmp_path, in_files)


testdata_methods_infiles = (
    (
        Path("requirements/manage.in"),
        Path("requirements/tox.in"),
        Path("requirements/prod.in"),
        Path("requirements/pins.in"),
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
        "requirements/tox.in",
        Path("requirements/tox.in"),
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
            ("requirements/goose-meat.in",),
        )
        for invalid in invalids:
            with pytest.raises(ValueError):
                files.get_by_relpath(invalid, set_name=checks_files)

        # nonexistent file
        check_for = "requirements/goose-meat.in"
        in_ = files.get_by_relpath(check_for, set_name=checks_files)
        assert in_ is None
    # assert has_logging_occurred(caplog)
    pass


testdata_unlock_compile = (
    pytest.param(
        Path(__file__).parent.joinpath(
            "_good_files", "complete-manage-pip-prod-unlock.pyproject_toml"
        ),
        (
            "requirements/prod.in",
            "requirements/pins.in",
            "requirements/pip.in",
            "requirements/manage.in",
        ),
        (),
        pytest.raises(MissingRequirementsFoldersFiles),
    ),
    (
        Path(__file__).parent.joinpath(
            "_good_files", "complete-manage-pip-prod-unlock.pyproject_toml"
        ),
        (
            "requirements/prod.in",
            "requirements/pins.in",
            "requirements/tox.in",
            "requirements/manage.in",
        ),
        (),
        does_not_raise(),
    ),
    (
        Path(__file__).parent.joinpath("_good_files", "complete.pyproject_toml"),
        (
            "requirements/prod.in",
            "requirements/pins.in",
            "requirements/pip.in",
            "requirements/pip-tools.in",
            "requirements/dev.in",
            "requirements/tox.in",
            "requirements/manage.in",
            "docs/requirements.in",
        ),
        (),
        does_not_raise(),
    ),
)
ids_unlock_compile = (
    "missing tox",
    "manage and tox",
    "constraint path needs to be resolved",
)


@pytest.mark.parametrize(
    "path_config, seq_create_these, additional_folders, expectation",
    testdata_unlock_compile,
    ids=ids_unlock_compile,
)
def test_unlock_compile(
    path_config,
    seq_create_these,
    additional_folders,
    expectation,
    tmp_path,
    prepare_folders_files,
    prep_pyproject_toml,
    path_project_base,
    caplog,
    has_logging_occurred,
):
    """Create .unlock files."""
    # pytest --showlocals --log-level INFO -k "test_unlock_compile" tests
    LOGGING["loggers"][g_app_name]["propagate"] = True
    logging.config.dictConfig(LOGGING)
    logger = logging.getLogger(name=g_app_name)
    logger.addHandler(hdlr=caplog.handler)
    caplog.handler.level = logger.level

    # prepare
    assert isinstance(seq_create_these, Sequence)
    #    makes both folders and files, but blank files
    prepare_folders_files(seq_create_these, tmp_path)

    #    move real files, no need to create folders
    path_cwd = path_project_base()
    for p_f in seq_create_these:
        abspath_src = path_cwd.joinpath(p_f)
        abspath_dest = tmp_path.joinpath(p_f)
        shutil.copy2(abspath_src, abspath_dest)
        # abspath_files.append(abspath_dest)
        pass

    path_config_dest = prep_pyproject_toml(path_config, tmp_path)

    # prepare (required and optionals .in files)
    inst = BackendType.load_factory(
        path_config_dest,
        parent_dir=tmp_path,
        additional_folders=additional_folders,
    )
    assert inst.parent_dir == tmp_path

    expected = list(inst.in_files())
    expected_count = len(expected)

    # unlock_compile
    with expectation:
        gen = unlock_compile(inst)
        unlock_files = list(gen)
    if isinstance(expectation, does_not_raise):
        unlock_files_count = len(unlock_files)
        assert expected_count - 1 == unlock_files_count

        # assert has_logging_occurred(caplog)
        pass


def test_create_symlinks_relative(tmp_path, prepare_folders_files, caplog):
    """.lnk files symlinks are relative, not absolute."""
    # pytest --showlocals --log-level INFO -k "test_create_symlinks_relative" tests
    LOGGING["loggers"][g_app_name]["propagate"] = True
    logging.config.dictConfig(LOGGING)
    logger = logging.getLogger(name=g_app_name)
    logger.addHandler(hdlr=caplog.handler)
    caplog.handler.level = logger.level

    src_abspath = tmp_path.joinpath("src.py")

    # NotADirectoryError (cwd)
    src = "hi-there"
    dest = "hello.lnk"
    with pytest.raises(NotADirectoryError):
        _create_symlinks_relative(src, dest, src_abspath)

    with pytest.raises(NotADirectoryError):
        _maintain_symlink(src_abspath, src_abspath)

    # FileNotFoundError (src)
    with pytest.raises(FileNotFoundError):
        _create_symlinks_relative(src, dest, tmp_path)

    with pytest.raises(FileNotFoundError):
        _maintain_symlink(tmp_path, src_abspath)

    # ValueError (dest suffix wrong)
    # _maintain_symlink does produce a ValueError
    path_src = tmp_path.joinpath(src)
    path_src.touch()
    dest = "hello.txt"
    with pytest.raises(ValueError):
        _create_symlinks_relative(src, dest, tmp_path)

    # Success case
    src = "requirements/hi-there.unlock"
    src_abspath = tmp_path.joinpath(src)
    dest = "hi-there.lnk"
    prepare_folders_files((src,), tmp_path)
    _create_symlinks_relative(src, dest, tmp_path)
    path_dest_expected = tmp_path.joinpath("requirements", dest)
    is_symlink = path_dest_expected.is_symlink()
    assert is_symlink
    assert path_dest_expected.resolve() == tmp_path.joinpath(src)
    path_dest_expected.unlink()
    assert not path_dest_expected.exists()

    _maintain_symlink(tmp_path, src_abspath)
    is_symlink = path_dest_expected.is_symlink()
    assert is_symlink
    assert path_dest_expected.resolve() == tmp_path.joinpath(src)
    path_dest_expected.unlink()
    assert not path_dest_expected.exists()

    # os.symlink not supported on this platform --> NotImplementedError
    src = "requirements/yo.lock"
    src_abspath = tmp_path.joinpath(src)
    prepare_folders_files((src,), tmp_path)
    dest = "yo.lnk"
    with (
        patch("os.symlink", side_effect=NotImplementedError),
        pytest.raises(NotImplementedError),
    ):
        _create_symlinks_relative(src, dest, tmp_path)
    with (
        patch("os.symlink", side_effect=NotImplementedError),
        pytest.raises(NotImplementedError),
    ):
        _maintain_symlink(tmp_path, src_abspath)


testdata_refresh = (
    (
        Path(__file__).parent.joinpath(
            "_bad_files", "static_dependencies.pyproject_toml"
        ),
        (
            "requirements/prod.in",
            "requirements/pins.in",
            "requirements/pip.in",
            "requirements/tox.in",
            "requirements/manage.in",
        ),
        (
            "requirements/prod.lock",
            "requirements/pip.lock",
            "requirements/tox.lock",
            "requirements/manage.lock",
            "requirements/prod.unlock",
            "requirements/pip.unlock",
            "requirements/tox.unlock",
            "requirements/manage.unlock",
        ),
        (
            "requirements/prod.lnk",
            "requirements/pip.lnk",
            "requirements/tox.lnk",
            "requirements/manage.lnk",
        ),
        pytest.raises(AssertionError),
    ),
    (
        Path(__file__).parent.joinpath(
            "_good_files", "complete-manage-pip-prod-unlock.pyproject_toml"
        ),
        (
            "requirements/prod.in",
            "requirements/pins.in",
            "requirements/pip.in",
            "requirements/manage.in",
        ),
        (
            "requirements/prod.lock",
            "requirements/pip.lock",
            "requirements/manage.lock",
            "requirements/prod.unlock",
            "requirements/pip.unlock",
            "requirements/manage.unlock",
        ),
        (
            "requirements/prod.lnk",
            "requirements/pip.lnk",
            "requirements/manage.lnk",
        ),
        pytest.raises(MissingRequirementsFoldersFiles),
    ),
    (
        Path(__file__).parent.joinpath(
            "_good_files", "complete-manage-pip-prod-unlock.pyproject_toml"
        ),
        (
            "requirements/prod.in",
            "requirements/pins.in",
            "requirements/tox.in",
            "requirements/manage.in",
        ),
        (
            "requirements/prod.lock",
            "requirements/tox.lock",
            "requirements/manage.lock",
            "requirements/prod.unlock",
            "requirements/tox.unlock",
            "requirements/manage.unlock",
        ),
        (
            "requirements/prod.lnk",
            "requirements/tox.lnk",
            "requirements/manage.lnk",
        ),
        does_not_raise(),
    ),
    (
        Path(__file__).parent.joinpath("_good_files", "complete.pyproject_toml"),
        (
            "requirements/prod.in",
            "requirements/pins.in",
            "requirements/pip.in",
            "requirements/pip-tools.in",
            "requirements/dev.in",
            "requirements/tox.in",
            "requirements/manage.in",
            "docs/requirements.in",
        ),
        (
            "requirements/prod.lock",
            "requirements/pip.lock",
            "requirements/pip-tools.lock",
            "requirements/dev.lock",
            "requirements/tox.lock",
            "requirements/manage.lock",
            "docs/requirements.lock",
            "requirements/prod.unlock",
            "requirements/pip.unlock",
            "requirements/pip-tools.unlock",
            "requirements/dev.unlock",
            "requirements/tox.unlock",
            "requirements/manage.unlock",
            "docs/requirements.unlock",
        ),
        (
            "requirements/prod.lnk",
            "requirements/pip.lnk",
            "requirements/pip-tools.lnk",
            "requirements/dev.lnk",
            "requirements/tox.lnk",
            "requirements/manage.lnk",
            "docs/requirements.lnk",
        ),
        does_not_raise(),
    ),
)
ids_refresh = (
    "missing tox",
    "pyproject.toml dependencies are static, not dynamic",
    "manage and tox",
    "constraint path needs to be resolved",
)


@pytest.mark.parametrize(
    "path_pyproject_toml, seq_create_in_files, seq_create_lock_files, seq_expected, expectation",
    testdata_refresh,
    ids=ids_refresh,
)
def test_refresh_links(
    path_pyproject_toml,
    seq_create_in_files,
    seq_create_lock_files,
    seq_expected,
    expectation,
    tmp_path,
    prepare_folders_files,
    prep_pyproject_toml,
    path_project_base,
    caplog,
    has_logging_occurred,
    cleanup_symlinks,
):
    """Test refresh .lnk files.

    Assumes .lock or .unlock files exists."""
    # pytest --showlocals --log-level INFO -k "test_refresh_links" tests
    LOGGING["loggers"][g_app_name]["propagate"] = True
    logging.config.dictConfig(LOGGING)
    logger = logging.getLogger(name=g_app_name)
    logger.addHandler(hdlr=caplog.handler)
    caplog.handler.level = logger.level

    path_config = prep_pyproject_toml(path_pyproject_toml, tmp_path)

    # prepare
    assert isinstance(seq_create_in_files, Sequence)
    assert isinstance(seq_create_lock_files, Sequence)

    # prepare .in
    prepare_folders_files(seq_create_in_files, tmp_path)
    #    move real files, no need to create folders
    path_cwd = path_project_base()
    for p_f in seq_create_in_files:
        abspath_src = path_cwd.joinpath(p_f)
        abspath_dest = tmp_path.joinpath(p_f)
        shutil.copy2(abspath_src, abspath_dest)
        # abspath_files.append(abspath_dest)
        pass

    # No .lock file
    #    prepare (required and optionals .in files)
    inst = BackendType.load_factory(
        path_config,
        parent_dir=tmp_path,
    )
    assert inst.parent_dir == tmp_path
    with pytest.raises(MissingRequirementsFoldersFiles):
        refresh_links(inst, is_set_lock=True)
    del inst

    # prepare .lock
    prepare_folders_files(seq_create_lock_files, tmp_path)
    #    move real files, no need to create folders
    for p_f in seq_create_lock_files:
        abspath_src = path_cwd.joinpath(p_f)
        abspath_dest = tmp_path.joinpath(p_f)
        shutil.copy2(abspath_src, abspath_dest)
        # abspath_files.append(abspath_dest)
        pass

    # prepare (required and optionals .in files)
    inst = BackendType.load_factory(
        path_config,
        parent_dir=tmp_path,
    )
    assert inst.parent_dir == tmp_path

    invalids = (
        0.1,
        "Hello world",
    )
    for invalid in invalids:
        with pytest.raises(TypeError):
            refresh_links(inst, is_set_lock=invalid)

    # None
    valid = None
    with expectation as excinfo:
        refresh_links(inst, is_set_lock=valid)
    if excinfo is None:
        excinfo_type = None
    else:
        excinfo_type = excinfo.type
    is_applies_only_to_none = False
    if excinfo_type is not None and excinfo_type == AssertionError:
        cleanup_symlinks(seq_expected, False)
        is_applies_only_to_none = True
    elif excinfo_type is not None and excinfo_type == MissingRequirementsFoldersFiles:
        cleanup_symlinks(seq_expected, False)
    else:
        cleanup_symlinks(seq_expected, True)

    if is_applies_only_to_none is True:
        cm = does_not_raise()
    else:
        cm = expectation

    valids = (
        True,
        False,
    )
    for valid in valids:
        with cm:
            refresh_links(inst, is_set_lock=valid)

            # verify symlinks
            cleanup_symlinks(seq_expected, False)

    # assert has_logging_occurred(caplog)
    pass


def test_postprocess_abspath_to_relpath(tmp_path, prepare_folders_files):
    """When creating .lock files post processer abs path --> relative path."""
    # pytest --showlocals --log-level INFO -k "test_postprocess_abspath_to_relpath" tests
    # prepare
    #    .in
    seq_create_in_files = (
        "requirements/prod.in",
        "docs/requirements.in",
    )
    prepare_folders_files(seq_create_in_files, tmp_path)

    #    .lock
    lines = (
        "#\n"
        "click==8.1.7\n"
        "    # via\n"
        f"    #   -c {tmp_path!s}/docs/../requirements/prod.in\n"
        "    #   click-log\n"
        "    #   scriv\n"
        "    #   sphinx-external-toc-strict\n"
        "    #   uvicorn\n"
        "sphobjinv==2.3.1.1\n"
        f"    # via -r {tmp_path!s}/docs/requirements.in\n\n"
    )
    expected = (
        "#\n"
        "click==8.1.7\n"
        "    # via\n"
        "    #   -c docs/../requirements/prod.in\n"
        "    #   click-log\n"
        "    #   scriv\n"
        "    #   sphinx-external-toc-strict\n"
        "    #   uvicorn\n"
        "sphobjinv==2.3.1.1\n"
        "    # via -r docs/requirements.in\n\n"
    )

    path_doc_lock = tmp_path.joinpath("docs", "requirements.lock")
    path_doc_lock.write_text(lines)

    # act
    _postprocess_abspath_to_relpath(path_doc_lock, tmp_path)

    # verify
    #    Within file contents, absolute path of parent folder is absent
    contents = path_doc_lock.read_text()
    is_not_occur_once = str(tmp_path) not in contents
    assert is_not_occur_once is True
    assert contents == expected


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
