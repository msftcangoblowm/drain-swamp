.. this will be appended to README.rst

Changelog
=========

..

   Feature request
   .................

   - Confirm setuptools-scm file finders are being called?

   - self hosted package server. See article
     https://safjan.com/Create%20Self-Hosted%20Python%20Package%20Repository/

   Known regressions
   ..................

   - release.yml
     affects:
     py39
     monkey/wrap_infer_version
     reproduce:
     encountered when using :code:`python -m build` getting dist.metadata.name
     example:
     e.g. gh workflow quality --> isort black flake8
     https://github.com/msftcangoblowm/drain-swamp/actions/runs/11362396076/job/31604183207
     discussion:
     https://github.com/pypa/setuptools/issues/3452
     https://github.com/pypa/setuptools/pull/3832

   - activate drain-swamp .venv
     logging-strict has no dependency, drain-swamp. However from logging-strict
     package base folder :code:`pre-commit run --all-files --show-diff-on-failure`
     fails.
     LookupError: toml section missing ...logging_strict/pyproject.toml does not
     contain a tool.drain-swamp section

   - rtd installs does not build or run a workflow. Does rtd give any workaround?
     Use github pages instead of rtd. Unless rtd respects workflows

   - test build sdist to detect issue with build backend

   - tox does not pass in config_settings. Read in DS_CONFIG_SETTINGS

   Commit items for NEXT VERSION
   ..............................

.. scriv-start-here

.. _changes_2-1-1:

Version 2.1.1 — 2025-01-07
--------------------------

- ci: bump actions versions
- chore: update requirements
- chore(pre-commit): update requirements
- refactor: remove logging config dict constants.LOGGING
- test: add pytest-logging-strict support

.. _changes_2-1-0:

Version 2.1.0 — 2024-12-15
--------------------------

