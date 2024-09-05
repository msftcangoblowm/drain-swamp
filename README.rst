drain-swamp
==============

Python build backend with build plugins and dependency lock switch

|  |kit| |codecov| |license|
|  |last-commit| |test-status| |quality-status| |docs|
|  |versions| |implementations|
|  |platforms| |black|
|  |downloads| |stars|
|  |mastodon-msftcangoblowm|

|feature banner|

.. PYVERSIONS

\* Python 3.9 through 3.13, PyPy

**New in 1.6.x**

recognize .in files options -r and -c; tox test only folder tests; favicons;
workflow for branches to test MacOS and Windows; MacOS supported;

**New in 1.5.x**

resolve dependency hell; dependency conflict prevent tests fail;
docs design elements improve presentation; gh-pages workflow;
fix semantic version edge cases pre+post;

What swamp?
------------

Code in Makefile or python scripts should be reduced or removed
entirely, in favor of packaged, unittested, and well documented code.

These files are the favorite target for those placing obfuscated code
triggering malware.

Lets call this hiding place, *the swamp*

drain-swamp has build plugins. Ideal for creating generated files like:

- setuptools-scm version file

- dependency lock and unlock files

Isn't protobuf also compiled? Great fit for a build plugin

Boilerplate
""""""""""""

Authors and maintainers deal with many packages. Boilerplate code is
copy+paste into multiple packages.

- an eye sore
- completely untested code
- small variations leak in
- code quality and feature improvements are less likely to happen

drain-swamp started out to reduce this

Updating docs
""""""""""""""

updates

- Sphinx ``docs/conf.py``
- CHANGES.rst
- NOTICE.txt

This is done skillfully, applying a generic technique, snippets. Static
config files become dynamic, encouraging automation.

flexible semantic versioning
"""""""""""""""""""""""""""""

In the build workflow, setting the version tag comes last, not before the build.

When building, the semantic version would come from the version file.
Which makes it's way into the sdist tarball

.. code:: shell

   python -m build -C--kind="0.5.1a4.dev6" -C--set-lock="0"

One of our build plugins will update the version file.

Lets check the license. Hmmm Apache2.0 abandonware, that's a great
reason to turn the dependency lock off.

It's slightly more messy than this, the jist is, config settings gets
passed to all build plugins.

**kind** can be:

*current* (or *now*) -- get semantic version from git

*tag* -- semantic version str from version file

a semantic version str -- so have full control over what it becomes

There is no bump version. Cuz we adults and semantic version str
isn't limited to *major.minor.patch*

Nor does changelog entries with *feat* and *fix* lines necessitate a
major or minor release bump.

bump version is the opposite, dumbing things down.

Extensions
-----------

*Snip* is the generic technique to make an otherwise static
config file, dynamic. Simple explanation: static portion is surrounded
by comments turning it into a snippet.

This technique is applied to aid DevOps.

Comes with these *extensions*:

**pipenv-unlock** -- switch on/off dependency locks

``pyproject.toml`` is not dynamic and it's not supposed to be dynamic. In
an ideal world, it would be static.

Authors disappear or die. Unfunded projects quickly become
abandonware. Packages with locked dependencies do not age well.

pipenv-unlock is a light switch to turn on/off dependency locking.

refresh both .unlock and .lock files. During build time, .lnk shortcut is created.

An author dies, discovers girls, or gets a job scrapping gum off sidewalks. No worries

refreshes symlinks (.lnk)

.. code-block:: shell

   pipenv-unlock refresh --set-lock "off"
   pipenv-unlock refresh --set-lock "on"

lock / unlock dependencies

.. code-block:: shell

   pipenv-unlock lock
   pipenv-unlock unlock

.. csv-table:: Following in Click's footsteps
   :header: "State", "Possible values"
   :widths: auto

   "lock", """1"", ""true"", ""t"", ""yes"", ""y"", ""on"""
   "unlock", """0"", ""false"", ""f"", ""no"", ""n"", ""off"""

**drain-swamp**

In ``conf.py``, there are some dynamic fields. Each package release,
has to change these fields:

- version
- release
- release_date
- copyright (start year and author name)

Reduces reliance on ``igor.py``

**scm-version** -- Version file support

Replaces getting version from setup.py or from setuptools-scm

Get scm (source control management) version

.. code-block:: shell

   scm-version get

0.5.2.dev0+g2988c13.d20240724

Get from version file

.. code-block:: shell

   drain-swamp tag

0.5.2

Write a semantic version str to version file. :code:`drain-swamp pretag`
to check/fix semantic version str

.. code-block:: shell

   scm-version write "0.5.2post0.dev1"

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

textwrap.dedent("""\\ means, remove any indention and escape
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

