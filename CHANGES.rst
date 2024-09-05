.. this will be appended to README.rst

Changelog
=========

..

   Feature request
   .................

   - On Windows, refresh links fails. Combining dependencies relative path with cwd path
     Use __debug__ to turn on module level logging AND send the logging to stdout

   - update workflows to detect project name. If ``drain-swamp``, build
     use config_settings options. Otherwise do the workaround. Export
     env variable which contain path to temp .toml file. File contain parsable
     config_settings which can be read from a subprocess

   - Makefile target to add the environment variable with path to a config_settings toml file

   - Confirm setuptools-scm file finders are being called?

   - self hosted package server. See article
   https://safjan.com/Create%20Self-Hosted%20Python%20Package%20Repository/

   Known regressions
   ..................

   - py310 regression. backport of code from py313
     Caused by https://github.com/pypy/pypy/pull/5003
     mentioned in https://github.com/pypy/pypy/issues/5004
     affects python-nightly.yml py310 Error in sys.excepthook TypeError: PatchedTracebackException.format() got an unexpected keyword argument 'colorize'

   - rtd installs does not build or run a workflow. Does rtd give any workaround?
     Resolve rtd issue before migrate sphinx-external-toc-strict to use drain-swamp

   - test build sdist to detect issue with build backend

   - scm-version write in version_tuple semantic version str missing local

   - tox does not pass in config_settings. Read in DS_CONFIG_SETTINGS

   Commit items for NEXT VERSION
   ..............................

.. scriv-start-here

.. _changes_1-6-5:

Version 1.6.5 — 2024-09-05
--------------------------

- feat: add safe path module
- ci(release): update pypa/gh-action-pypi-publish

.. _changes_1-6-4:

Version 1.6.4 — 2024-09-05
--------------------------

- ci: add macos to os.matrix
- ci: update gha versions
- chore(pre-commit): add interrogate
- chore(tox): add interrogate target
- docs: add interrogate package and requirements. Ensure 100% documentation.
- test: in each test, document pytest command to get coverage for one module
- style: update project.urls so recognized by pypi

.. _changes_1-6-3:

Version 1.6.3 — 2024-09-03
--------------------------

- feat: add BackendType repr
- feat(_run_cmd): add Windows safe resolve_path
- feat(_run_cmd): cmd str support
- ci(branch-test-others): refresh .lnk rather than build package
- ci(branch-test-others): fix requirement file suffix
- fix(cli_igor): seed changelog add check file not found and missing start token
- test: remove non-regression pytest.xfail

.. _changes_1-6-2:

Version 1.6.2 — 2024-08-31
--------------------------

- ci(coverage): update codecov/codecov-action to latest commit
- ci(branch-test-others): add workflow for branches to test on MacOS and Windows

.. _changes_1-6-1:

Version 1.6.1 — 2024-08-22
--------------------------

- ci(python-nightly): try py312 and py313 tagged not nightly

.. _changes_1-6-0:

Version 1.6.0 — 2024-08-22
--------------------------

- fix(lock_toggle): recognize .in files options -c and -r
- refactor(lock_toggle): enum.Enum to identify sets InFiles._files and InFiles._zeroes
- refactor(lock_toggle): add .in file line pattern match functions
- ci(python-nightly): tox run only tests folder
- docs: add favicons 200x200 svg and 180x180 apple-touch-icon

.. _changes_1-5-4:

Version 1.5.4 — 2024-08-20
--------------------------

- docs(.gitattributes): inform git .inv are binary files
- docs: add inventory for pluggy and setuptools
- docs(linkcheck): fix broken links
- docs: fix numerous minor issues
- docs(code manual): toctree --> grid
- style: carefully choose grid item icons

.. _changes_1-5-3post0:

Version 1.5.3.post0 — 2024-08-18
--------------------------------

- docs: add inventory so Sphinx recognize class packaging.version.Version

.. _changes_1-5-3:

Version 1.5.3 — 2024-08-18
--------------------------

- fix(version_semantic): edge cases pre+post. pre+post+dev and post+dev
- docs: inform pypi docs available on both rtd and gh pages

.. _changes_1-5-2:

Version 1.5.2 — 2024-08-16
--------------------------

- ci(gh-pages): deploy with both branch and tag protection nonviable
- ci(gh-pages): allow workflow dispatch