- fix(dev.lock): requires latest wreck release
- chore: bump wreck
- fix(docs/conf.py): sphinx conf broken import
- fix(pyproject.toml): add missing build dependency wreck
- feat: add wreck support
- fix: pyproject.toml section pipenv-unlock (#10)
- refactor: remove entrypoint pipenv-unlock
- docs: reduce links in source code not sphinx inventory files

.. _changes_2-0-0:

Version 2.0.0 — 2024-11-06
--------------------------

- feat: approach for requirements organize by venvs rather than folders
- feat(lock_inspect): add unlock_compile implementation
- refactor(lock_toggle): move InFile related --> lock_infile
- docs(conf.py): add autodoc_type_aliases for documenting TypeAlias
- test: lock_util.replace_suffixes_last rather than _safe_path.replace_suffixes
- test(lock_infile): add test for InFiles.write

.. _changes_1-8-6:

Version 1.8.6 — 2024-10-30
--------------------------

- feat: add command pipenv-unlock fix (#14)
- fix(lock_inspect): Pins.subset_req Windows unsafe path comparison
- refactor(lock_inspect): add _wrapper_pins_by_pkg Pins.by_pkg wrapper function
- test(test_lock_inspect.py): use get_locals on _wrapper_pins_by_pkg
- chore(MANIFEST.in): remove global include of .lnk files
- chore(tox-test.ini): turn on pytest verbose and show locals

.. _changes_1-8-5:

Version 1.8.5 — 2024-10-24
--------------------------

- ci(python-nightly): for tox from python version strip -nightly
- chore(branch-test-others): update to use env.OS_SHORT
- chore(python-nightly): update to use env.OS_SHORT
- ci(tox-test.ini): from setenv remove COVERAGE_FILE
- ci(tox-test.ini): allow coverage combine no data to combine error
- ci(testsuite): env.OS_SHORT unavailable in same step
- ci(testsuite): append OS_SHORT into GITHUB_ENV
- feat(tox-test.ini): add cov.pth to inform coverage about subprocess
- ci(testsuite): try tox -e with matrix.os-short
- ci(testsuite): tox-test use -e to restrict to one python version
- fix(mypy): really annoying catch 22 try-except import block
- ci: bump msftcangoblowm/drain-swamp-action to 1.0.2
- chore: add pins-cffi.in. Adjust tests
- chore: bump cffi to 1.17.1
- chore: bump logging-strict to 1.3.6
- chore: bump pyproject-hooks to 1.2.0
- chore: bump logging-strict to 1.3.5
- fix: dist.metadata.name --> dist.name setuptools#3319
- refactor: remove plugin ds_refresh_links
- refactor: stop editing pyproject.toml snippet
- refactor: remove .lnk stop using .lnk also in ci
- refactor: remove pipenv-unlock is_lock and pipenv-unlock refresh
- fix(pyproject.toml): required dependencies unlock
- ci: pip install requirements on one line
- ci(release): try --use-pep517 to deal with setuptools#3319
- fix(tox.ini): flake8-pyi and black disagree. Ignore flake8 failure
- chore: bump drain-swamp-snippet to 1.0.1
- chore: bump logging-strict to 1.3.4
- fix: add support for .shared.in (#13)
- fix: pins.in and prod.in now have extension .shared.in
- fix: For multiple suffixes check only last suffix
- feat: add pyproject_reading from setuptools-scm (MIT)
- feat(patch_pyproject_reading): add TOML array of tables support
- feat(pep518_read): find_pyproject_toml add support for test files
- fix(pep518_read): find_pyproject_toml given a valid file path, avoid reverse search
- ci: condense multiple pip calls

.. _changes_1-8-3:

Version 1.8.3 — 2024-10-05
--------------------------

- ci(test-coverage): unique job name and py39 --> py310
- ci(quality-docs): fix outputs job name
- fix: importlib-metadata ensure use latest version
- refactor: build plugins prefix plugin name to messages
- refactor(lock_toggle): improve instructions when missing .unlock or .lock files
- ci(quality-docs): separate workflow for docs
- ci: bump pypa/gh-action-pypi-publish to 1.10.3
- ci: drain-swamp-action version is 1.0.1 not v1.0.1
- fix: click.Path parameters receive as pathlib.Path. Previously str
- chore: normalize pip and setuptools versions
- chore: bump actions/checkout to v4.2.0
- docs: add mission and contributing
- chore: rtd and tox.ini target docs py39 --> py310
- docs: py39 --> py310
- chore: two venvs. docs py310. Everything else py39
- docs(Makefile): catch all target comment out

.. _changes_1-8-2:

Version 1.8.2 — 2024-09-23
--------------------------

- fix: resolve_path cannot find executable fallback to pep366 invocation
- refactor: rename tests/test_snip --> tests/_good_snips
- chore: remove dependency pytest-cov
- docs: rewrite front page
- ci: from drain-swamp-action remove input fetch_tags
- ci: actions/checkout put repository in with block
- ci(release): kind tag not env.RELEASE_VERSION

.. _changes_1-8-1:

Version 1.8.1 — 2024-09-20
--------------------------

- ci: use msftcangoblowm/drain-swamp-action
- chore(workflows): review gha versions

.. _changes_1-8-0:

Version 1.8.0 — 2024-09-20
--------------------------

- feat: use package drain-swamp-snippet
- refactor: remove module drain_swamp.snip
- chore: add build requirement dependency drain-swamp-snippet

.. _changes_1-7-2:

Version 1.7.2 — 2024-09-11
--------------------------

- test(static dependencies): remove tool.pipenv-unlock section
- fix(backend_abc): from pyproject.toml process additional folders
- chore: turn all is_module_debug flags off
- chore(cli_unlock): comment out __debug__ blocks

.. _changes_1-7-1:

Version 1.7.1 — 2024-09-10
--------------------------

- ci(testsuite): pypy-3.9 upstream issue sys.executable suffix wrong case
- test(backend_abc): copy over .lock and .unlock files, not just empty files
- fix(backend_abc): fix sorting hat parsing optional dependencies
- fix(backend_abc): sorting hat on Windows sort resolved
- feat(safe_path): add replace_suffixes
- fix(backend_abc): sorting hat strategy differs by platform
- fix(run_cmd): cmd sequence --> str --> shlex.split
- test(backend_abc): confirm cause not run_cmd pipenv-unlock refresh
- fix: sorting hat combine paths with resolve_joinpath
- fix(run_cmd): shlex.split set posix parameter
- refactor: remove exception BackendNotSupportedError
- refactor: remove the concept of backend awareness
- refactor: backend_abc no longer an abc
- fix: careful not to write Windows linesep into a TOML file
- refactor: where possible _to_purepath rather than PurePosixPath and PureWindowsPath
- fix: remove snip constructor param is_quiet
- fix(backend_setuptools): dependency file relative path treat as PurePosixPath
- fix: TOML format path must be single quoted
- feat: automagically choose platform supported dependency lock copy implementation
- feat: packaging process symlinks --> files. Check for either
- test: On Windows, no executable true, but there might be git
- fix: strftime %D and %T works on all platforms
- fix: run_cmd file not found error message is platform specific
- test: if Windows, unlink file not symlink
- fix: patch strftime. Platform consistency
- test(backend_setuptools): apply platform line seperator

.. _changes_1-7-0:

Version 1.7.0 — 2024-09-06
--------------------------

- feat: Windows support

.. _changes_1-6-11:

Version 1.6.11 — 2024-09-06
---------------------------

- fix(lock_toggle): on Windows rather than symlink copy file
- style(lock_toggle): log folder access permissions

.. _changes_1-6-10:

Version 1.6.10 — 2024-09-06
---------------------------

- fix(lock_toggle): move open folder file descriptor into try-except block
- fix(safe_path): resolve_joinpath maintain Path and PurePath flavor

.. _changes_1-6-9:

Version 1.6.9 — 2024-09-06
--------------------------

- style: pipenv-unlock refresh improve log messages

.. _changes_1-6-8:

Version 1.6.8 — 2024-09-06
--------------------------

- feat: print logging, by entrypoint or entrypoint cmd, if __debug__ and not running tests

.. _changes_1-6-7:

Version 1.6.7 — 2024-09-05
--------------------------

- fix(version_semantic): fixes the zero commits semantic str

.. _changes_1-6-6:

Version 1.6.6 — 2024-09-05
--------------------------

- chore: upgrade cffi. On macos, cffi build fail

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
