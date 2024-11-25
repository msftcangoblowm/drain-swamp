"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

Unit test -- Module

.. code-block:: shell

   python -m coverage run --source='drain_swamp.lock_compile' -m pytest \
   --showlocals tests/test_lock_compile.py && coverage report \
   --data-file=.coverage --include="**/lock_compile.py"

"""

import logging
import logging.config
import shutil
from collections.abc import Generator
from contextlib import nullcontext as does_not_raise
from pathlib import (
    Path,
    PurePath,
)
from typing import cast

import pytest

from drain_swamp._package_installed import is_package_installed
from drain_swamp._safe_path import (
    resolve_joinpath,
    resolve_path,
)
from drain_swamp.constants import (
    LOGGING,
    g_app_name,
)
from drain_swamp.exceptions import MissingRequirementsFoldersFiles
from drain_swamp.lock_compile import (
    _compile_one,
    _postprocess_abspath_to_relpath,
    is_timeout,
    lock_compile,
    prepare_pairs,
)
from drain_swamp.lock_infile import InFiles
from drain_swamp.pep518_venvs import (
    VenvMapLoader,
    get_reqs,
)

from .testdata_lock_inspect import (
    ids_lock_compile_live,
    testdata_lock_compile_live,
)

testdata_compile_one = (
    pytest.param(
        (
            Path(__file__).parent.parent.joinpath("requirements/pins.shared.in"),
            Path(__file__).parent.parent.joinpath("requirements/pip.in"),
            Path(__file__).parent.parent.joinpath("requirements/pip-tools.in"),
        ),
        "requirements/pip-tools.in",
        "requirements/pip-tools.out",
    ),
)
ids_compile_one = ("pip-tools.in --> pip-tools.lock",)


@pytest.mark.xfail(
    not is_package_installed("pip-tools"),
    reason="dependency package pip-tools is required",
)
@pytest.mark.parametrize(
    "seq_copy_these, in_relpath, out_relpath",
    testdata_compile_one,
    ids=ids_compile_one,
)
def test_compile_one(
    seq_copy_these,
    in_relpath,
    out_relpath,
    tmp_path,
):
    """Lock a .in file."""
    # pytest -vv --showlocals --log-level INFO -k "test_compile_one" tests
    path_ep = resolve_path("pip-compile")
    ep_path = str(path_ep)
    path_cwd = tmp_path
    context = ".venv"

    # prepare
    #    dest folders
    path_dir = cast("Path", resolve_joinpath(tmp_path, "requirements"))
    path_dir.mkdir(parents=True, exist_ok=True)

    #    Copy real .in files
    for abspath_src in seq_copy_these:
        src_abspath = str(abspath_src)
        abspath_dest = tmp_path / "requirements" / abspath_src.name
        shutil.copy2(src_abspath, abspath_dest)
    abspath_in = cast("Path", resolve_joinpath(tmp_path, in_relpath))
    abspath_out = cast("Path", resolve_joinpath(tmp_path, out_relpath))
    in_abspath = abspath_in.as_posix()
    out_abspath = abspath_out.as_posix()

    # Conforms to interface?
    assert isinstance(in_abspath, str)
    assert isinstance(out_abspath, str)
    assert isinstance(ep_path, str)
    assert issubclass(type(path_cwd), PurePath)
    assert context is None or isinstance(context, str)

    # act
    optabspath_out, err_details = _compile_one(
        in_abspath,
        out_abspath,
        ep_path,
        path_cwd,
        context,
        timeout=PurePath,
    )
    # verify
    t_failures = (err_details,)
    if err_details is not None and is_timeout(t_failures):
        pytest.skip("lock_compile requires a web connection")
    else:
        assert optabspath_out is not None
        assert issubclass(type(optabspath_out), PurePath)
        assert optabspath_out.exists() and optabspath_out.is_file()


testdata_lock_file_paths_to_relpath = (
    (
        (
            "requirements/prod.shared.in",
            "docs/requirements.in",
        ),
        (
            "#\n"
            "click==8.1.7\n"
            "    # via\n"
            "    #   -c {tmp_path!s}/docs/../requirements/prod.shared.in\n"
            "    #   click-log\n"
            "    #   scriv\n"
            "    #   sphinx-external-toc-strict\n"
            "    #   uvicorn\n"
            "sphobjinv==2.3.1.1\n"
            "    # via -r {tmp_path!s}/docs/requirements.in\n\n"
        ),
        (
            "#\n"
            "click==8.1.7\n"
            "    # via\n"
            "    #   -c docs/../requirements/prod.shared.in\n"
            "    #   click-log\n"
            "    #   scriv\n"
            "    #   sphinx-external-toc-strict\n"
            "    #   uvicorn\n"
            "sphobjinv==2.3.1.1\n"
            "    # via -r docs/requirements.in\n\n"
        ),
        "docs/requirements.lock",
    ),
)
ids_lock_file_paths_to_relpath = ("remove absolute paths from .lock file",)


@pytest.mark.parametrize(
    "seq_reqs_relpath, lock_file_contents, expected_contents, dest_relpath",
    testdata_lock_file_paths_to_relpath,
    ids=ids_lock_file_paths_to_relpath,
)
def test_lock_file_paths_to_relpath(
    seq_reqs_relpath,
    lock_file_contents,
    expected_contents,
    dest_relpath,
    tmp_path,
    prepare_folders_files,
):
    """When creating .lock files post processer abs path --> relative path."""
    # pytest --showlocals --log-level INFO -k "test_lock_file_paths_to_relpath" tests
    # prepare
    #    .in
    prepare_folders_files(seq_reqs_relpath, tmp_path)

    #    .lock create with contents
    path_doc_lock = cast("Path", resolve_joinpath(tmp_path, dest_relpath))
    path_doc_lock.write_text(lock_file_contents.format(**{"tmp_path": tmp_path}))

    # act
    _postprocess_abspath_to_relpath(path_doc_lock, tmp_path)

    # verify
    #    Within file contents, absolute path of parent folder is absent
    actual_contents = path_doc_lock.read_text()
    is_not_occur_once = str(tmp_path) not in actual_contents
    assert is_not_occur_once is True
    assert actual_contents == expected_contents


@pytest.mark.xfail(
    not is_package_installed("pip-tools"),
    reason="dependency package pip-tools is required",
)
@pytest.mark.parametrize(
    "path_config, venv_relpath, seq_reqs_relpath, in_relpath, out_relpath, expectation",
    testdata_lock_compile_live,
    ids=ids_lock_compile_live,
)
def test_lock_compile_live(
    path_config,
    venv_relpath,
    seq_reqs_relpath,
    in_relpath,
    out_relpath,
    expectation,
    tmp_path,
    path_project_base,
    prep_pyproject_toml,
    prepare_folders_files,
    caplog,
    has_logging_occurred,
):
    """Test lock compile"""
    # pytest -vv --showlocals --log-level INFO -k "test_lock_compile_live" tests
    LOGGING["loggers"][g_app_name]["propagate"] = True
    logging.config.dictConfig(LOGGING)
    logger = logging.getLogger(name=g_app_name)
    logger.addHandler(hdlr=caplog.handler)
    caplog.handler.level = logger.level

    path_cwd = path_project_base()
    # prepare
    #    pyproject.toml
    path_f = prep_pyproject_toml(path_config, tmp_path)

    # Act
    #    Test without copying over support files
    loader = VenvMapLoader(path_f.as_posix())
    with pytest.raises(NotADirectoryError):
        lock_compile(loader, venv_relpath)
    #    Test not filtering by venv relpath
    with pytest.raises(NotADirectoryError):
        lock_compile(loader, None)

    #    create folders (venv and requirements folders)
    venv_relpaths = (
        ".venv",
        ".tools",
        "requirements",
        "docs",
    )
    for create_relpath in venv_relpaths:
        abspath_venv = cast("Path", resolve_joinpath(tmp_path, create_relpath))
        abspath_venv.mkdir(parents=True, exist_ok=True)

    #    Test without copying over support files
    loader = VenvMapLoader(path_f.as_posix())
    with pytest.raises(MissingRequirementsFoldersFiles):
        lock_compile(loader, venv_relpath)

    # prepare
    #    copy just the reqs .in
    abspath_src = cast("Path", resolve_joinpath(path_cwd, in_relpath))
    abspath_dest = cast("Path", resolve_joinpath(tmp_path, in_relpath))
    shutil.copy2(abspath_src, abspath_dest)

    # prepare
    #    copy (one venv, not all venv) requirements to respective folders
    for relpath_f in seq_reqs_relpath:
        abspath_src = cast("Path", resolve_joinpath(path_cwd, relpath_f))
        abspath_dest = cast("Path", resolve_joinpath(tmp_path, relpath_f))
        shutil.copy2(abspath_src, abspath_dest)

    # Act
    loader = VenvMapLoader(path_f.as_posix())

    # overloaded function prepare_pairs
    with expectation:
        # _, files = filter_by_venv_relpath(loader, venv_relpath)
        try:
            t_abspath_in = get_reqs(loader, venv_path=venv_relpath)
            # Generic -- To test prepare_pairs, must be InFiles
            files = InFiles(path_cwd, t_abspath_in)
            files.resolution_loop()
        except MissingRequirementsFoldersFiles:
            raise
        except (NotADirectoryError, ValueError, KeyError):
            raise

    if isinstance(expectation, does_not_raise):
        gen = prepare_pairs(t_abspath_in)
        assert isinstance(gen, Generator)
        list(gen)  # execute Generator
        gen = prepare_pairs(files, path_cwd=tmp_path)
        assert isinstance(gen, Generator)
        list(gen)  # execute Generator
        # path_cwd must be provided and be a Path
        with pytest.raises(AssertionError):
            gen = prepare_pairs(files, path_cwd=None)
            list(gen)  # execute Generator

        # Fallback
        with pytest.raises(NotImplementedError):
            gen = prepare_pairs(None)
            list(gen)

    with expectation:
        """
        func_path = f"{g_app_name}.lock_inspect.lock_compile"
        args = (loader, venv_relpath)
        kwargs = {}
        t_ret = get_locals(func_path, lock_compile, *args, **kwargs)  # noqa: F841
        t_status, t_locals = t_ret
        """
        t_status = lock_compile(
            loader,
            venv_relpath,
            timeout=PurePath,
        )
    # Verify
    if isinstance(expectation, does_not_raise):
        # assert has_logging_occurred(caplog)
        assert t_status is not None
        assert isinstance(t_status, tuple)
        t_compiled, t_failures = t_status
        assert isinstance(t_failures, tuple)
        assert isinstance(t_compiled, tuple)
        if is_timeout(t_failures):
            pytest.skip("lock_compile requires a web connection")
        else:
            is_no_failures = len(t_failures) == 0
            assert is_no_failures
            compiled_count = len(t_compiled)
            assert compiled_count == 1