.. _changes_1-5-1:

Version 1.5.1 — 2024-08-16
--------------------------

- ci: add workflow gh-pages
- ci: set concurrency group. quality docs higher priority than gh-pages

.. _changes_1-5-0:

Version 1.5.0 — 2024-08-16
--------------------------

- feat: upgrade dependencies sphinx-external-toc-strict zipp typing-extensions
- fix(version_semantic): get_version recognize definition of release level ambiguous
- fix: resolve dependency hell sphinx-external-toc-strict zipp typing-extensions
- docs: add dependencies sphinx-design sphinx-tabs sphinx-favicon
- docs: improve page elements appearance. Use card grid tabs
- test: when missing dependencies build fail --> pytest.xfail

.. _changes_1-4-0post0:

Version 1.4.0post0 — 2024-08-14
--------------------------

- fix(config_settings): fix module import dotted path
- feat: pipenv-unlock refresh and in plugin set dependency suffix to .lnk
- fix(config_settings): catch and log warning on malformed toml exception
- refactor: move BackendType.read --> TomlParser.read
- refactor: add check is_package_installed. Remove redundant checks

.. _changes_1-3-4:

Version 1.3.4 — 2024-08-11
--------------------------

- docs: fix add requirement sphinx-copybutton

.. _changes_1-3-3:

Version 1.3.3 — 2024-08-11
--------------------------

- fix: fileinput module requires to print each line
- docs: add extension sphinx-copybutton

.. _changes_1-3-2:

Version 1.3.2 — 2024-08-11
--------------------------

- fix: pypi requires tag version. Downgrade pip-tools to tag version

.. _changes_1-3-1:

Version 1.3.1 — 2024-08-11
--------------------------

- fix: pin latest development version of pip-tools

.. _changes_1-3-0:

Version 1.3.0 — 2024-08-11
--------------------------

- feat: .lock files post process paths absolute --> relative
- docs(index): remove table of contents at bottom of page
- docs(overview): hide page section title

.. _changes_1-2-9:

Version 1.2.9 — 2024-08-07
--------------------------

- docs: be explicit supported tested platforms
- docs: add badge platforms

.. _changes_1-2-8:

Version 1.2.8 — 2024-08-07
--------------------------

- docs: tests confirm py313 support. Update pyproject.toml classifiers
- docs: reorder badges
- docs: add badges downloads implementations

.. _changes_1-2-7:

Version 1.2.7 — 2024-08-07
--------------------------

- ci(coverage): fix codecov-action commit sha
- ci(testsuite): py314 not available yet

.. _changes_1-2-6:

Version 1.2.6 — 2024-08-07
--------------------------

- ci(python-nightly): upgrade ubuntu focal 20.04 --> jammy 22.04
- ci(workflows): actions commit sha instead of version tag
- ci(workflows): resume cache python package
- ci(tox): add gh section

.. _changes_1-2-5:

Version 1.2.5 — 2024-08-06
--------------------------

- ci(python-nightly): missing .lnk. build sdist to refresh

.. _changes_1-2-4:

Version 1.2.4 — 2024-08-06
--------------------------

- docs(pdf): missing index page. Move contents index --> overview
- docs: add banner
- docs: rewrite front page of docs
- style: update project description

.. _changes_1-2-3:

Version 1.2.3 — 2024-08-06
--------------------------

- fix(wrap_infer_version): get package folder from env variable or Path.cwd
- refactor: version accessible from package. rtd needs
- ci(rtd): cease ignoring generated version file
- ci(pre-commit): exclude version file
- style: exclude version file from isort black flake8
- style: flake-pyi vs black gentlemenly tussle over trifles
- style: decorator kwarg quoted str, mistaken for a doc string Y020
- docs(README): add badges

.. _changes_1-2-2:

Version 1.2.2 — 2024-08-05
--------------------------

- docs(conf.py): use version from version file otherwise version from snippet

.. _changes_1-2-1:

Version 1.2.1 — 2024-08-05
--------------------------

- fix(entrypoints): remove support for --version option
- refactor: add module constants_maybe. Move constants.__version_app constants.__url__
- ci(tox-test): remove py314
- ci: build sdist to run build plugins to recreate generated files

.. _changes_1-2-0:

