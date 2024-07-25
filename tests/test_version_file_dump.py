"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

.. code-block:: shell

   pytest --showlocals --log-level INFO tests/test_version_file_dump.py
   pytest --showlocals --cov="drain_swamp" --cov-report=term-missing tests/test_version_file_dump.py

"""

from pathlib import (
    Path,
    PurePath,
)

import pytest

from drain_swamp.version_file.dump_version import (
    _validate_template,
    dump_version,
)


def test_dump_version(tmp_path, prepare_folders_files):
    # prepare
    seq_rel_paths = ("_version.py",)
    prepare_folders_files(seq_rel_paths, tmp_path)

    version = "0.0.1a.dev1"
    # absolute path obsolete --> DeprecationWarning
    write_to = tmp_path / "_version.py"
    with pytest.deprecated_call():
        dump_version(tmp_path, version, write_to)
    pass


def test_validate_template(tmp_path, prepare_folders_files):
    # prepare
    target = Path("_version.py")
    assert issubclass(type(target), PurePath)
    seq_rel_paths = (target,)
    prepare_folders_files(seq_rel_paths, tmp_path)

    # supplying a nonsense template
    invalids = (
        "",
        "   ",
    )
    for template in invalids:
        with pytest.warns(Warning):
            actual = _validate_template(target, template)
            assert actual is not None
            assert isinstance(actual, str)
            assert len(actual) != 0

    template = None
    # unsupported target suffix type --> ValueError
    target = Path("_version.rst")
    with pytest.raises(ValueError):
        _validate_template(target, template)

    # supported target suffix
    target = Path("_version.py")
    actual = _validate_template(target, template)
    assert actual is not None
    assert isinstance(actual, str)
    assert len(actual) != 0

    # supply a template
    template_rst = {".rst": "{version}"}
    target = Path("_version.rst")
    actual = _validate_template(target, template_rst)
    assert actual is not None
    assert isinstance(actual, dict)
