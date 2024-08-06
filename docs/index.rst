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

- pyproject.toml dependencies locks
- semantic versioning -- current, tag (in version file), semantic version str
- build Python package uses plugins

updating

- Sphinx ``docs/conf.py``
- CHANGES.rst
- NOTICE.txt

This is done skillfully, applying a generic technique, snippets. Static
config files become dynamic, encouraging automation.

That's a lot of boilerplate code ... gone! Not all, but most.

.. PYVERSIONS

* Python 3.9 through 3.12, PyPy

**New in 1.2.x**

generate version file if missing; ci workflows recreate generated files;
docs use available version str; badges; cease ignoring version file;

**New in 1.1.x**

tox-test.ini; tox.ini; gha; build backend DS_CONFIG_SETTINGS support;
add gha variable DRAINSWAMP_SET_LOCK;

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

Writes a semantic version str to version file. :code:`drain-swamp pretag`
to check/fix semantic version str

.. code-block:: shell

   scm-version write "0.5.2post0.dev1"

.. tableofcontents::
