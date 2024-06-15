About authors
==============

As a package author, have reservations about the arguments made by pipenv,
pip-compile-multi, and pip-tools.

For those unfamiliar, those deal with dependency management.

Before going into their claims, would like to introduce you to authors.

as-is
------

Package authors and maintainers are, for the most part, unpaid. If
there income source is not from their FOSS efforts, their time will
be drawn away from package maintenance, or even worse, eventually
leads to them disappearing.

The packages are perfectly fine besides a few package dependencies
constraints that are out of date or unnecessarily constrained.

Forking a project just cuz has dependency constraint issues is the realm
of package authors, not the average Python user. And both don't want
this burden!

So it's safe to assume, on a long enough time scale, all authors disappear. And
this wouldn't be a show stopper if they hadn't locked dependencies.

We are incompetent
"""""""""""""""""""

If we aren't then someone else is.

As evidence of our incompetence, almost all Python packages lack
semantic versioning support and rarely use versioning beyond,
``[major].[minor].[micro]``.

Instead of learning semantic versioning, the version str is hardcoded
in a file. The version actually comes from git, not your package.
setuptools-scm generates the version file for the wheel, but no
version file exists in the tarball.

The benefit of this is can produce development releases, prereleases,
release candidate releases, and post releases.

So what happens next? Instead of learning semantic versioning, we switch
out the build backend. Anything except setuptools. Afterwards still
no semantic versioning.

Have it both ways
------------------

I heard a rumor, locking dependencies is the way forward. Except it
can trip up normies (pip users) and these dependencies have a very high
likelihood of, at some point, not being regularly updated.

Would like a switch to lock and unlock dependencies.

Arrives at work

.. code:: shell

   pipenv-unlock lock --snip="bill_murphys_zombie_movie_theater_popcorn"

Comes back home

.. code:: shell

   pipenv-unlock unlock --snip="bill_murphys_zombie_movie_theater_popcorn"

At which point, can inconveniently die without inconveniencing the rest of us.

(The ``--snip`` option is needed only when there are multiple snippets / file.
The snippet code, here, only for the love of cringe culture ...)

That one guy
-------------

Captain Obvious the master of facts everyone already knows says::

  pip strongly discourages making multiple wheels with slight variations,
  besides archecture or OS, for the same release

Remember that?

Have encountered authors whom are: unresponsible, dismissive, or simply disappeared.

pip advice, *well shucks*,

Contact the author or fork the project

drain-swamp says::

   Don't lock the dependencies in the first place. Or have an easy means to
   unlock those dependencies.

What drain-swamp is not:

- build system backend with maybe own frontend e.g. poetry hatch

- pip/venv workflow tool e.g. pipx
