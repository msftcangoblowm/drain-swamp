Anatomy of a snippet
====================

There is a block of text within a configuration file which would like to replace.

The only requirement is the file format should recognize pound symbol ``#`` as a comment.

snippet code
-------------

A snippet is a dynamic block in an otherwise static file.

The snippet code identifies each snippet. If there is only one snippet,
it's optional. To future proof it, best practice is to set a snippet
code. There is no down side besides ...

i'm going to make you watch really horrible movies!

The snippet code should be a cringe cultural reference. Will also see
this in the changelog.

In a changelog, an entry line seldomly uses ``- style:``. Especially not
as the first line.

And it's sorta awkward seeing it in a changelog.

Heh! Changelogs aren't supposed to be for entertainment

.. card::
   :shadow: none

   A snippet **without** a snippet_co
   ^^^

   .. code:: text

      before snippet
      # @@@ editable
      code block
      # @@@ end
      after snippet

   +++

   | If only one, can provide a snippet code or not.
   | At your discretion.
   | In the future, could this static file ever use more snippets?

.. card::
   :shadow: none

   A snippet **with** a snippet_co
   ^^^

   .. code:: text

      before snippet
      # @@@ i_am_a_snippet_co
      code block
      # @@@ end
      after snippet

   +++

   If there are multiple snippets, identifies the unique snippet

.. card::
   :shadow: none

   Multiple snippets in one file
   ^^^

   .. code:: text

      before snippet
      # @@@ i_am_a_snippet_co
      code block
      # @@@ end
      some more content
      # @@@ i_am_another_snippet_co
      code block
      # @@@ end
      after snippet

| Don't nest snippets
| Don't mismatch begin/end tags
| markdown not supported

replace example
----------------

Replace the text within the snippet

.. doctest:: with_id_replace

   >>> import tempfile
   >>> import textwrap
   >>> from pathlib import Path
   >>>
   >>> from drain_swamp.snip import Snip, ReplaceResult
   >>>
   >>> # prepare
   >>> text = (
   ...     "before snippet\n"
   ...     "# @@@ editable i_am_a_snippet_co\n"
   ...     "code block\n"
   ...     "# @@@ end\n"
   ...     "after snippet\n"
   ... )
   >>> contents_existing = textwrap.dedent(text)
   >>>
   >>> contents_new = """new\ncontents\nhere"""
   >>>
   >>> text_expected = (
   ...     "before snippet\n"
   ...     "# @@@ editable i_am_a_snippet_co\n"
   ...     "new\n"
   ...     "contents\n"
   ...     "here\n"
   ...     "# @@@ end\n"
   ...     "after snippet\n"
   ... )
   >>> expected = textwrap.dedent(text_expected)
   >>>
   >>> with tempfile.TemporaryDirectory() as f_path:
   ...     path_f = Path(f_path)
   ...
   ...     # prepare
   ...     path_some_conf = path_f / "some.conf"
   ...     chars_written = path_some_conf.write_text(contents_existing)
   ...
   ...     # act
   ...     snip = Snip(path_some_conf, is_quiet=True)
   ...     is_success = snip.replace(contents_new, id_="i_am_a_snippet_co")
   ...
   ...     actual = path_some_conf.read_text()
   ...     assert is_success == ReplaceResult.REPLACED
   ...     assert actual == expected
   ...
   >>>

In a temporary folder, created a file, ``some.conf`` with contents,
*contents_existing*.

The snippet, with id *i_am_a_snippet_co*, replace the contents with *contents_new*.

:code:`textwrap.dedent("""\\` would normally be used to:

- remove indention
- ignores the preceding newline

Snip constructor parameter, is_quiet, turns off logging

Validation
-----------

validation occurs at the beginning of
:py:meth:`Snip.replace <drain_swamp.snip.Snip.replace>`. Failing
validation, replace will not proceed; file contents will be unaffected.

Validation checks:

- nesting

- mismatching or out of order start / end tags

Where to use
-------------

Python package authors rarely write and publish just one python package.

We write lots of packages!

In each package, there is boilerplate code, not covered by unittests,
that is almost an exact copy as found in other packages.

After a few published packages, this boilerplate code becomes a liability
and an eye sore.

Code within ``Makefile`` or ``igor.py`` needs to brought under control.
Like a cancer, waiting to be exploited, less is more.

Ideally cut out in its entirely; preferably, as much as reasonable.

File formats -- supported

Lines starting with pound sign **#** are considered comments:

- python
- bash
- pyproject.toml
- Linux config files

File formats -- tricky:

- yaml

  Indention would need to be supplied with the content. There is no
  :code:`indent=8` option

File formats -- ill-suited (for now):

- html

  Comment begin/end tokens are :code:`<!-- -->`

- RestructuredText

  Comment token (period)(period)(space)

- markdown

  Platform-independent comment

  .. code:: text

     (empty line)
     [comment]: # (This actually is the most platform independent comment)

  The blank line before the comment line and maybe one afterwards would be tricky

  .. seealso::

     `markdown comments <https://stackoverflow.com/a/32190021>`_

- Makefile

  Makefile contains two languages: Makefile and bash (or whatever shell is set).
  So there are two distinct languages in one file. Intertwined!

  Isn't autotools meant to build Makefiles? Isn't this also a sewer
  targetted by hackers?

  The entire point is to reduce Makefile and igor.py code to the minimum.
