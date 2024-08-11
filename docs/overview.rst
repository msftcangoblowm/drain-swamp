.. raw:: html

   <div style="visibility: hidden;">

Overview
=========

.. raw:: html

   </div>

|feature banner|

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

.. code-block:: shell

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

Get :abbr:`scm (source control management)` version

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

.. |feature banner| image:: _static/drain-swamp-banner-640-320.*
   :alt: drain-swamp features build plugins and dependency lock switch
