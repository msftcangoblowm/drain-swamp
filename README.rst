drain-swamp
==============

Python packaging automation is ripe for exploit. Lets drain the swamp!

Code in Makefile or python scripts should be reduced or removed
entirely, in favor of packaged, unittested, and well documented code.

Authors and maintainers deal with lots of repos. Too often
boilerplate gets copy and pasted into each package, becoming:

- an eye sore
- completely untested code
- small variations leak in
- code quality and feature improvements are less likely to happen

Drain swamp focuses on:

- pyproject.toml dependencies and optional dependencies
- Sphinx ``docs/conf.py``
- CHANGES.rst
- NOTICE.txt

This is done skillfully, applying a generic technique, snippets. Static
config files become dynamic, encouraging automation.

That's a lot of boilerplate code ... gone! Not all, but most.

.. PYVERSIONS

* Python 3.9 through 3.12, and 3.13.0a3 and up.

**New in 0.5.x:**

igor.py retired; pipenv-unlock is_lock command; swamp-drain cheats command;
integration unit tests seperated;

**New in 0.4.0:**

removed sphinxcontrib-snip; infer snippet code; list snippets;

Whats a snippet?
-----------------

Within a configuration, often need to run some code to change a some text.

The only requirement is the file format should recognize pound symbol ``#`` as a comment.

A snippet **without** an snippet code (id)

.. code:: text

   before snippet
   # @@@ editable
   code block
   # @@@ end
   after snippet

A snippet **with** an snippet code (id)

.. code:: text

   before snippet
   # @@@ i_am_a_snippet_co
   code block
   # @@@ end
   after snippet

Replace the text within the snippet

.. code:: python

    import tempfile
    import textwrap
    from pathlib import Path

    from drain_swamp.snip import Snip

    # prepare
    contents_existing = textwrap.dedent(
        """\
    before snippet
    # @@@ editable i_am_a_snippet_co
    code block
    # @@@ end
    after snippet
    """
    )

    contents_new = """new\ncontents\nhere"""

    expected = textwrap.dedent(
        """\
    before snippet
    # @@@ editable i_am_a_snippet_co
    new
    contents
    here
    # @@@ end
    after snippet
    """
    )

    with tempfile.TemporaryDirectory() as f_path:
        path_f = Path(f_path)

        # prepare
        path_some_conf = path_f / "some.conf"
        path_some_conf.write_text(contents_existing)

        # act
        snip = Snip(path_some_conf, is_quiet=True)
        snip.replace(contents_new, id_="i_am_a_snippet_co")

        actual = path_some_conf.read_text()

    assert actual == expected

In a temporary folder, created a file, ``some.conf`` with contents,
*contents_existing*.

Replace the contents within the snippet, with id *i_am_a_snippet_co*,
with *contents_new*.

:code:`textwrap.dedent("""\` means, remove any indention and escape
ignore the preceding newline

Snip constructor parameter, is_quiet, turns off logging

Where to use snippets?
------------------------

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

     https://stackoverflow.com/a/32190021

- Makefile

  Makefile contains two languages: Makefile and bash (or whatever shell is set).
  So there are two distinct languages in one file. Intertwined!

  Isn't autotools meant to build Makefiles? Isn't this also a sewer
  targetted by hackers?

  The entire point is to reduce Makefile and igor.py code to the minimum.

Extensions
-----------

*Snip* is the generic tool. Applying this tool to specific situations
should be considered Extensions (or plugins).

In which case, comes with two extensions:

**pipenv-unlock**

pyproject.toml is not dynamic and it's not supposed to be dynamic. In
an ideal world, it would be static.

But some authors, disappear or die. The primary issue with abandoned
package is it's dependency locked.

pipenv-unlock is a light switch to turn on/off dependency locking.

Snap ... on!

Snap ... off!

Snap ... on!

Snap ... off!

(author dies or discovers girls or gets a job scrapping gum off sidewalks)

world+dog: Phew! Winning ... err ... I mean, *So sad. Poor him*

**sphinxcontrib-snip**

Sphinx is amazing. In ``conf.py``, there are some dynamic fields. Each
package release, has to change these fields:

- version
- release
- release_date
- copyright (start year and author name)

Code that handles this should be removed from ``igor.py``!
