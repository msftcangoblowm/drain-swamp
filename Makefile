.ONESHELL:
.DEFAULT_GOAL := help
SHELL := /bin/bash

# underscore separated; aka sdist and whl names
# https://blogs.gentoo.org/mgorny/2023/02/09/the-inconsistencies-around-python-package-naming-and-the-new-policy/
APP_NAME := drain_swamp

define NORMALIZE_APP_NAME
try:
    from importlib import metadata
except ImportError:
    v = '$(APP_NAME)'.replace('_', "-").replace('.', "-")
    print(v)
else:
    print(metadata.metadata('$(APP_NAME)')['Name']))
endef

#virtual environment. If 0 issue warning
#Not activated:0
#activated: 1
ifeq ($(VIRTUAL_ENV),)
$(warning virtualenv not activated)
is_venv =
else
is_venv = 1
VENV_BIN := $(VIRTUAL_ENV)/bin
VENV_BIN_PYTHON := python3
endif

ifeq ($(is_venv),1)
  # Package name is hyphen delimited
  PACKAGE_NAME ?= $(shell $(VENV_BIN_PYTHON) -c "$(NORMALIZE_APP_NAME)")
  VENV_PACKAGES ?= $(shell $(VENV_BIN_PYTHON) -m pip list --disable-pip-version-check --no-python-version-warning --no-input | /bin/awk '{print $$1}')
  IS_PACKAGE ?= $(findstring $(1),$(VENV_PACKAGES))

  is_wheel ?= $(call IS_PACKAGE,wheel)
  is_piptools ?= $(call IS_PACKAGE,pip-tools)

  find_whl = $(shell [[ -z "$(3)" ]] && extention=".whl" || extention="$(3)"; [[ -z "$(2)" ]] && srcdir="dist" || srcdir="$(2)/dist"; [[ -z "$(1)" ]] && whl=$$(ls $$srcdir/$(APP_NAME)*.whl  --format="single-column") || whl=$$(ls $$srcdir/$(1)*.whl --format="single-column"); echo $${whl##*/})
endif

##@ Helpers

# https://www.thapaliya.com/en/writings/well-documented-makefiles/
.PHONY: help
help:					## (Default) Display this help -- Always up to date
	@awk -F ':.*##' '/^[^: ]+:.*##/{printf "  \033[1m%-20s\033[m %s\n",$$1,$$2} /^##@/{printf "\n%s\n",substr($$0,5)}' $(MAKEFILE_LIST)

##@ Build dependencies

.PHONY: upgrade doc_upgrade diff_upgrade _upgrade
PIP_COMPILE = $(VENV_BIN_PYTHON) -m piptools compile --allow-unsafe --resolver=backtracking

upgrade:				## Update the *.pip files with the latest packages satisfying *.in files.
	@$(MAKE) _upgrade COMPILE_OPTS="--upgrade"

upgrade-one:			## Update the *.pip files for one package. `make upgrade-one package=...`
	@test -n "$(package)" || { echo "\nUsage: make upgrade-one package=...\n"; exit 1; }
	$(MAKE) _upgrade COMPILE_OPTS="--upgrade-package $(package)"

# python -m piptools compile --allow-unsafe --resolver=backtracking -o requirements/pip-tools.lock requirements/pip-tools.in
_upgrade: export CUSTOM_COMPILE_COMMAND=make upgrade
_upgrade:
ifeq ($(is_venv),1)
  ifeq ($(is_piptools), pip-tools)
	@pip install --quiet --disable-pip-version-check --requirement requirements/pip-tools.lock
	$(PIP_COMPILE) -o requirements/pip-tools.lock requirements/pip-tools.in
	$(PIP_COMPILE) -o requirements/pip.lock requirements/pip.in
	$(PIP_COMPILE) -o requirements/kit.lock requirements/kit.in
	$(PIP_COMPILE) -o requirements/prod.lock requirements/prod.in
	$(PIP_COMPILE) --no-strip-extras -o requirements/tox.lock requirements/tox.in
	$(PIP_COMPILE) --no-strip-extras -o requirements/manage.lock requirements/manage.in
	$(PIP_COMPILE) --no-strip-extras -o requirements/dev.lock requirements/dev.in
	$(PIP_COMPILE) --no-strip-extras -o requirements/mypy.lock requirements/mypy.in
  endif
endif

doc_upgrade: export CUSTOM_COMPILE_COMMAND=make doc_upgrade
doc_upgrade: $(VENV_BIN)	## Update the doc/requirements.pip file
ifeq ($(is_venv),1)
  ifeq ($(is_piptools), pip-tools)
	@$(VENV_BIN)/pip install --quiet --disable-pip-version-check --requirement requirements/pip-tools.lock
	$(VENV_BIN)/$(PIP_COMPILE) -o docs/requirements.lock docs/requirements.in
  endif
endif

diff_upgrade:			## Summarize the last `make upgrade`
	@# The sort flags sort by the package name first, then by the -/+, and
	@# sort by version numbers, so we get a summary with lines like this:
	@#      -bashlex==0.16
	@#      +bashlex==0.17
	@#      -build==0.9.0
	@#      +build==0.10.0
	@/bin/git diff -U0 | /bin/grep -v '^@' | /bin/grep == | /bin/sort -k1.2,1.99 -k1.1,1.1r -u -V

##@ Testing

#run all pre-commit checks
.PHONY: pre-commit
pre-commit:				## Run checks found in .pre-commit-config.yaml
	@pre-commit run --all-files

#--strict is on
.PHONY: mypy
mypy:					## Static type checker (in strict mode)
ifeq ($(is_venv),1)
	@$(VENV_BIN_PYTHON) -m mypy -p $(APP_NAME)
endif

#make [check=1] black
.PHONY: black
black: private check_text = $(if $(check),"--check", "--quiet")
black:					## Code style --> In src and tests dirs, Code formatting. Sensible defaults -- make [check=1] black
ifeq ($(is_venv),1)
	@$(VENV_BIN)/black $(check_text) src/
	$(VENV_BIN)/black $(check_text) tests/
endif

.PHONY: isort
isort:					## Code style --> sorts imports
ifeq ($(is_venv),1)
	@$(VENV_BIN)/isort src/
	$(VENV_BIN)/isort tests/
endif

.PHONY: flake
flake:					## Code style --> flake8 extreme style nitpikker
ifeq ($(is_venv),1)
	@$(VENV_BIN_PYTHON) -m flake8 src/
	$(VENV_BIN_PYTHON) -m flake8 tests/
endif

# --cov-report=xml
# Dependencies: pytest, pytest-cov, pytest-regressions
# make [v=1] coverage
.PHONY: coverage
coverage: private verbose_text = $(if $(v),"--verbose")
coverage:				## Run tests, generate coverage reports -- make [v=1] coverage
ifeq ($(is_venv),1)
	@$(VENV_BIN)/pytest --showlocals --cov=drain_swamp --cov-report=term-missing --cov-config=pyproject.toml $(verbose_text) tests
endif

##@ Kitting
# Initial build
# mkdir dist/ ||:; python -m build --outdir dist/ .
# pip install --disable-pip-version-check --no-color --find-links=file://///$HOME/Downloads/git_decimals/sphinx_external_toc_strict/dist sphinx-external-toc-strict

REPO_OWNER := msftcangoblowm/drain-swamp
REPO := $(REPO_OWNER)/drain_swamp

.PHONY: edit_for_release cheats relbranch kit_check kit_build kit_upload
.PHONY: test_upload kits_build kits_download github_releases

edit_for_release:               ## Edit sources to insert release facts (see howto.txt)
	python igor.py edit_for_release

cheats:                                 ## Create some useful snippets for releasing (see howto.txt)
	python igor.py cheats | tee cheats.txt

relbranch:                              ## Create the branch for releasing (see howto.txt)
	@git switch -c $(REPO_OWNER)/release-$$(date +%Y%m%d)

# Do not create a target(s) kit: or kits:
kit_check:                              ## Check that dist/* are well-formed
	python -m twine check dist/*
	@echo $$(ls -1 dist | wc -l) distribution kits

kit_build:                              ## Make the source distribution
	python igor.py build_next ""

kit_upload:                             ## Upload the built distributions to PyPI
	twine upload --verbose dist/*

test_upload:                    ## Upload the distributions to PyPI's testing server
	twine upload --verbose --repository testpypi --password $$TWINE_TEST_PASSWORD dist/*

kits_build:                             ## Trigger GitHub to build kits
	python ci/trigger_build_kits.py $(REPO_OWNER)

kits_download:                  ## Download the built kits from GitHub
	python ci/download_gha_artifacts.py $(REPO_OWNER) 'dist-*' dist

github_releases: $(DOCBIN)              ## Update GitHub releases.
	$(DOCBIN)/python -m scriv github-release --all

.PHONY: install
install: override usage := make [force=1]
install: override check_web := Install failed. Possible cause no web connection
install: private force_text = $(if $(force),"--force-reinstall")
install:				## Installs *as a package*, not *with the ui* -- make [force=1] [debug=1] install
ifeq ($(is_venv),1)
  ifeq ($(is_wheel), wheel)
	@if [[  "$$?" -eq 0 ]]; then

	whl=$(call find_whl,$(APP_NAME),,) #1: PYPI package name (hyphens). 2 folder/app name (APP_NAME;underscores). 3 file extension
	echo $(whl)
	$(VENV_BIN_PYTHON) -m pip install --disable-pip-version-check --no-color --log="/tmp/$(APP_NAME)_install_prod.log" $(force_text) "dist/$$whl"

	fi

  endif
endif

.PHONY: install-force
install-force: force := 1
install-force: install	## Force install even if exact same version
