.. this will be appended to README.rst

Changelog
=========

..

   Feature request
   .................

   - article discussing when to use: alpha, beta, post, and rc

   - break up getting started. Configure one piece at a time. Small victories

   - self hosted package server. See article
   https://safjan.com/Create%20Self-Hosted%20Python%20Package%20Repository/

   Known regressions
   ..................

   - (upstream) click.Path(resolve_path=True) chokes given a non-Path. Gave a float

     type=click.Path(exists=True, file_okay=True, dir_okay=True, resolve_path=True),

     Expect: Ideally use default value, fallback to exit code 2

     Actual: uncatchable TypeError crash

     `click#2742 <https://github.com/pallets/click/issues/2742>`_

   Commit items for NEXT VERSION
   ..............................

.. scriv-start-here

.. _changes_0-5-0:

Version 0.5.0 — 2024-06-10
--------------------------

- feat(pipenv-unlock): add command is_lock
- feat(swamp-drain): add command cheats
- refactor(entrypoints): py313+ importlib to ignore __package__. Use __spec__
- fix: click.Path(resolve_path=True) resolves relative path --> absolute path
- test(pep366): run commands directly. Use only source code
- test(pep366): integration test. Isolated from 1st run unit tests
- refactor: retire igor.py

.. _changes_0-4-0:

Version 0.4.0 — 2024-06-07
--------------------------

- style: Little shop of horror motorcycle googles
- feat(snip): infer snippet_co. When not provided and only one snippet
- feat: list snippets
- refactor: remove redundant entrypoint, sphinxcontrib-snip

.. _changes_0-3-0:

Version 0.3.0 — 2024-06-04
--------------------------

- style: little shop of horrors obedient girlfriend
- fix: build package bomb when encounter ``.in`` files with -c lines
- feat(pipenv-unlock): compile requirements .in --> .unlock
- refactor: add constant SUFFIX_UNLOCK to not confuse .in and .unlock
- refactor(snip): add Enum, ReplaceResult. Retire optional boolean

.. _changes_0-2-0:

Version 0.2.0 — 2024-05-28
--------------------------

- style: little shop of horrors overly dramatic water spout
- feat(drain-swamp): add command, pretag. Sanitize semantic version str
- refactor(igor.py): remove do_edit_for_release do_bump_version do_build_next do_pretag
- ci(howto.txt): sanitize a semantic version str
- ci(howto.txt): should be master, not main
- refactor(igor.py): remove print_banner
- style: package was renamed, in requirments .in files, refer to the new package name
- refactor: add setuptool-scm as a dependency. Get the current version
- refactor(version_semantic): private member prepend with single underscore
- docs: inventory for setuptools-scm
- docs: add doctests for _version.py. Explain pretag with examples
- docs: show private members of version_semantic.py
- docs: fix doctest which explain snippet usage
- fix: get current version no longer update _version.py
- feat(cli_igor): add command, current. Gets current version

.. _changes_0-1-0:

Version 0.1.0 — 2024-05-23
--------------------------

- style: little shop of horrors shrine candles
- style: dentist keep shrine with candles. Building yet to burn down
- feat: snippets technique extended to support optional snippet code
- feat: build package with full semantic versioning support
- feat: lock and unlock dependences
- feat: update Sphinx docs/conf.py, NOTICE.rst, and CHANGES.rst

.. scriv-end-here
