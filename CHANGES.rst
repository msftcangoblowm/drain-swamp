.. this will be appended to README.rst

Changelog
=========

..

   Feature request
   .................

   - in pipenv-unlock, is_lock. 0 is lock. 1 is unlock

   - self hosted package server. See article
   https://safjan.com/Create%20Self-Hosted%20Python%20Package%20Repository/

   Known regressions
   ..................

   Commit items for NEXT VERSION
   ..............................

.. scriv-start-here

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
