.ONESHELL:
SHELL := /bin/bash

# Minimal makefile for Sphinx documentation
#

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

err_check_web_conn := Failed. Has issues or no web connection

# You can set these variables from the command line.
SPHINXOPTS    := -aE
SPHINXBUILDNOOPT := $(VENV_BIN)/sphinx-build
SPHINXBUILD   := $(SPHINXBUILDNOOPT) $(SPHINXOPTS) $(O)
SOURCEDIR     := .
BUILDDIR      := _build

##@ Build

# Convert *.txt --> *.inv Base folder only
# sphobjinv convert -q zlib objects-toc-strict.txt objects-toc-strict.inv
.PHONY: build_inv
build_inv:				## inventory base folder only .txt --> .inv
ifeq ($(is_venv),1)
	@while read f_path; do
	  if [[ -f "$${f_path}.txt" ]]; then
	    [[ ! -f "$${f_path}.inv" ]] && $(VENV_BIN)/sphobjinv convert -q zlib "$${f_path}.txt" "$${f_path}.inv" ||:
	  fi
	done < <(/bin/find $(SOURCEDIR) -maxdepth 1 -type f -name "*.txt" -exec basename {} .txt \;)
endif

.PHONY: inv2txt
inv2txt:				## .inv without .txt convert to .txt
inv2txt: | _inv2txt clean_inv

#  Revert *.inv --> .txt Base folder only. .inv without cooresponding .txt
.PHONY: _inv2txt
_inv2txt:
	@while read f_path; do
	  if [[ -f "$${f_path}.inv" ]] && [[ ! -f "$${f_path}.txt" ]]; then
	    $(VENV_BIN)/sphobjinv convert -q plain "$${f_path}.inv" "$${f_path}.txt" ||:
	  fi
	done < <(/bin/find $(SOURCEDIR) -maxdepth 1 -type f -name "*.inv" -exec basename {} .inv \;)

# clean .inv that have cooresponding .txt
.PHONY: clean_inv
clean_inv:				## remove .inv files that have cooresponding .txt file
	@while read f_path; do
	  if [[ -f "$${f_path}.txt" ]]; then
	    [[ -f "$${f_path}.inv" ]] && /bin/rm --preserve-root=all "$${f_path}.inv" ||:
	  fi
	done < <(/bin/find $(SOURCEDIR) -maxdepth 1 -type f -name "*.txt" -exec basename {} .txt \;)

.PHONY: html
html:				## Sphinx build html. Only whats been changed
ifeq ($(is_venv),1)
	@$(SPHINXBUILDNOOPT) -b html "$(SOURCEDIR)" "$(BUILDDIR)/html"
endif

.PHONY: htmlall
htmlall:				## Sphinx build clean and build html
ifeq ($(is_venv),1)
	@$(SPHINXBUILD) -b html "$(SOURCEDIR)" "$(BUILDDIR)/html"
endif

# @$(SPHINXBUILD) -b latexpdf "$(SOURCEDIR)" "$(BUILDDIR)/latex"
.PHONY: pdf
pdf:				## Sphinx build pdf
ifeq ($(is_venv),1)
	@$(SPHINXBUILDNOOPT) -M latexpdf "$(SOURCEDIR)" "$(BUILDDIR)"

endif

##@ Test

.PHONY: linkcheck
linkcheck:				## Sphinx check urls within docs and code base
ifeq ($(is_venv),1)
	@$(SPHINXBUILD) -b linkcheck "$(SOURCEDIR)" "$(BUILDDIR)" || echo "$(err_check_web_conn). exit code $$?"
endif

.PHONY: _objects
_objects:
ifeq ($(is_venv),1)
	@if [[ -n "$(project_name)" ]] && [[ -z "$(find)" ]]; then

	echo "$(usage)" 1>&2

	else

	if [[ ! -x $(VENV_BIN)/sphobjinv ]]; then
	echo "package sphobjinv not installed or available"
	else
	objinv=objects-$(project_name).inv
	/bin/yes | $(VENV_BIN)/sphobjinv suggest $(SOURCEDIR)/$$objinv "$(find)" -st 58
	fi

	fi
endif

