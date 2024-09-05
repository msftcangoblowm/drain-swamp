"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

Unittest for module, drain_swamp.snip

Unit test -- Module

.. code-block:: shell

   python -m coverage run --source='drain_swamp.snip' -m pytest \
   --showlocals tests/test_snip.py && coverage report \
   --data-file=.coverage --include="**/snip.py"

Integration test

.. code-block:: shell

   make coverage
   pytest --showlocals --cov="drain_swamp" --cov-report=term-missing \
   --cov-config=pyproject.toml tests

"""

import contextlib
import io
import logging
import logging.config
from pathlib import Path

import pytest

from drain_swamp.constants import (
    LOGGING,
    g_app_name,
)
from drain_swamp.snip import (
    ReplaceResult,
    Snip,
    check_matching_tag_count,
    check_not_nested_or_out_of_order,
)

testdata_test_snip_harden = [
    (
        "with_id_key_no_snippet.txt",
        "asdf",
        "abc abc abc",
        "zzzzzzzzzzzzz\nzzzzzzzzzz\nzzzzzzzzzzzzz\n",
        "zzzzzzzzzzzzz\nzzzzzzzzzz\nzzzzzzzzzzzzz\n",
        ReplaceResult.NO_MATCH,
        False,
    ),
    (
        "with_id_key_no_key.txt",
        "asdf",
        "abc abc abc",
        "zzzzzzzzzzzzz\n# @@@ editable\nblah blah blah\n# @@@ end\nzzzzzzzzzzzzz\n",
        "zzzzzzzzzzzzz\n# @@@ editable\nblah blah blah\n# @@@ end\nzzzzzzzzzzzzz\n",
        ReplaceResult.NO_MATCH,
        False,
    ),
    (
        "with_id_no_key_key.txt",
        "",
        "abc abc abc",
        "zzzzzzzzzzzzz\n# @@@ editable george\nblah blah blah\n# @@@ end\nzzzzzzzzzzzzz\n",
        "zzzzzzzzzzzzz\n# @@@ editable george\nabc abc abc\n# @@@ end\nzzzzzzzzzzzzz\n",
        ReplaceResult.REPLACED,
        False,
    ),
    (
        "with_id_no_change.txt",
        "asdf",
        "blah blah blah",
        "zzzzzzzzzzzzz\n# @@@ editable asdf\nblah blah blah\n# @@@ end\nzzzzzzzzzzzzz\n",
        "zzzzzzzzzzzzz\n# @@@ editable asdf\nblah blah blah\n# @@@ end\nzzzzzzzzzzzzz\n",
        ReplaceResult.NO_CHANGE,
        False,
    ),
    (
        "with_id.txt",
        "asdf",
        "abc abc abc",
        "zzzzzzzzzzzzz\n# @@@ editable asdf\nblah blah blah\n# @@@ end\nzzzzzzzzzzzzz\n",
        "zzzzzzzzzzzzz\n# @@@ editable asdf\nabc abc abc\n# @@@ end\nzzzzzzzzzzzzz\n",
        ReplaceResult.REPLACED,
        False,
    ),
    (
        "without_id_have_id_no_match.txt",
        "george",
        "abc abc abc",
        "zzzzzzzzzzzzz\n# @@@ editable\nblah blah blah\n# @@@ end\nzzzzzzzzzzzzz\nzzzzzzzzzzzzz\n# @@@ editable george\nblah blah blah\n# @@@ end\nzzzzzzzzzzzzz\n",
        "zzzzzzzzzzzzz\n# @@@ editable\nblah blah blah\n# @@@ end\nzzzzzzzzzzzzz\nzzzzzzzzzzzzz\n# @@@ editable george\nabc abc abc\n# @@@ end\nzzzzzzzzzzzzz\n",
        ReplaceResult.REPLACED,
        True,
    ),
    (
        "with_id_snippet_empty.txt",
        "asdf",
        "abc abc abc",
        "zzzzzzzzzzzzz\n# @@@ editable asdf\n\n# @@@ end\nzzzzzzzzzzzzz\n",
        "zzzzzzzzzzzzz\n# @@@ editable asdf\nabc abc abc\n# @@@ end\nzzzzzzzzzzzzz\n",
        ReplaceResult.REPLACED,
        False,
    ),
    (
        "without_id_empty_str.txt",
        "",
        "abc abc abc",
        "zzzzzzzzzzzzz\n# @@@ editable\nblah blah blah\n# @@@ end\nzzzzzzzzzzzzz\n",
        "zzzzzzzzzzzzz\n# @@@ editable\nabc abc abc\n# @@@ end\nzzzzzzzzzzzzz\n",
        ReplaceResult.REPLACED,
        True,
    ),
    (
        "without_id_none.txt",
        None,
        "abc abc abc",
        "zzzzzzzzzzzzz\n# @@@ editable\nblah blah blah\n# @@@ end\nzzzzzzzzzzzzz\n",
        "zzzzzzzzzzzzz\n# @@@ editable\nabc abc abc\n# @@@ end\nzzzzzzzzzzzzz\n",
        ReplaceResult.REPLACED,
        True,
    ),
    (
        "without_id_not_str.txt",
        1.12345,
        "abc abc abc",
        "zzzzzzzzzzzzz\n# @@@ editable\nblah blah blah\n# @@@ end\nzzzzzzzzzzzzz\n",
        "zzzzzzzzzzzzz\n# @@@ editable\nabc abc abc\n# @@@ end\nzzzzzzzzzzzzz\n",
        ReplaceResult.REPLACED,
        True,
    ),
    (
        "without_id_excess_whitespace.txt",
        "    ",
        "abc abc abc",
        "zzzzzzzzzzzzz\n# @@@ editable\nblah blah blah\n# @@@ end\nzzzzzzzzzzzzz\n",
        "zzzzzzzzzzzzz\n# @@@ editable\nabc abc abc\n# @@@ end\nzzzzzzzzzzzzz\n",
        ReplaceResult.REPLACED,
        True,
    ),
    (
        "with_id_match_2nd.txt",
        "george",
        "abc abc abc",
        "zzzzzzzzzzzzz\n# @@@ editable asdf\nblah blah blah\n# @@@ end\nzzzzzz\n# @@@ editable george\nhey there ted\n# @@@ end\nzzzzzzz\n",
        "zzzzzzzzzzzzz\n# @@@ editable asdf\nblah blah blah\n# @@@ end\nzzzzzz\n# @@@ editable george\nabc abc abc\n# @@@ end\nzzzzzzz\n",
        ReplaceResult.REPLACED,
        False,
    ),
    (
        "with_id_match_1st.txt",
        "asdf",
        "abc abc abc",
        "zzzzzzzzzzzzz\n# @@@ editable asdf\nblah blah blah\n# @@@ end\nzzzzzz\n# @@@ editable george\nhey there ted\n# @@@ end\nzzzzzzz\n",
        "zzzzzzzzzzzzz\n# @@@ editable asdf\nabc abc abc\n# @@@ end\nzzzzzz\n# @@@ editable george\nhey there ted\n# @@@ end\nzzzzzzz\n",
        ReplaceResult.REPLACED,
        False,
    ),
    (
        "with_id_match_1st_and_3rd.txt",
        "asdf",
        "abc abc abc",
        "zzzzzzzzzzzzz\n# @@@ editable asdf\nblah blah blah\n# @@@ end\nzzzzzz\n# @@@ editable george\nhey there ted\n# @@@ end\nzzzzzzz\n# @@@ editable asdf\nlol lol lol\n# @@@ end\noh ok then",
        "zzzzzzzzzzzzz\n# @@@ editable asdf\nabc abc abc\n# @@@ end\nzzzzzz\n# @@@ editable george\nhey there ted\n# @@@ end\nzzzzzzz\n# @@@ editable asdf\nabc abc abc\n# @@@ end\noh ok then",
        ReplaceResult.REPLACED,
        False,
    ),
]
ids_test_snip_harden = [
    "No snippet. Nothing to do",
    "one snip. with id. key / no key",
    "one snip. with id. no key / key",
    "one snip. with id. no change",
    "one snip. with id",
    "two snippets. one with one without id. key. invalid to mix",
    "one snip. with id. snippet empty",
    "one snip. without id empty str",
    "one snip. without id empty none",
    "one snip. without id empty not a str",
    "one snip. without id empty excess whitespace",
    "two snips. both have id. match 2nd",
    "two snips. both have id. match 1st",
    "three snips. All have id. match 1st and 3rd",
]


@pytest.mark.parametrize(
    "file_name, id_, replace_text, file_contents, expected, expected_result_status, is_quiet",
    testdata_test_snip_harden,
    ids=ids_test_snip_harden,
)
def test_snip_harden(
    file_name,
    id_,
    replace_text,
    file_contents,
    expected,
    expected_result_status,
    is_quiet,
    tmp_path,
    caplog,
    file_regression,
    has_logging_occurred,
):
    """Test Snip.replace failure and normal usage.

    .. seealso::

       `FileRegressionFixture.check <https://pytest-regressions.readthedocs.io/en/latest/api.html#pytest_regressions.file_regression.FileRegressionFixture.check>`_

    """
    # pytest --showlocals --log-level INFO -k "test_snip_harden" tests
    # py39+ Cannot have LOGGING.loggers.root
    LOGGING["loggers"][g_app_name]["propagate"] = True
    logging.config.dictConfig(LOGGING)
    logger = logging.getLogger(name=g_app_name)
    logger.addHandler(hdlr=caplog.handler)
    caplog.handler.level = logger.level

    # files/folders --> FileNotFoundError --> False
    invalids = (
        str(tmp_path),  # a folder
        Path("/proc/tmp/george/bob/ted/todd/dan.txt"),  # nonexistent file
        Path("__init__.py"),  # relative file (not scary normally empty)
    )
    for invalid in invalids:
        er_bad = Snip(invalid, is_quiet=is_quiet)
        # Fails at this point, not on class construction
        is_success = er_bad.replace(replace_text, id_=id_)
        assert is_success is None or ReplaceResult.VALIDATE_FAIL == is_success

    # prepare
    path_fname = tmp_path.joinpath(file_name)

    path_fnames = (
        path_fname,
        str(path_fname),
    )
    for mixed_f in path_fnames:
        Path(mixed_f).touch()
        Path(mixed_f).write_text("")  # reset file contents

        # empty file --> ValueError
        er_bad_val = Snip(mixed_f, is_quiet=is_quiet)
        with pytest.raises(ValueError):
            er_bad_val.get_file()

    for mixed_f in path_fnames:
        path_f = Path(mixed_f)
        path_f.write_text(file_contents)
        er = Snip(mixed_f, is_quiet=is_quiet)

        # pass in non-str
        invalids = (
            None,
            1.1234,
            1,
        )
        for invalid in invalids:
            with pytest.raises(TypeError):
                er.replace(invalid, id_=id_)

        # normal call
        is_success = er.replace(replace_text, id_=id_)
        if is_success is None or is_success == ReplaceResult.VALIDATE_FAIL:
            # issue with file or one or more validation checks failed
            pass
        else:
            assert is_success == expected_result_status
            actual = er.get_file()
            assert actual == expected

            assert has_logging_occurred(caplog)

            file_regression.check(expected, extension=".txt", binary=False)


def test_snip_properties():
    """Test Snip properties."""
    # pytest --showlocals --log-level INFO -k "test_properties" tests
    is_quiet_invalids = (
        None,
        "Hello World!",
    )
    path_invalids = (
        None,
        1.12345,
        1,
    )
    for p_invalid in path_invalids:
        for q_invalid in is_quiet_invalids:
            with pytest.raises(TypeError):
                Snip(p_invalid, is_quiet=q_invalid)


@pytest.mark.parametrize(
    "file_name, id_, replace_text, file_contents, expected, expected_result_status, is_quiet",
    testdata_test_snip_harden,
    ids=ids_test_snip_harden,
)
def test_checks_normal_usage(
    file_name,
    id_,
    replace_text,
    file_contents,
    expected,
    expected_result_status,
    is_quiet,
    caplog,
):
    """Snippet validity checks."""
    # pytest --showlocals --log-level INFO -k "test_checks_normal_usage" tests
    LOGGING["loggers"][g_app_name]["propagate"] = True
    logging.config.dictConfig(LOGGING)
    logger = logging.getLogger(name=g_app_name)
    logger.addHandler(hdlr=caplog.handler)
    caplog.handler.level = logger.level

    assert check_matching_tag_count(
        file_contents,
        Snip.TOKEN_START,
        Snip.TOKEN_END,
    )

    # check_matching_tag_count must occur before this check
    #    arg validation -- invalids
    invalids = (
        None,
        "",
        "    ",
        1.12345,
    )
    test_data = []
    a_ = file_contents
    b_ = Snip.TOKEN_START
    c_ = Snip.TOKEN_END
    for invalid_a in invalids:
        test_data.append((invalid_a, b_, c_))
    for invalid_b in invalids:
        test_data.append((a_, invalid_b, c_))
    for invalid_c in invalids:
        test_data.append((a_, b_, invalid_c))
    for t_args in test_data:
        assert check_not_nested_or_out_of_order(*t_args) is False

    #    normal usage
    assert check_not_nested_or_out_of_order(
        file_contents,
        Snip.TOKEN_START,
        Snip.TOKEN_END,
    )


@pytest.mark.parametrize(
    "file_name, id_, replace_text, file_contents, expected, expected_result_status, is_quiet",
    testdata_test_snip_harden,
    ids=ids_test_snip_harden,
)
def test_checks_bad_input(
    file_name,
    id_,
    replace_text,
    file_contents,
    expected,
    expected_result_status,
    is_quiet,
    caplog,
):
    """Snippet validity checks bad input."""
    # pytest --showlocals --log-level INFO -k "test_checks_bad_input" tests
    LOGGING["loggers"][g_app_name]["propagate"] = True
    logging.config.dictConfig(LOGGING)
    logger = logging.getLogger(name=g_app_name)
    logger.addHandler(hdlr=caplog.handler)
    caplog.handler.level = logger.level

    # prepare test data
    invalids = (
        None,
        "",
        "    ",
        1.12345,
    )
    test_data_checks_bad_input = []
    a_ = file_contents
    b_ = Snip.TOKEN_START
    c_ = Snip.TOKEN_END
    for invalid_a in invalids:
        test_data_checks_bad_input.append((invalid_a, b_, c_))
    for invalid_b in invalids:
        test_data_checks_bad_input.append((a_, invalid_b, c_))
    for invalid_c in invalids:
        test_data_checks_bad_input.append((a_, b_, invalid_c))

    # check_matching_tag_count
    for t_args in test_data_checks_bad_input:
        assert check_matching_tag_count(*t_args) is False

    # check_not_nested_or_out_of_order
    for t_args in test_data_checks_bad_input:
        assert check_not_nested_or_out_of_order(*t_args) is False


SNIPS_BAD = list(Path(__file__).parent.joinpath("_bad_snips").glob("*.txt"))


@pytest.mark.parametrize(
    "path",
    SNIPS_BAD,
    ids=[path.name.rsplit(".", 1)[0] for path in SNIPS_BAD],
)
def test_check_snips_bad(path):
    """Snips gone wrong."""
    # pytest --showlocals --log-level INFO -k "test_check_snips_bad" tests

    file_contents = path.read_text()
    invalids = [
        (file_contents, Snip.TOKEN_START, Snip.TOKEN_END),
    ]

    for t_args in invalids:
        # check_matching_tag_count ... pass
        assert check_matching_tag_count(*t_args)

        # check_not_nested_or_out_of_order ... fail
        assert not check_not_nested_or_out_of_order(*t_args)

    # bad files should fail validation
    snip = Snip(path)
    assert snip.validate() is False


@pytest.mark.parametrize(
    "file_name, id_, replace_text, file_contents, expected, expected_result_status, is_quiet",
    testdata_test_snip_harden,
    ids=ids_test_snip_harden,
)
def test_snip_validate(
    file_name,
    id_,
    replace_text,
    file_contents,
    expected,
    expected_result_status,
    is_quiet,
    caplog,
    tmp_path,
):
    """Test Snip.validate."""
    # pytest --showlocals --log-level INFO -k "test_snip_validate" tests
    LOGGING["loggers"][g_app_name]["propagate"] = True
    logging.config.dictConfig(LOGGING)
    logger = logging.getLogger(name=g_app_name)
    logger.addHandler(hdlr=caplog.handler)
    caplog.handler.level = logger.level

    # prepare
    path_fname = tmp_path.joinpath(file_name)

    path_fnames = (
        path_fname,
        str(path_fname),
    )
    for mixed_f in path_fnames:
        Path(mixed_f).touch()
        Path(mixed_f).write_text("")  # reset file contents

        # empty file --> ValueError --> False
        snip_empty = Snip(mixed_f, is_quiet=is_quiet)
        assert snip_empty.validate() is False

        Path(mixed_f).write_text(file_contents)

        # good
        snip = Snip(mixed_f, is_quiet=True)
        is_valid = snip.validate()
        assert is_valid is True

        # invalid files/folders --> FileNotFoundError --> False
        invalids = (
            str(tmp_path),  # a folder
            Path("/proc/tmp/george/bob/ted/todd/dan.txt"),  # nonexistent file
            Path("__init__.py"),  # relative file (not scary normally empty)
        )
        for invalid in invalids:
            snip_bad = Snip(invalid, is_quiet=is_quiet)
            # Fails at this point, not on class construction
            is_valid = snip_bad.validate()
            assert is_valid is False


testdata_snip_contents = [
    (
        "with_id_key_no_snippet.txt",
        "asdf",
        "zzzzzzzzzzzzz\nzzzzzzzzzz\nzzzzzzzzzzzzz\n",
        ReplaceResult.NO_MATCH,
        False,
    ),
    (
        "with_id_key_no_key.txt",
        "asdf",
        "zzzzzzzzzzzzz\n# @@@ editable\nblah blah blah\n# @@@ end\nzzzzzzzzzzzzz\n",
        ReplaceResult.NO_MATCH,
        False,
    ),
    (
        "with_id_no_key_key.txt",
        "",
        "zzzzzzzzzzzzz\n# @@@ editable george\nblah blah blah\n# @@@ end\nzzzzzzzzzzzzz\n",
        "blah blah blah",
        False,
    ),
    (
        "with_id.txt",
        "asdf",
        "zzzzzzzzzzzzz\n# @@@ editable asdf\nblah blah blah\n# @@@ end\nzzzzzzzzzzzzz\n",
        "blah blah blah",
        False,
    ),
    (
        "with_id_snippet_empty.txt",
        "asdf",
        "zzzzzzzzzzzzz\n# @@@ editable asdf\n\n# @@@ end\nzzzzzzzzzzzzz\n",
        "",
        False,
    ),
    (
        "without_id_empty_str.txt",
        "",
        "zzzzzzzzzzzzz\n# @@@ editable\nblah blah blah\n# @@@ end\nzzzzzzzzzzzzz\n",
        "blah blah blah",
        True,
    ),
    (
        "without_id_none.txt",
        None,
        "zzzzzzzzzzzzz\n# @@@ editable\nblah blah blah\n# @@@ end\nzzzzzzzzzzzzz\n",
        "blah blah blah",
        True,
    ),
    (
        "without_id_not_str.txt",
        1.12345,
        "zzzzzzzzzzzzz\n# @@@ editable\nblah blah blah\n# @@@ end\nzzzzzzzzzzzzz\n",
        "blah blah blah",
        True,
    ),
    (
        "without_id_excess_whitespace.txt",
        "    ",
        "zzzzzzzzzzzzz\n# @@@ editable\nblah blah blah\n# @@@ end\nzzzzzzzzzzzzz\n",
        "blah blah blah",
        True,
    ),
    (
        "with_id_match_2nd.txt",
        "george",
        "zzzzzzzzzzzzz\n# @@@ editable asdf\nblah blah blah\n# @@@ end\nzzzzzz\n# @@@ editable george\nhey there ted\n# @@@ end\nzzzzzzz\n",
        "hey there ted",
        False,
    ),
    (
        "with_id_match_1st.txt",
        "asdf",
        "zzzzzzzzzzzzz\n# @@@ editable asdf\nblah blah blah\n# @@@ end\nzzzzzz\n# @@@ editable george\nhey there ted\n# @@@ end\nzzzzzzz\n",
        "blah blah blah",
        False,
    ),
    (
        "with_id_match_1st_and_3rd.txt",
        "asdf",
        "zzzzzzzzzzzzz\n# @@@ editable asdf\nblah blah blah\n# @@@ end\nzzzzzz\n# @@@ editable george\nhey there ted\n# @@@ end\nzzzzzzz\n# @@@ editable asdf\nlol lol lol\n# @@@ end\noh ok then",
        "blah blah blah",
        False,
    ),
]
ids_snip_contents = [
    "No snippets. Nothing to do",
    "one snip. with id. No key",
    "one snip. with id. No key. Infers key",
    "one snip. with id",
    "one snip. with id. snippet empty",
    "one snip. without id empty str. Infers key",
    "one snip. without id empty none/ Infers key",
    "one snip. without id empty not a str. Infers key",
    "one snip. without id empty excess whitespace. Infers key",
    "two snips. both have id. match 2nd",
    "two snips. both have id. match 1st",
    "three snips. All have id. match 1st and 3rd",
]


@pytest.mark.parametrize(
    "file_name, id_, file_contents, expected, is_quiet",
    testdata_snip_contents,
    ids=ids_snip_contents,
)
def test_snip_contents(
    file_name,
    id_,
    file_contents,
    expected,
    is_quiet,
    tmp_path,
    prepare_folders_files,
    caplog,
    has_logging_occurred,
):
    """Test snippet algo."""
    # pytest --showlocals --log-level INFO -k "test_snip_contents" tests
    # pytest --showlocals --log-level INFO tests/test_snip.py::test_snip_contents["No snippets. Nothing to do"]
    LOGGING["loggers"][g_app_name]["propagate"] = True
    logging.config.dictConfig(LOGGING)
    logger = logging.getLogger(name=g_app_name)
    logger.addHandler(hdlr=caplog.handler)
    caplog.handler.level = logger.level

    path_abs = tmp_path / file_name
    snip = Snip(path_abs, is_quiet=is_quiet)

    # No preparation -- snip.contents
    t_actual = snip.contents(id_=id_)
    assert t_actual == ReplaceResult.VALIDATE_FAIL

    # No preparation -- snip.print
    with contextlib.redirect_stderr(io.StringIO()):
        snippets = snip.print()
    assert snippets == ReplaceResult.VALIDATE_FAIL

    # prepare
    seq_create_these = (file_name,)
    prepare_folders_files(seq_create_these, tmp_path)
    path_abs.write_text(file_contents)

    # act -- snip.print
    #    same return value as snip.snippet
    with contextlib.redirect_stderr(io.StringIO()) as f_1:
        snippets = snip.print()
    msg = f_1.getvalue()

    if isinstance(snippets, ReplaceResult):
        assert snippets == ReplaceResult.NO_MATCH
        # logger.info(f"No snippets: {snippets}\n{msg}")
        pass
    else:
        #    Block of human readable beautiful prose was printed
        assert len(msg) != 0

    # act -- snip.contents
    t_actual = snip.contents(id_=id_)

    assert has_logging_occurred(caplog)

    if isinstance(t_actual, ReplaceResult):
        assert t_actual == ReplaceResult.NO_MATCH
    else:
        # id_ might have been inferred
        assert t_actual[0] == expected
