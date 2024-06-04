"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

..

Unittest for module, drain_swamp.lock_toggle

Without coverage

.. code-block:: shell

   pytest --showlocals --log-level INFO tests/test_lock_toggle.py

With coverage

.. code-block:: shell

   pytest --showlocals --cov="drain_swamp" --cov-report=term-missing tests/test_lock_toggle.py

"""

import logging
import logging.config
import pkgutil
import shutil
from collections.abc import Sequence
from pathlib import Path
from unittest.mock import patch

import pytest

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
    lock_compile,
    unlock_compile,
)

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
    pkgutil.find_loader("piptools") is None,
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
    caplog,
    has_logging_occurred,
):
    # pytest --showlocals --log-level INFO -k "test_lock_compile" tests
    LOGGING["loggers"][g_app_name]["propagate"] = True
    logging.config.dictConfig(LOGGING)
    logger = logging.getLogger(name=g_app_name)
    logger.addHandler(hdlr=caplog.handler)
    caplog.handler.level = logger.level

    # prepare (required and optionals .in files)
    prepare_folders_files(seq_create_these, tmp_path)

    inst = BackendType.load_factory(
        path_config,
        parent_dir=tmp_path,
        additional_folders=additional_folders,
    )

    expected = list(inst.in_files())
    expected_count = len(expected)

    # dry run. Thank you /bin/true
    with (patch(f"{g_app_name}.lock_toggle.PATH_PIP_COMPILE", Path("/bin/true")),):
        gen_lock_files = lock_compile(inst)
        actual_count = len(list(gen_lock_files))
        assert actual_count == 0

    # lock_compile
    gen_lock_files = lock_compile(inst)
    actual_count = len(list(gen_lock_files))
    assert has_logging_occurred(caplog)
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
    "prod 0 pins 0 pip 1",
    "prod 0 pins 0 tox 1 manage 3",
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

    assert has_logging_occurred(caplog)


testdata_resolve_loop = (
    (
        Path("requirements/prod.in"),
        Path("requirements/pins.in"),
        Path("requirements/pip.in"),
    ),
    (
        Path("requirements/manage.in"),
        Path("requirements/tox.in"),
        Path("requirements/prod.in"),
        Path("requirements/pins.in"),
    ),
    pytest.param(
        (
            Path("requirements/manage.in"),
            Path("requirements/prod.in"),
            Path("requirements/pins.in"),
        ),
        marks=pytest.mark.xfail(raises=MissingRequirementsFoldersFiles),
    ),
)
ids_resolve_loop = (
    "prod 0 pins 0 pip 1",
    "prod 0 pins 0 tox 1 manage 3",
    "tox constraint file missing",
)


@pytest.mark.parametrize(
    "relpath_files",
    testdata_resolve_loop,
    ids=ids_resolve_loop,
)
def test_resolve_loop(
    relpath_files,
    path_project_base,
    caplog,
    has_logging_occurred,
):
    """Resolve constraints raising error is unresolvable constraints"""
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
    files.resolution_loop()
    #  No remaining InFile with unresolved constraints
    assert len(files._files) == 0

    assert has_logging_occurred(caplog)


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
    abspath_file_0.write_text("-c requirements/secrets-to-time-travel.in\n\n")
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
):
    # pytest --showlocals --log-level INFO -k "test_methods_infiles" tests
    assert isinstance(relpath_files, Sequence)

    # prepare
    abspath_files = []
    path_cwd = path_project_base()
    for p_f in relpath_files:
        abspath = path_cwd.joinpath(p_f)
        abspath_files.append(abspath)

    files = InFiles(path_cwd, abspath_files)
    check_files = (
        None,
        "files",
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


testdata_unlock_compile = (
    pytest.param(
        Path(__file__).parent.joinpath(
            "_good_files", "complete-manage-pip-prod.pyproject_toml"
        ),
        (
            "requirements/prod.in",
            "requirements/pins.in",
            "requirements/pip.in",
            "requirements/manage.in",
        ),
        (),
        marks=pytest.mark.xfail(raises=MissingRequirementsFoldersFiles),
    ),
    (
        Path(__file__).parent.joinpath(
            "_good_files", "complete-manage-pip-prod.pyproject_toml"
        ),
        (
            "requirements/prod.in",
            "requirements/pins.in",
            "requirements/tox.in",
            "requirements/manage.in",
        ),
        (),
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
    ),
)
ids_unlock_compile = (
    "missing tox",
    "manage and tox",
    "constraint path needs to be resolved",
)


@pytest.mark.parametrize(
    "path_config, seq_create_these, additional_folders",
    testdata_unlock_compile,
    ids=ids_unlock_compile,
)
def test_unlock_compile(
    path_config,
    seq_create_these,
    additional_folders,
    tmp_path,
    prepare_folders_files,
    path_project_base,
    caplog,
    has_logging_occurred,
):
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

    # prepare (required and optionals .in files)
    inst = BackendType.load_factory(
        path_config,
        parent_dir=tmp_path,
        additional_folders=additional_folders,
    )

    assert inst.parent_dir == tmp_path

    expected = list(inst.in_files())
    expected_count = len(expected)

    # unlock_compile
    gen = unlock_compile(inst)
    unlock_files = list(gen)
    unlock_files_count = len(unlock_files)
    assert expected_count - 1 == unlock_files_count

    assert has_logging_occurred(caplog)
