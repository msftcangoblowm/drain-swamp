About authors
==============

As a package author, have reservations about the arguments made by pipenv,
pip-compile-multi, and pip-tools.

For those unfamiliar, those deal with dependency management.

Before going into their claims, would like to introduce you to authors.

as-is
------

Package authors and maintainers are, for the most part, unpaid. And this
eventually leads to them disappearing. The packages are perfectly fine
besides a few package dependencies constraints that are out of date or
unnecessarily constrained.

Forking a project just cuz has dependency constraint issues is the realm
of package authors, not the average Python user. And both don't want
this burden!

So it's safe to assume, on a long enough time scale, all authors disappear. And
this wouldn't be a show stopper if they hadn't locked dependencies.

We are incompetent
"""""""""""""""""""

If we aren't then someone else is.

As evidence of our incompetence, almost all Python packages lack
semantic versioning support. Instead of learning semantic versioning,
the version str is hardcoded in a file. The version actually comes from
git, not your package. setuptools-scm generates the version
file for the wheel, but no version file exists in the tarball.

The benefit of this is can produce development releases, prereleases,
release candidate releases, and post releases.

So what happens next? Instead of learning semantic versioning, we switch
out the build backend. Anything except setuptools. Afterwards still
no semantic versioning.

As long as packages have simple tagged versions like 1.1.2 piptools and
pip are ok. But of course, there has to be that one guy who understands
semantic versioning and has released a package with a post release.

Piptools gets moody, inconsistently sometimes chokes, by choosing the
wrong dependency version.

pip chokes by plunging the end user into dependency hell

And their advice? Contact the author or fork the package.

Have it both ways
------------------

In an idealized world, pipenv is 100% right, if we enjoy ignore normies
(pip users)

However some of us avoid social isolation by ostrication. We live in the real world,
which resembles a sewer, filled with rats, and xz maintainers. And would
much prefer being able to easy resolve dependency conflicts by not
nurturing/enabling them in the first place!

And counter-intuitively going to our day jobs and then doing the exact opposite

So would like to lock and unlock dependencies, with one command.

Goes to work

.. code:: shell

   pipenv-unlock lock --snip="bill_murphys_zombie_movie_theater_popcorn"

Comes back home

.. code:: shell

   pipenv-unlock unlock --snip="bill_murphys_zombie_movie_theater_popcorn"

Could the snippet code be removed from the snippet in ``pyproject.toml``?

Of course, but what fun would that be?

Admit it!

In life, put up with loads more annoying stuff than having to worry
about which zombie movie that snippet code is from?

That one guy
-------------

Captain Obvious the master of facts everyone already knows says::

  pip strongly discourages making multiple wheels with slight variations,
  besides archecture or OS, for the same release

Remember that?

Me too! Then encountered authors and some disappeared. pip, *well shucks*
