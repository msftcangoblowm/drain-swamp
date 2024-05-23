"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

Be able to search and replace editable regions within text files

.. py:data:: __all__
   :type: tuple[str]
   :value: ("Snip",)

   Modules exports

.. py:data:: _logger
   :type: logging.Logger

   Module level logger

"""

from __future__ import annotations

import logging
import re
import string
from functools import partial
from pathlib import (
    Path,
    PurePath,
)

from .check_type import is_ok
from .constants import g_app_name

__package__ = "drain_swamp"
__all__ = ("Snip",)

_logger = logging.getLogger(f"{g_app_name}.snip")


def check_matching_tag_count(
    contents,
    token_start=None,
    token_end=None,
):
    """Checks tag count. Completely oblivious to overlapping tags

    Non-overlapping start/end tokens

    .. code-block:: python

        from drain_swamp.snip import check_matching_tag_count, Snip

        token_start = Snip.TOKEN_START
        token_end = Snip.TOKEN_END
        contents = f"{token_start}{token_end}{token_start}{token_end}"

        is_ok = check_matching_tag_count(
            contents,
            token_start,
            token_end,
        )
        assert is_ok

    :param contents: file contents to be validated
    :type contents: str
    :param token_start: Default None. Regex indicating start of a snippet
    :type token_start: str | None
    :param token_end: Default None. Regex indicating end of a snippet
    :type token_end: str | None
    :returns: True is check successful otherwise False
    :rtype: bool
    """
    if is_ok(contents) and is_ok(token_start) and is_ok(token_end):
        start_count = contents.count(token_start)
        end_count = contents.count(token_end)

        _logger.debug(f"start token count: {start_count}")
        _logger.debug(f"end token count: {end_count}")
        is_tag_count_match = start_count == end_count
        _logger.debug(f"token counts match: {is_tag_count_match}")
        ret = is_tag_count_match
    else:
        ret = False

    return ret


def check_not_nested_or_out_of_order(
    contents,
    token_start,
    token_end,
):
    """Check tag pairs are not nested / out of order

    Assumes :py:func:`drain_swamp.snip.check_matching_tag_count`
    already checked.

    :param contents: file contents to check
    :type contents: str
    :param token_start: Default None. Start token
    :type token_start: str | None
    :param token_end: Default None. End token
    :type token_end: str | None
    :returns:

       True on success False indicates give feedback and
       **definitely do not** attempt replacing a snippet

    :rtype: bool
    :raises:

        - :py:exc:`ValueError` -- Either no contents, no start token,
          or no end token provided

    """
    ret = True

    if is_ok(contents) and is_ok(token_start) and is_ok(token_end):
        idx_current = 0
        found_next = True
        while found_next is True:
            idx_start = contents.find(token_start, idx_current)
            idx_end = contents.find(token_end, idx_current)

            # Not errors:
            # - no tag pairs at all
            # - no next tags
            is_no_more_tags = idx_start == -1 and idx_end == -1
            if is_no_more_tags:
                found_next = False
                continue
            else:  # pragma: no cover
                pass

            # is_end_at_beginning = idx_end != -1 and idx_end == idx_current
            is_no_start_tag = idx_start == -1 and idx_end != -1
            is_no_end_tag = idx_start != -1 and idx_end == -1
            is_both_exist = idx_start != -1 and idx_end != -1
            is_end_before_start = is_both_exist and idx_end < idx_start
            is_bad = is_no_start_tag or is_no_end_tag or is_end_before_start

            # is_good
            """
            is_start_before_end = (
                is_both_exist
                and idx_start < idx_end
            )
            """
            pass

            if is_bad:
                ret = False
                found_next = False
            else:
                # next start idx
                idx_next_start = idx_end + len(token_end) + 1
                # advance past end tag
                idx_current = idx_next_start
    else:
        # either no contents, no start token, or no end token
        ret = False
        msg_info = "Either no contents, no start token, or no end token provided"
        _logger.info(msg_info)

    return ret


def sanitize_id(id_=""):
    """tokenize snippet code. alphanumeric + underscore

    :param id_:

       Snippet code. Default empty str. If empty str or None or just
       whitespace, considered as an empty string

    :type id_: typing.Any | None
    :returns: The snippet code sanitized
    :rtype: str
    """
    if id_ is None:
        # None
        ret = ""
    else:
        if not isinstance(id_, str):
            # unsupported type
            ret = ""
        else:
            # hyphen --> underscore
            ret = id_.replace("-", "_")

            # \w
            allowed_chars = string.ascii_letters + "_"
            # filter out any other character
            ret = "".join(c for c in ret if c in allowed_chars)

    return ret


class Snip:
    """jinja2 templates is time consuming to get the spacing right. A
    snippet is an easier alternative

    .. py:attribute:: TOKEN_START
       :type: str
       :value: "# @@@ editable"

       Beginning token of an editable section. Optionally can be followed
       by one whitespace and a str id. ID can contain alphanumberic
       characters and underscore. If there is no id, a file can contain at
       most one editable section

    .. py:attribute:: TOKEN_END
       :type: str
       :value: "# @@@ end\\n"

       End token denotes end of editable section. A trailing newline is expected

    .. py:attribute:: PATTERN_W_ID
       :type: re.Pattern

       Compiled regex which allows for an optional id. Captures two groups:
       id and contents.

       Removed regex which doesn't not support optional id for editable sections

       ``.*`` means capture greedily. ``.*?`` means shortest path match

       .. seealso::

          ``(?s)`` means single line mode. equivalent to compile flag ``re.DOTALL``

          `regex -- modifiers <https://www.regular-expressions.info/modifiers.html>`_

    :ivar fname: the file in/near the project to update
    :vartype fname: str | pathlib.Path
    :ivar is_quiet: Default False, set to True to repress logging
    :vartype is_quiet: bool | None

    :raises:

       - :py:exc:`TypeError` -- Unsupported type, fname can be either a str or Path

    .. todo::

       Take editable file paths from ``pyproject.toml``

    """

    TOKEN_START = "# @@@ editable"
    TOKEN_END = "# @@@ end\n"
    # PATTERN_WO_ID = re.compile(r"(?s)# @@@ editable\n.*# @@@ end\n")
    PATTERN_W_ID = re.compile(
        r"# @@@ editable\s?(\w*)?\n(.*?)\n# @@@ end\n",
        flags=re.DOTALL,
    )
    __slots__ = ("_is_quiet", "_path_file", "_contents")

    def __init__(
        self,
        fname,
        is_quiet=False,
    ):
        super().__init__()
        self.is_quiet = is_quiet

        # Not throughly validated
        self.path_file = fname

        self._contents = None

    @property
    def path_file(self):
        """Path has not necessarily been checked. Run thru a validator func

        :returns: A raw path either relative or absolute
        :rtype: pathlib.Path
        """
        return self._path_file

    @path_file.setter
    def path_file(self, val):
        """Setter does not check:

        - whether relative or absolute path

        - whether is known to have editable region and therefore allowed

        :param val: Should be a str or Path. Either relative or absolute
        :type val: typing.Any
        :raises:

           - :py:exc:`TypeError` -- Unsupported type, can be either str or Path

        """
        msg_exc = "Unsupported type, fname can be either a str or Path"
        if val is None:
            raise TypeError(msg_exc)
        else:
            if isinstance(val, str):
                self._path_file = Path(val)
            elif issubclass(type(val), PurePath):
                self._path_file = val
            else:
                raise TypeError(msg_exc)

    def is_file_ok(self):
        """Try to grab permitted editable files from ``pyproject.toml``

        :returns: True if file has absolute and is permitted
        :rtype: bool

        .. todo:: r/w ??

           What about confirm: readable and writable!

        """
        # Replace this with a check of ``pyproject.toml`` settings
        is_editable_file = True
        path_f = self.path_file
        ret = (
            path_f.exists()
            and path_f.is_file()
            and path_f.is_absolute()
            and is_editable_file
        )
        return ret

    @property
    def is_quiet(self):
        """Whether to permit printing status to stderr

        :returns: True to not print status updates
        :rtype: bool
        """
        return self._is_quiet

    @is_quiet.setter
    def is_quiet(self, val):
        """Whether or not to suppress info logging messages

        :param val: Should be a bool. Defaults to False
        :type val: typing.Any
        """
        # Eventhough optional, is_quiet is a bool
        if val is None or not isinstance(val, bool):
            self._is_quiet = False
        else:  # pragma: no cover
            self._is_quiet = val

    def get_file(self):
        """Read the file

        :returns: file contents
        :rtype: str
        :raises:

           - :py:exc:`ValueError` -- cannot read file or is empty
           - :py:exc:`FileNotFoundError` -- file is not ok for whatever reason

        """
        if not self.is_file_ok() and not self.is_quiet:  # pragma: no cover
            msg_info = f"Cannot update nonexistent file, {str(self.path_file)}"
            _logger.info(msg_info)
        else:  # pragma: no cover
            pass

        if self.is_file_ok():
            ret = self.path_file.read_text(encoding="utf-8")

            if ret is None or len(ret) == 0:
                # Expecting file to not be empty
                # Also expecting to contain editable regions
                msg_exc = "Expecting file to be non-empty"
                raise ValueError(msg_exc)
            else:  # pragma: no cover
                pass
        else:  # pragma: no cover
            # file not ok
            msg_exc = (
                f"file not ok. replace editable region ... skip {str(self.path_file)}"
            )
            raise FileNotFoundError(msg_exc)

        return ret

    def replace(self, replacement, id_=""):
        """Find snippet with *id_*. If no *id_*, provided the file
        may contain at most one snippet.

        *id_* should be a cringe worthy cultural reference to an object
        or minor character! One id should be changed for every minor
        version release or PR

        In the changelog, in the commit, the top most lines should
        use

        .. code-block:: text

           *- style: * tags

           Explain the snippet_co (id_) cringe worthy cultural reference


        :param replacement: Just the content. Will be substituted within the file
        :type replacement: str
        :param id_:

           Default empty string. So as to support multiple snippets within a file.
           If only intended ever to have one snippet, empty string is appropriate

        :type id_: str | None
        :returns: True if a *replacement* occurred otherwise False
        :rtype: bool

        :raises:

            - :py:exc:`TypeError` -- Unsupported type, *replacement* contents must be a str

        """
        cls = type(self)
        if replacement is None or not isinstance(replacement, str):
            msg_exc = "Unsupported type, replacement contents must be a str"
            raise TypeError(msg_exc)

        id_ = sanitize_id(id_)
        if not self.is_quiet:  # pragma: no cover
            _logger.info(f"id_ (user input; filtered): {id_}")
            _logger.info(f"replacement (user input filtered): {replacement}")
        else:  # pragma: no cover
            pass

        def replace_fcn(matchobj):
            """inline func for snippets. Which are editable regions within utf-8 text
            files. Under the hood, The search and replace is using
            :py:func:`re.sub` and a nasty regex

            - ``matchobj.group(0)``
              Entire snippet including start/end tokens. Non-greedy
              will match first end token

            - ``matchobj.group(1)``
              snippet id. Can be empty string if no multiple id support

            - ``matchobj.group(2)``
              snippet contents

            Requires these outer func/meth variables:

            - token_start
            - token_end
            - id_
            - replacement

            Assumes the text is within a text file, not a stream nor a str.

            Example before and after

            snippet with an id

            .. code-block:: text

               id_ = "asdf"
               replacement = "abc abc abc"
               old_text = "zzzzzzzzzzzzz\n# @@@ editable asdf\nblah blah blah\n# @@@ end\nzzzzzzzzzzzz\n"

               expected = (
                   "zzzzzzzzzzzzz\n# @@@ editable asdf\nabc abc abc\n# @@@ end\nzzzzzzzzzzzz\n"
               )

            snippet without an id

            .. code-block:: text

               id_ = ""
               replacement = "abc abc abc"
               old_text = "zzzzzzzzzzzzz\n# @@@ editable\nblah blah blah\n# @@@ end\nzzzzzzzzzzzz\n"

               expected = (
                   "zzzzzzzzzzzzz\n# @@@ editable\nabc abc abc\n# @@@ end\nzzzzzzzzzzzz\n"
               )

            Only one snippet without an id allowed with a file. snippets
            with id and **one** snippet without id are allowed

            :param matchobj: Regex match object. Provided when a match occurs
            :type matchobj: re.Match
            :returns:

               If not an actual match, return the original content
               otherwise modify the content. Whatever returned will
               replace the existing text

            :rtype: str | None

            .. seealso::

               `re.sub <https://docs.python.org/3/library/re.html#re.sub>`_

               `regex tester web app <https://regexr.com/>`_

            """
            _logger.debug(f"matched region:   {matchobj.group(0)}")
            _logger.debug(f"current id:       {matchobj.group(1)}")
            _logger.debug(f"current contents: {matchobj.group(2)}")
            _logger.debug(f"target id:        {id_}")
            _logger.debug(f"replacement: {replacement}")

            current_id = matchobj.group(1)
            is_target_have_id = len(id_) != 0
            is_current_have_id = len(current_id) != 0

            if is_target_have_id and is_current_have_id and current_id == id_:
                # both have id and match
                ret = f"{token_start} {id_}\n{replacement}\n{token_end}"
                _logger.info("both have id; match")
            elif is_target_have_id and is_current_have_id and current_id != id_:
                # both have id; no match
                _logger.debug("both have id; no match --> return unmodified")
                ret = matchobj.group(0)
            elif not is_target_have_id and not is_current_have_id:
                ret = f"{token_start}\n{replacement}\n{token_end}"
                _logger.debug("both no id; match")
            else:
                _logger.debug("not a match --> return unmodified")
                ret = matchobj.group(0)

            _logger.debug(f"ret: {ret}")

            return ret

        # first match snippet
        snippet_existing = self.contents(id_=id_)

        # file contents
        text_existing = self._contents

        # A replacement will occur
        ret = False
        if snippet_existing is not None:
            # Run re.sub on all editable regions
            token_start = cls.TOKEN_START
            token_end = cls.TOKEN_END
            new_text = re.sub(cls.PATTERN_W_ID, replace_fcn, text_existing)

            if not self.is_quiet:  # pragma: no cover
                _logger.info(f"text (after re.sub): {new_text}")
            else:  # pragma: no cover
                pass

            is_changed = new_text != text_existing

            if is_changed:
                if not self.is_quiet:  # pragma: no cover
                    msg_info = f"Updating {str(self.path_file)}"
                    _logger.info(msg_info)
                else:  # pragma: no cover
                    pass
                self.path_file.write_text(new_text)
                ret = True
            else:  # pragma: no cover
                pass

        return ret

    def validate(self):
        """validate target file contents are safe

        All checks must pass. Over time add additional checks

        :returns: All checks passed
        :rtype: bool
        """

        # This is an initial check, so should return, not raise
        try:
            contents = self.get_file()
        except (ValueError, FileNotFoundError):
            msg_exc = (
                f"file not ok. replace editable region ... skip {str(self.path_file)}"
            )
            _logger.warning(msg_exc)
            self._contents = None
            return False

        cls = type(self)

        token_start = cls.TOKEN_START
        token_end = cls.TOKEN_END
        validators = (
            partial(
                check_matching_tag_count,
                contents,
                token_start=token_start,
                token_end=token_end,
            ),
            partial(
                check_not_nested_or_out_of_order,
                contents,
                token_start=token_start,
                token_end=token_end,
            ),
        )
        ret = all([validator() for validator in validators])

        # file contents --> buffer, so don't have to get_file twice
        if ret is True:
            self._contents = contents
        else:
            self._contents = None

        return ret

    def contents(self, id_=None):
        """Get the contents. Use :py:func:`re.match` to parse and
        retrieve 2nd group

        :param id_: Default None. snippet_co
        :type id_: str | None
        :returns: snippet contents, if match for the snippet otherwise None
        :rtype: str | None
        """
        if not self.validate():
            if not self.is_quiet:  # pragma: no cover
                msg_info = f"file: validation failed. Check file {str(self.path_file)}"
                _logger.info(msg_info)
            else:  # pragma: no cover
                pass
            return None

        contents = self._contents

        cls = type(self)
        id_ = sanitize_id(id_)
        if not self.is_quiet:  # pragma: no cover
            _logger.debug(f"target id:        {id_}")
        else:  # pragma: no cover
            pass

        pattern = cls.PATTERN_W_ID
        prog = re.compile(pattern)

        seq_ret = []
        for m in prog.finditer(contents):
            if m is not None and m.group(1) == id_:
                if not self.is_quiet:
                    _logger.info(f"matched region:   {m.group(0)}")
                    _logger.info(f"current id:       {m.group(1)}")
                    _logger.info(f"current contents: {m.group(2)}")
                else:  # pragma: no cover
                    pass

                seq_ret.append(m.group(2))

        if len(seq_ret) >= 1:
            ret = seq_ret[0]
        else:
            ret = None
            if not self.is_quiet:  # pragma: no cover
                _logger.info("match: no")
            else:  # pragma: no cover
                pass

        return ret
