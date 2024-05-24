.. this will be appended to README.rst

Changelog
=========

..

   Feature request
   .................

   self hosted package server. See article
   https://safjan.com/Create%20Self-Hosted%20Python%20Package%20Repository/

   Known regressions
   ..................

   - :code:`python -m build` reads both dependencies and optional-dependencies.
     The requirements files cannot include pip-tools syntax like ``-c prod.in``.
     Reproduce:
     In pyproject.toml, change dependencies to ``.in`` files.
     Run :code:`python -m build`
     or :code:`src/drain_swamp/cli_igor.py build --kind="0.0.1"`
     Result: build bombs
     Mitigation: Recursively include .in file requirements to build .unlock files

   Commit items for NEXT VERSION
   ..............................

   - feat(drain-swamp): add command, pretag. Sanitize semantic version str
   - refactor(igor.py): remove do_edit_for_release do_bump_version do_build_next do_pretag
   - ci(howto.txt): sanitize a semantic version str
   - ci(howto.txt): should be master, not main

.. scriv-start-here

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