Ideally, cut out entirely or as much as is reasonable.

File formats -- supported

Lines starting with pound sign **#** are considered comments:

- python
- bash
- pyproject.toml
- Linux config files

.. |last-commit| image:: https://img.shields.io/github/last-commit/msftcangoblowm/drain-swamp/master
    :target: https://github.com/msftcangoblowm/drain-swamp/pulse
    :alt: last commit to gauge activity
.. |test-status| image:: https://github.com/msftcangoblowm/drain-swamp/actions/workflows/testsuite.yml/badge.svg?branch=master&event=push
    :target: https://github.com/msftcangoblowm/drain-swamp/actions/workflows/testsuite.yml
    :alt: Test suite status
.. |quality-status| image:: https://github.com/msftcangoblowm/drain-swamp/actions/workflows/quality.yml/badge.svg?branch=master&event=push
    :target: https://github.com/msftcangoblowm/drain-swamp/actions/workflows/quality.yml
    :alt: Quality check status
.. |docs| image:: https://readthedocs.org/projects/drain-swamp/badge/?version=latest&style=flat
    :target: https://drain-swamp.readthedocs.io/
    :alt: Documentation
.. |kit| image:: https://img.shields.io/pypi/v/drain-swamp
    :target: https://pypi.org/project/drain-swamp/
    :alt: PyPI status
.. |versions| image:: https://img.shields.io/pypi/pyversions/drain-swamp.svg?logo=python&logoColor=FBE072
    :target: https://pypi.org/project/drain-swamp/
    :alt: Python versions supported
.. |license| image:: https://img.shields.io/github/license/msftcangoblowm/drain-swamp
    :target: https://pypi.org/project/drain-swamp/blob/master/LICENSE
    :alt: License
.. |stars| image:: https://img.shields.io/github/stars/msftcangoblowm/drain-swamp.svg?logo=github
    :target: https://github.com/msftcangoblowm/drain-swamp/stargazers
    :alt: GitHub stars
.. |mastodon-msftcangoblowm| image:: https://img.shields.io/mastodon/follow/112019041247183249
    :target: https://mastodon.social/@msftcangoblowme
    :alt: msftcangoblowme on Mastodon
.. |codecov| image:: https://codecov.io/gh/msftcangoblowm/drain-swamp/branch/master/graph/badge.svg?token=13dL2Owydg
    :target: https://codecov.io/gh/msftcangoblowm/drain-swamp
    :alt: drain-swamp coverage percentage
.. |black| image:: https://img.shields.io/badge/code%20style-black-000000.svg
   :target: https://github.com/ambv/black
.. |downloads| image:: https://img.shields.io/pypi/dm/drain-swamp
.. |implementations| image:: https://img.shields.io/pypi/implementation/drain-swamp
.. |platforms| image:: https://img.shields.io/badge/platform-linux-lightgrey

.. https://img.shields.io/badge/platform-windows%20%7C%20macos%20%7C%20linux-lightgrey

.. |feature banner| image:: /docs/_static/drain-swamp-banner-640-320.svg
   :alt: drain-swamp features build plugins and dependency lock switch