Version 1.2.0 — 2024-08-05
--------------------------

- style: watchmen Dr Manhatten stands by does nothing expresses academic curiousity
- feat: add param is_only_not_exists. Create nonexistent version file during write
- fix: version file is generated, git no track. During build, not exists, create it
- fix: in build backend, lazy load plugins after ensuring existence of version file
- fix(build plugins): subprocess cmd use absolute path
- fix(wrap_infer_version): add reverse search for config file
- refactor: remove package exports except exceptions
- refactor: config_settings hack encapsulate in class ConfigSettings
- tests(conftest): fixture finalize remove resources only on success
- tests(conftest): add fixture to verify version file semantic version str
- ci: missing requirements include

.. _changes_1-1-2:

Version 1.1.2 — 2024-08-02
--------------------------

- ci: fix terniary condition use single quotes not double quotes

.. _changes_1-1-1:

Version 1.1.1 — 2024-08-02
--------------------------

- ci: create github repository variable vars.DRAINSWAMP_SET_LOCK
- ci: workflows bypass .lnk symlinks env variable LOCK_SUFFIX and SET_LOCK
- ci(testsuite): refresh dependency locks .lnk before run tests

.. _changes_1-1-0:

Version 1.1.0 — 2024-08-01
--------------------------

- style: fantastic four helicopter jump skiing
- feat: build backend support for DS_CONFIG_SETTINGS
- fix(lock_toggle): py314 deprecation warning for pkgutil.find_loader
- fix(mypy.in): add typing stub dependency types-setuptools
- fix(pip.lock): resolve dependency conflict typing-extensions
- docs(snip): fix param reference parsing issue
- refactor(lock_toggle): sphinx friendly dataclass
- ci: add .github workflows
- ci(tox-test.ini): add separate tox file for running tests
- test(conftest): remove pytest_plugins sphinx.testing.fixtures
- docs(MANIFEST.in): remove exclude src/_version.py
- docs(objects-python-missing): to inventory add entry for dataclasses.InitVar
- docs(README.rst): remove non-vanilla ReStructuredText

.. _changes_1-0-1:

Version 1.0.1 — 2024-07-29
--------------------------

- style: little shop of horrors two dozen roses
- docs: add donation procedure
- docs: add closed source license procedure
- docs: license from apache2 to agplv3+
- docs(MANIFEST.in): remove include lines
- docs(LICENSE): move to base folder. In docs, symlink to base folder file

.. _changes_1-0-0:

Version 1.0.0 — 2024-07-25
--------------------------

- style: little shop of horrors N2O helmet
- fix: require minimum setuptools>=70.0.0 version
- feat: add entrypoint scm-version
- feat: refresh symlink during sdist build or manually pipenv-unlock refresh
- feat: native support for version file
- feat: entrypoint setuptools.finalize_distribution_options use plugins
- feat: setuptools thin wrapped build-backend
- feat(drain-swamp): add tag command
- ci(tox.ini): use symlink .lnk not .lock or .unlock
- ci(gitignore): add to ignore .lnk symlinks
- ci(gitignore): add to ignore rogue src/_version.py
- refactor(setup.py): remove. Use entrypoint distutils.setup_keywords
- refactor(parser_in): class TomlParser. reverse search path_file and d_pyproject_toml
- refactor(_run_cmd): wrap subprocess.run return a tuple
- test: from setuptools-scm, 5 fingers appropriate class WorkDir and pytest fixture wd
- feat(check_type): add check click_bool
- feat: sane fallback when before git init and no version file
- fix(pep518_read): find_project_root remove lru_cache decorator
- docs: do not show blank page after toc
- docs: add make targets pdf-view and html-view
- test(test_wrap_version_keyword): cleanup temporary version file
- test: use resources teardown resources

.. _changes_0-5-1:

Version 0.5.1 — 2024-06-15
--------------------------

- style: little shop of horrors punchable dental hygienist
- refactor: tool.drain-swamp rather than tool.sphinxcontrib-snip
- fix(pipenv-unlock): remove ignore of additional_folders argument to unlock and lock
- test(integration): click allow input as str only
- docs: when to use: alpha, beta, post, and rc
- docs: add section troubleshooting
- docs: add section paid services
- docs: add section api
- docs: add section getting started
- docs: add section why
- style: edit project description

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
