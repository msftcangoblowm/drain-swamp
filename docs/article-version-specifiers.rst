Semantic versions
==================

This is a terse review of semantic versioning beyond just
``[major].[minor].[micro]`` scheme

Emphasis is placed on explaining when to use: alpha, beta, rc, and post releases

`[Full article] <https://packaging.python.org/en/latest/specifications/version-specifiers/#version-scheme>`_

Public version identifiers
---------------------------

The canonical public version identifiers MUST comply with the following scheme:

.. code-block:: text

   [N!]N(.N)*[{a|b|rc}N][.postN][.devN]

Local version identifiers
---------------------------

Local version identifiers MUST comply with the following scheme:

.. code-block:: text

   <public version identifier>[+<local version label>]

They consist of a normal public version identifier (as defined in the
previous section), along with an arbitrary “local version label”, separated
from the public version identifier by a plus. Local version labels have
no specific semantics assigned, but some syntactic restrictions are imposed.

Pre-releases
-------------

Some projects use an “alpha, beta, release candidate” pre-release cycle to
support testing by their users prior to a final release.

If used as part of a project’s development cycle, these pre-releases are
indicated by including a pre-release segment in the version identifier:

.. code-block:: text

   X.YaN   # Alpha release
   X.YbN   # Beta release
   X.YrcN  # Release Candidate
   X.Y     # Final release

Final releases
---------------

A version identifier that consists solely of a release segment and optionally an epoch identifier is termed a “final release”.

The release segment consists of one or more non-negative integer values, separated by dots:

.. code-block:: text

   N(.N)*

Post-releases
--------------

Some projects use post-releases to address minor errors in a final release that do not affect the distributed software (for example, correcting an error in the release notes).

Developmental releases
-------------------------

Some projects make regular developmental releases, and system packagers (especially for Linux distributions) may wish to create early releases directly from source control which do not conflict with later project releases.

If used as part of a project’s development cycle, these developmental releases are indicated by including a developmental release segment in the version identifier:

.. code-block:: text

   X.Y.devN    # Developmental release
   X.YaN.devM       # Developmental release of an alpha release
   X.YbN.devM       # Developmental release of a beta release
   X.YrcN.devM      # Developmental release of a release candidate
   X.Y.postN.devM   # Developmental release of a post-release
