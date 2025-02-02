import re
import sys
from pathlib import Path

from packaging.version import parse
from sphinx_pyproject import SphinxConfig
from wreck.pep518_read import find_project_root

path_docs = Path(__file__).parent
path_package_base = path_docs.parent
sys.path.insert(0, str(path_package_base))  # Needed ??

# @@@ editable
copyright = "2024–2025, Dave Faulkmore"
# The short X.Y.Z version.
version = "2.1.1"
# The full version, including alpha/beta/rc tags.
release = "2.1.1"
# The date of release, in "monthname day, year" format.
release_date = "January 7, 2025"
# @@@ end

v = parse(release)
version_short = f"{v.major}.{v.minor}"
# version_xyz = f"{v.major}.{v.minor}.{v.micro}"
version_xyz = version

# pyproject.toml search algo. Credit/Source: https://pypi.org/project/black/
srcs = (path_package_base,)
t_root = find_project_root(srcs)

try:
    from drain_swamp.constants_maybe import __version__ as version_semantic_full
except ImportError:
    # set during each tagged release
    version_long = version_xyz
else:
    # version file is generated during python -m build --sdist
    version_long = version_semantic_full

config = SphinxConfig(
    # Path(__file__).parent.parent.joinpath("pyproject.toml"),
    t_root[0] / "pyproject.toml",
    globalns=globals(),
    config_overrides={"version": version_long},
)

# This project is a fork from "Sphinx External ToC"
proj_project = config.name
proj_description = config.description
proj_authors = config.author

slug = re.sub(r"\W+", "-", proj_project.lower())
proj_master_doc = config.get("master_doc")
project = f"{proj_project} {version_xyz}"

###############
# Dynamic
###############
rst_epilog = """
.. |project_name| replace:: {slug}
.. |package-equals-release| replace:: drain_swamp=={release}
.. |author-contact| replace:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>
""".format(
    release=release, slug=slug
)

html_theme_options = {
    "description": proj_description,
    "show_relbars": True,
    "logo_name": False,
    "logo": "snip-logo.svg",
    "show_powered_by": False,
}

latex_documents = [
    (
        proj_master_doc,
        f"{slug}.tex",
        f"{proj_project} Documentation",
        proj_authors,
        "manual",  # manual, howto, jreport (Japanese)
        True,
    )
]
man_pages = [
    (
        proj_master_doc,
        slug,
        f"{proj_project} Documentation",
        [proj_authors],
        1,
    )
]
texinfo_documents = [
    (
        proj_master_doc,
        slug,
        f"{proj_project} Documentation",
        proj_authors,
        slug,
        proj_description,
        "Miscellaneous",
    )
]

#################
# Static
#################
ADDITIONAL_PREAMBLE = r"""
\DeclareUnicodeCharacter{20BF}{\'k}
"""

latex_elements = {
    "sphinxsetup": "verbatimforcewraps",
    "extraclassoptions": "openany,oneside",
    "preamble": ADDITIONAL_PREAMBLE,
}

html_sidebars = {
    "**": [
        "about.html",
        "searchbox.html",
        "navigation.html",
        "relations.html",
    ],
}

intersphinx_mapping = {
    "python": (  # source https://docs.python.org/3/objects.inv
        "https://docs.python.org/3",
        ("objects-python.inv", None),
    ),
    "snip": (
        "https://drain-swamp.readthedocs.io/en/stable",
        ("objects-snip.inv", "objects-snip.txt"),
    ),
    "gh-black": (
        "https://github.com/psf/black",
        ("objects-gh-black.inv", "objects-gh-black.txt"),
    ),
    "python-missing": (
        "https://github.com/python/cpython/blob",
        ("objects-python-missing.inv", "objects-python-missing.txt"),
    ),
    "setuptools-scm": (
        "https://setuptools-scm.readthedocs.io/en/stable",
        ("objects-setuptools-scm.inv", "objects-setuptools-scm.txt"),
    ),
    "packaging": (
        "https://packaging.pypa.io/en/stable",
        ("objects-packaging.inv", "objects-packaging.txt"),
    ),
    "pluggy": (
        "https://pluggy.readthedocs.io/en/stable",
        ("objects-pluggy.inv", "objects-pluggy.txt"),
    ),
    "setuptools": (
        "https://setuptools.pypa.io/en/stable",
        ("objects-setuptools.inv", "objects-setuptools.txt"),
    ),
    "gh-setuptools": (
        "https://github.com/pypa/setuptools",
        ("objects-gh-setuptools.inv", "objects-gh-setuptools.txt"),
    ),
    "dss": (
        "https://drain-swamp-snippet.readthedocs.io/en/stable",
        ("objects-dss.inv", "objects-dss.txt"),
    ),
    "gh-dsa": (
        "https://github.com/msftcangoblowm/drain-swamp-action",
        ("objects-gh-dsa.inv", "objects-gh-dsa.txt"),
    ),
    "gh-ds": (
        "https://github.com/msftcangoblowm/drain-swamp",
        ("objects-gh-ds.inv", "objects-gh-ds.txt"),
    ),
    "gh-setuptools-scm": (
        "https://github.com/pypa/setuptools-scm",
        ("objects-gh-setuptools-scm.inv", "objects-gh-setuptools-scm.txt"),
    ),
}
intersphinx_disabled_reftypes = ["std:doc"]
autodoc_type_aliases = {
    "TOML_RESULT": "drain_swamp.monkey.pyproject_reading.TOML_RESULT",
    "TOML_LOADER": "drain_swamp.monkey.pyproject_reading.TOML_LOADER",
    "_T": "drain_swamp.lock_inspect._T",
    "DATUM": "drain_swamp.lock_datum.DATUM",
    "DatumByPkg": "drain_swamp.lock_datum.DatumByPkg",
    "PinsByPkg": "drain_swamp.lock_inspect.PinsByPkg",
    "PkgsWithIssues": "drain_swamp.lock_discrepancy.PkgsWithIssues",
    "T_REQUIRED": "drain_swamp.snippet_dependencies.T_REQUIRED",
    "T_OPTIONALS": "drain_swamp.snippet_dependencies.T_OPTIONALS",
}

extlinks = {
    "pypi_org": (  # url to: aiologger
        "https://pypi.org/project/%s",
        "%s",
    ),
}

# spoof user agent to prevent broken links
# curl -A "Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:24.0) Gecko/20100101 Firefox/24.0" --head "https://github.com/python/cpython/blob/3.12/Lib/unittest/case.py#L193"
linkcheck_request_headers = {
    "https://github.com/": {
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:24.0) Gecko/20100101 Firefox/24.0",
    },
    "https://docs.github.com/": {
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:24.0) Gecko/20100101 Firefox/24.0",
    },
}

# Ignore unfixable WARNINGS
# in pyproject.toml --> nitpicky = true
# in conf.py --> nitpicky = True
nitpick_ignore = [
    ("py:class", "ValidatorType"),
]

favicons = [
    {"rel": "icon", "href": "icon-drain-swamp-200x200.svg", "type": "image/svg+xml"},
    {
        "rel": "apple-touch-icon",
        "sizes": "180x180",
        "href": "apple-touch-icon-180x180.png",
        "type": "image/png",
    },
]
