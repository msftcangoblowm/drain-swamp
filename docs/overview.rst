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

Boilerplate
""""""""""""

Authors and maintainers deal with many packages. Boilerplate code is
copy+paste into multiple packages.

- an eye sore
- completely untested code
- small variations leak in
- code quality and feature improvements are less likely to happen

``drain-swamp`` started out to reduce this

Generated files
---------------

For Python packages, which contain generated files, UX is improved
by generating those files during the build process.

These batteries are included:

- setuptools-scm version file

- dependency lock switch

  ``.lock``, ``.unlock``, and ``.lnk`` files

Micro services use message queues for inter-process communications.
The messages use ``protobuf`` message protocol which produces a
generated file. That **must** be part of the build process.

Would be a good fit for a build plugin

version file
""""""""""""

The build plugin for interacting with version file, it's
about having flexibility on which version str to use.

Different circumstances calls for different version str

- CI tagged release workflow needs ``tag`` version from the version file

- CI on push workflows need the ``current`` version

- :code:`python -m build` provide the new version str

This flexibility allows to test building a package
before :code:`git push` or a tagged release.

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

Features
--------

Updating docs
""""""""""""""

Before a commit, update the date and version str in several locations

updates

- Sphinx ``docs/conf.py``
- CHANGES.rst
- NOTICE.txt

This Sphinx conf.py contains a snippet. The entire contents of the snippet
is replaced. This technique is now a separate package,
drain-swamp-snippet_

.. _drain-swamp-snippet: https://pypi.org/project/drain-swamp-snippet

Dependency lock switch
""""""""""""""""""""""

Authors disappear or die. Unfunded projects quickly become
abandonware. Packages with locked dependencies do not age well.

Lets check the license. Hmmm Apache2.0 abandonware, that's a great
reason to turn the dependency lock off.

**reqs** is a light switch to turn on/off dependency locking.

On your repo, set a CI variable and that is the switch.

When the repo is inactive, turn off the switch and make a release
without dependency locking.

**How it works**

A snippet in ``pyproject.toml`` containing both
dependencies and optional-dependencies. There is additional
meta data as well.

Refresh both ``.unlock`` and ``.lock`` files. During build time,
``.lnk`` shortcut is created.

Create dependency files with the ``.in`` extension.
These include the dependencies and lines with ``-r`` and
``-c`` to include other dependency files.

Then

Create both lock and unlock dependency files

.. code-block:: shell

   reqs fix
   reqs unlock

build config settings
""""""""""""""""""""""

The Python packages build process occurs within a subprocess.
The hottest trending topic is how to pass config settings to
this subprocess?

Right before :code:`python -m build`, depending on context,
use whichever method is most appropriate.

**custom build backend**

This would only work for a custom build backend. Will see
it's use only in drain-swamp howto.txt

.. code:: shell

   python -m build -C--kind="0.5.1a4.dev6"

Unless authoring a custom build backend, can safely
ignore.

**cli**

Use :ref:`Bash workaround <gh_dsa:bash>`

**tox**

Similiar to *cli*. During ``pre_command``, the TOML file and
environment variable DS_CONFIG_SETTINGS are created.

:ref:`tox test <gh_ds:tox-test>`

:ref:`tox <gh_ds:tox>`

**github workflows**

:ref:`drain-swamp-action gh action <gh_dsa:action>` creates the TOML
file and environment variable DS_CONFIG_SETTINGS.

Immediately after this gh action, there is fair bit of:

upload and download artifacts, between step communication,
and maybe between jobs communication.

- matrix size == 1 :ref:`release workflow <gh_ds:release>`

There is one job. Communication is only between steps. e.g. ubuntu-latest-3.10

- matrix size > 1 :ref:`quality workflow <gh_ds:quality>`

There are several jobs. A parent job occurs once. Constraining artifact upload
to only occur once.

.. seealso::

   :ref:`drain-swamp gh workflows <gh_ds:workflows>`

.. |feature banner| image:: _static/drain-swamp-banner-640-320.*
   :alt: drain-swamp features build plugins and dependency lock switch