# make objects_py find=logging.Logger
# $(VENV_BIN_PYTHON) -m sphinx.ext.intersphinx $(SOURCEDIR)/objects-python.inv
.PHONY: objects_py
objects_py: override project_name := python
objects_py: override usage := "make objects_py find=[dotted path]"
objects_py:	_objects		## Query python Sphinx objects. make objects_py find="[dotted path]"
objects_py:

# $(VENV_BIN_PYTHON) -m sphinx.ext.intersphinx $(SOURCEDIR)/objects-toc-strict.inv
# make objects_toc find=VERSION_FALLBACK
.PHONY: objects_toc
objects_toc: override project_name := sphinx-external-toc-strict
objects_toc: override usage := "make objects_toc find=[dotted path]"
objects_toc:	_objects	## Query toc Sphinx objects. make objects_toc find="[dotted path]"
objects_toc:

# make obj_strictyaml find=YAML
# make obj_strictyaml find=strictyaml.exceptions
.PHONY: obj_strictyaml
obj_strictyaml: override project_name := strictyaml
obj_strictyaml: override usage := "make obj_strictyaml find=[dotted path]"
obj_strictyaml:	_objects	## Query strictyaml Sphinx objects. make obj_strictyaml find="[dotted path]"
obj_strictyaml:

# make obj_pluggy find=pluggy.HookspecMarker
.PHONY: obj_pluggy
obj_pluggy: override project_name := pluggy
obj_pluggy: override usage := "make obj_pluggy find=[dotted path]"
obj_pluggy:	_objects	## Query pluggy Sphinx objects. make obj_pluggy find="[dotted path]"
obj_pluggy:

# Stubbornly insists on repeating on outdated files.
# -T show tracebacks on Exception
# -q quiet
# --keep-going even if there are warnings
# @$(MAKE) htmlall
.PHONY: doctest
doctest:				## Confirm in-doc code does what it claims
ifeq ($(is_venv),1)
	@$(SPHINXBUILD) -b doctest "$(SOURCEDIR)" "$(BUILDDIR)"
endif

##@ View

.PHONY: pdf-view
pdf-view:				## Open in pdf viewier
	@DESKTOP_DIR=/usr/share/applications
	pdf_viewer=$$(/bin/xdg-mime query default application/pdf)
	if [[ "$$pdf_viewer" = "gimp.desktop" && -f $$DESKTOP_DIR/org.gnome.Evince.desktop ]]; then
	/bin/xdg-mime default org.gnome.Evince.desktop application/pdf
	fi
	while read f_path; do
	abspath_pdf=$$f_path
	done < <(/bin/find $(CURDIR)/_build/latex -maxdepth 1 -type f -name "*.pdf" -print)

	if [[ -x "/bin/xdg-open" ]] && [[ -f "$${abspath_pdf}" ]]; then
	/bin/xdg-open $$abspath_pdf
	fi

.PHONY: html-view
html-view:				## Open in web browser
	@arr=("index" "intro")
	for master_doc in $${arr[@]}; do
	abspath_html=$(CURDIR)/_build/html/$$master_doc.html
	if [[ -x "/bin/xdg-open" ]] && [[ -f "$$abspath_html" ]]; then
	/bin/xdg-open $$abspath_html
	fi
	done

##@ Misc

# Put it first so that "make" without argument is like "make help".
.PHONY: sphinx_help
sphinx_help:			## sphinx-build --help
ifeq ($(is_venv),1)
	@$(SPHINXBUILD) --help "$(SOURCEDIR)" "$(BUILDDIR)"
endif

# Original
# https://www.thapaliya.com/en/writings/well-documented-makefiles/
# coverage adaptation (https://github.com/nedbat/coveragepy/commits?author=nedbat)
# https://github.com/nedbat/coveragepy/blob/5124586e92da3e69429002b2266ce41898b953a1/Makefile
.PHONY: help
help:				## (Default) Display this help -- Always up to date
	@awk -F ':.*##' '/^[^: ]+:.*##/{printf "  \033[1m%-20s\033[m %s\n",$$1,$$2} /^##@/{printf "\n%s\n",substr($$0,5)}' $(MAKEFILE_LIST)
	#@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
.PHONY: Makefile
%: Makefile				## Catch all target
ifeq ($(is_venv),1)
	@$(SPHINXBUILD) -b $@ "$(SOURCEDIR)" "$(BUILDDIR)"
endif
