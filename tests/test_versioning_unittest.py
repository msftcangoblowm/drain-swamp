"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

Unittest for dealing with scm version str

"""

import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

from drain_swamp.constants import g_app_name
from drain_swamp.version_semantic import (
    SemVersion,
    Version,
    _current_tag,
    _current_version,
    _get_app_name,
    _map_release,
    _remove_v,
    get_version,
    sanitize_tag,
)

testdata_v = (
    ("v1.0.1", "1.0.1"),
    ("0!v1.0.1", "0!1.0.1"),
    ("1!v1.0.1", "1!1.0.1"),
    ("0!v1.0.1+g4b33a80.d20240129", "0!1.0.1+g4b33a80.d20240129"),
    ("1!v1.0.1+g4b33a80.d20240129", "1!1.0.1+g4b33a80.d20240129"),
    ("v0.1.1.dev0+g4b33a80.d20240129", "0.1.1.dev0+g4b33a80.d20240129"),
    ("v0.1.1.post0+g4b33a80.d20240129", "0.1.1.post0+g4b33a80.d20240129"),
    ("v0.1.1.a1dev1+g4b33a80.d20240129", "0.1.1.a1dev1+g4b33a80.d20240129"),
    ("v0.1.1.alpha1dev1+g4b33a80.d20240129", "0.1.1.alpha1dev1+g4b33a80.d20240129"),
    ("v0.1.1.b1dev1+g4b33a80.d20240129", "0.1.1.b1dev1+g4b33a80.d20240129"),
    ("v0.1.1.beta1dev1+g4b33a80.d20240129", "0.1.1.beta1dev1+g4b33a80.d20240129"),
    ("v0.1.1.rc1dev1+g4b33a80.d20240129", "0.1.1.rc1dev1+g4b33a80.d20240129"),
)

testdata_valids = (
    ("0.0.1", "0.0.1", "0-0-1"),  # tagged final version
    ("0.1.1.dev0+g4b33a80.d20240129", "0.1.1.dev0", "0-1-1"),
    ("0.1.1.dev1+g4b33a80.d20240129", "0.1.1.dev1", "0-1-1"),
    ("0.1.1.post0+g4b33a80.d20240129", "0.1.1.post0", "0-1-1post0"),
    ("0.1.1.a1dev1+g4b33a80.d20240129", "0.1.1a1.dev1", "0-1-1a1"),
    ("0.1.1.alpha1dev1+g4b33a80.d20240129", "0.1.1a1.dev1", "0-1-1a1"),
    ("0.1.1.b1dev1+g4b33a80.d20240129", "0.1.1b1.dev1", "0-1-1b1"),
    ("0.1.1.beta1dev1+g4b33a80.d20240129", "0.1.1b1.dev1", "0-1-1b1"),
    ("0.1.1.rc1dev1+g4b33a80.d20240129", "0.1.1rc1.dev1", "0-1-1rc1"),
)

testdata_invalids = (("0.1.dev0.d20240213", "0.1.1.dev0"),)

# long|short form --> long form
testdata_releaselevel = (
    ("candidate", "candidate"),
    ("rc", "candidate"),
    ("post", "post"),
    ("a", "alpha"),
    ("alpha", "alpha"),
    ("b", "beta"),
    ("beta", "beta"),
)


class PackageVersioning(unittest.TestCase):
    """Working with version str."""

    def setUp(self):
        """Setup testdata, vals."""
        self.vals = (
            (
                (0, 0, 1),
                {"releaselevel": "alpha", "serial": 0, "dev": None},
                "0.0.1a0",
            ),
            (
                (0, 0, 1),
                {"releaselevel": "beta", "serial": 0, "dev": None},
                "0.0.1b0",
            ),
            (
                (0, 0, 1),
                {"releaselevel": "candidate", "serial": 0, "dev": None},
                "0.0.1rc0",
            ),
            (
                (0, 0, 1),
                {"releaselevel": "rc", "serial": 0, "dev": None},
                "0.0.1rc0",
            ),
            (
                (0, 0, 1),
                {"releaselevel": "", "serial": 0, "dev": None},
                "0.0.1",
            ),
            (
                (0, 0, 1),
                {"releaselevel": "alpha", "serial": 3, "dev": 10},
                "0.0.1a3.dev10",
            ),
            (
                (0, 0, 1),
                {"releaselevel": "post", "serial": 3, "dev": None},
                "0.0.1post3",
            ),
        )

    def test_setuptools_scm_version_file(self):
        """Autogenerated file by setuptools-scm."""
        valids = (
            ((0, 5, 2), "0.5.2"),
            ((0, 5, 2, "dev0"), "0.5.2.dev0"),
            ((0, 5, 2, "dev0", "g1234567.d20240101"), "0.5.2.dev0+g1234567.d20240101"),
        )
        for t_ver, ver_expected in valids:
            ver = list(t_ver[:3])
            ver_short = ".".join(map(str, ver))
            if len(t_ver) == 3:
                # 0.0.1
                ver_long = ver_short
                ver_actual = ver_long
            elif len(t_ver) in [4, 5]:
                # __version_tuple__
                # 0.0.1.a1dev8
                ver_dev = t_ver[3]
                ver_long = ver_short
                if len(ver_dev) != 0:
                    ver_long += f".{ver_dev}"

                if len(t_ver) == 4:
                    ver_actual = ver_long
                else:
                    ver_git = t_ver[-1]
                    ver_actual = f"{ver_long}+{ver_git}"

            self.assertEqual(ver_actual, ver_expected)

    def test_sanitize_tag(self):
        """Convert repo version --> semantic version."""
        for v_in, v_expected, anchor in testdata_valids:
            v_actual, _ = sanitize_tag(v_in)
            self.assertEqual(v_actual, v_expected)

        # sanitize_tag and get_version both should fail
        for v_in, v_expected in testdata_invalids:
            with self.assertRaises(ValueError):
                sanitize_tag(v_in)

        for v_in, v_expected in testdata_invalids:
            with self.assertRaises(ValueError):
                get_version(v_in, is_use_final=True)

        # Strip epoch and locals
        valids = (
            ("1!1.0.1a1.dev1", "1.0.1a1.dev1"),
            ("1.0.1a1.dev1+4b33a80.4b33a80", "1.0.1a1.dev1"),
            ("1.0.1.alpha1.dev1+4b33a80.4b33a80", "1.0.1a1.dev1"),
            ("1.2.3rc1.post0.dev9+g4b33a80.d20241212", "1.2.3rc1.post0.dev9"),
        )
        for orig, expected in valids:
            actual, _ = sanitize_tag(orig)
            self.assertEqual(actual, expected)

    def test_get_version_normal(self):
        """Used for display only. Allows release level, final."""
        # Flip the logic backwards
        finals = (
            None,
            0.12345,  # unsupported type
            False,
        )
        for final in finals:
            for args, kwargs, actual in self.vals:
                # compensate for ``candidate`` being invalid semantic version component
                if kwargs["releaselevel"] == "candidate":
                    releaselevel_in = "rc"
                else:
                    releaselevel_in = kwargs["releaselevel"]

                expect_info, expect_dev = get_version(
                    actual,
                    is_use_final=final,
                )
                self.assertEqual(args, expect_info[:3])
                self.assertEqual(kwargs["dev"], expect_dev)
                self.assertEqual(kwargs["serial"], expect_info[-1])

                if len(releaselevel_in) == 0:
                    self.assertEqual(len(expect_info[-2]), 0)
                else:
                    # has pre-release component
                    self.assertEqual(releaselevel_in, expect_info[-2])

        # Allow final
        actual = "1.0.1"
        l_actual = actual.split(".")
        l_actual2 = map(int, iter(l_actual))
        t_actual = tuple(l_actual2)
        expect_info, expect_dev = get_version(
            actual,
            is_use_final=True,
        )
        self.assertIsNone(expect_dev)
        self.assertEqual(0, expect_info[-1])
        self.assertEqual("final", expect_info[-2])
        self.assertEqual(t_actual, expect_info[:3])

        # Has both dev and is a prerelease
        dev_pres = (
            ("0.1.1.a1dev1+g4b33a80.d20240129", "0.1.1a1.dev1"),
            ("0.1.1.alpha1dev1+g4b33a80.d20240129", "0.1.1a1.dev1"),
            ("0.1.1.b1dev1+g4b33a80.d20240129", "0.1.1b1.dev1"),
            ("0.1.1.beta1dev1+g4b33a80.d20240129", "0.1.1b1.dev1"),
            ("0.1.1.rc1dev1+g4b33a80.d20240129", "0.1.1rc1.dev1"),
            ("0.1.1.candidate1dev1+g4b33a80.d20240129", "0.1.1rc1.dev1"),
        )

        for dev_pre in dev_pres:
            expected, _ = sanitize_tag(dev_pre[1])
            expect_info, expect_dev = get_version(expected)

            v = Version(expected)

            v_pre = v.pre
            v_pre_is = v.is_prerelease
            v_dev = v.dev
            self.assertEqual(expect_dev, v_dev)

            pre = expect_info[-2]
            if pre == "rc":
                # ``rc`` long format is invalid semantic version str
                self.assertIn(pre, _map_release.values())
            else:
                self.assertIn(pre, _map_release.keys())

                found_k = None
                for k, v in _map_release.items():
                    if pre == k and pre != "rc":
                        found_k = k
                self.assertIsNotNone(found_k)
                # pre is long format. So ``alpha`` rather than ``a``
                self.assertEqual(pre, found_k)

        # Has dev and no releaselevel
        dev_pres = (
            ("0.1.1.a1dev1+g4b33a80.d20240129", "0.1.1.dev1"),
            ("0.1.1.alpha1dev1+g4b33a80.d20240129", "0.1.1.dev0"),
            ("0.1.1.b1dev1+g4b33a80.d20240129", "0.1.1dev8"),
        )
        for dev_pre in dev_pres:
            expected, _ = sanitize_tag(dev_pre[1])
            v = Version(expected)

            v_pre = v.pre
            v_pre_is = v.is_prerelease
            v_dev = v.dev

            expect_info, expect_dev = get_version(expected)

            self.assertEqual(expect_dev, v_dev)
            self.assertIsNone(v_pre)

        # post only
        dev_pres = (
            ("0.1.1.post0+g4b33a80.d20240129", "0.1.1.post0", 0, False),
            ("0.1.1.post8", "0.1.1.post8", 8, False),
            ("0.1.1.post5", "0.1.1post5", 5, False),
            ("1.4.0.post1.dev0", "1.4.0.post1.dev0", 1, True),
        )
        for t_ver in dev_pres:
            is_pre = t_ver[3]
            expected_post = t_ver[2]
            expected, _ = sanitize_tag(t_ver[0])

            v = Version(expected)
            v_post = v.post
            v_post_is = v.is_postrelease
            v_pre_is = v.is_prerelease
            self.assertTrue(v_post_is)
            self.assertEqual(v_pre_is, is_pre)

            t_expect_info, expect_dev = get_version(expected)
            self.assertEqual(v_post, expected_post)
            self.assertEqual(t_expect_info[-2], "post")

        # edge cases
        dev_edges = (
            ("1.2.3rc1.post0.dev9", "1.2.3rc1.post0.dev9", 0),  # pre not stored!
            ("1.2.3.rc1.post0.dev9", "1.2.3rc1.post0.dev9", 0),  # pre not stored!
        )
        for t_ver in dev_edges:
            expected_post = t_ver[2]
            ver_expected, _ = sanitize_tag(t_ver[1])

            v = Version(ver_expected)
            v_pre = v.pre
            v_post_is = v.is_postrelease
            v_pre_is = v.is_prerelease
            self.assertTrue(v_post_is)
            self.assertTrue(v_pre_is)

            t_expect_info, expect_dev = get_version(ver_expected)

            # preserve pre. post is not preserved
            # candidate --> rc. candidate is not valid semantic version str component
            pre_actual_long = t_expect_info[-2]
            pre_serial_actual = t_expect_info[-1]

            self.assertEqual(pre_actual_long, "rc")
            self.assertEqual(pre_serial_actual, v_pre[1])

    def test_get_version_edge_cases(self):
        """coverage not picking up the edge cases."""
        testdata_get_version = (
            ("1.4.0.post1.dev0", 0, 1),
            ("1.2.3rc1.post0.dev9", 9, 1),
        )
        for edge_case, dev_expected, serial_expected in testdata_get_version:
            t_expect_info, dev_actual = get_version(edge_case)
            serial_actual = t_expect_info[-1]
            self.assertEqual(dev_actual, dev_expected)
            self.assertEqual(serial_actual, serial_expected)

    def test_v_remove(self):
        """Remove epoch and local and v prefix from semantic version str."""
        for v_in, expected in testdata_v:
            actual = _remove_v(v_in)
            self.assertEqual(actual, expected)


class SemVersioning(unittest.TestCase):
    """Class tests tag version (from version file) and current scm version."""

    def setUp(self):
        """Setup cwd and this test folder path."""
        if "__pycache__" in __file__:
            # cached
            self.path_tests = Path(__file__).parent.parent
        else:
            # not cached
            self.path_tests = Path(__file__).parent
        self.cwd = self.path_tests.parent

    def test_current_tag(self):
        """If not tagged version at all will be None."""
        cmd = []
        with patch(
            "subprocess.run",
            side_effect=subprocess.CalledProcessError(128, cmd),
        ):
            actual = _current_tag(path=self.cwd)
            self.assertIsNone(actual)

        # simulate git saying, no tagged versions yet
        with patch(
            "subprocess.run",
            return_value=subprocess.CompletedProcess(
                cmd,
                returncode=128,
                stderr="fatal: No names found, cannot describe anything.",
            ),
        ):
            actual = _current_tag(path=self.cwd)
            self.assertIsNone(actual)

        # Successful call
        expected = "0.0.1"
        with (
            patch(
                "subprocess.run",
                return_value=subprocess.CompletedProcess(
                    cmd,
                    returncode=0,
                    stdout=expected,
                ),
            ),
        ):
            actual = _current_tag(path=self.cwd)
            self.assertIsInstance(actual, str)
            self.assertEqual(actual, expected)

    def test_current_version(self):
        """setuptools-scm retrieves development version from git.

        Without epoch, local, or prepended v.
        """
        # setuptools-scm is not installed.
        #    Current version is obtained from package setuptools-scm
        with patch(
            f"{g_app_name}.version_semantic.is_package_installed",
            return_value=False,
        ):
            actual = _current_version(path=self.cwd)
            self.assertIsNone(actual)

        cmd = []
        with patch(
            "subprocess.run",
            side_effect=subprocess.CalledProcessError(128, cmd),
        ):
            actual = _current_version(path=self.cwd)
            self.assertIsNone(actual)

        with patch(
            "subprocess.run",
            return_value=subprocess.CompletedProcess(
                cmd,
                returncode=128,
                stdout="",
            ),
        ):
            actual = _current_version(path=self.cwd)
            self.assertIsNone(actual)

        # Successful call
        expected = "0.0.1"
        with (
            patch(
                "subprocess.run",
                return_value=subprocess.CompletedProcess(
                    cmd,
                    returncode=0,
                    stdout=expected,
                ),
            ),
        ):
            actual = _current_version(path=self.cwd)
            self.assertIsInstance(actual, str)
            self.assertEqual(actual, expected)

    def test_semversion_properties(self):
        """Parse and check SemVersion properties."""
        sv = SemVersion()
        for v_in, expected in testdata_v:
            sv.parse_ver(v_in)
            self.assertIsInstance(sv.major, int)
            self.assertIsInstance(sv.minor, int)
            self.assertIsInstance(sv.micro, int)
            self.assertIsInstance(sv.releaselevel, str)
            self.assertIsInstance(sv.serial, int)
            if sv.dev is None:
                self.assertIsNone(sv.dev)
            else:
                self.assertIsInstance(sv.dev, int)

        # path_cwd setter
        path_dir = self.cwd
        path_pyproject_toml = path_dir / "pyproject.toml"
        with self.assertRaises(NotADirectoryError):
            SemVersion(path=path_pyproject_toml)

        # is_use_final setter
        invalids = (
            None,
            1.2345,
            "",
        )
        for invalid in invalids:
            sv.is_use_final = True
            sv.is_use_final = invalid
            self.assertFalse(sv.is_use_final)

    def test_semversion_parse_ver(self):
        """SemVersion now stores version local."""
        sv = SemVersion()
        locals_ = (
            (None, None),  # empty string or None
            ("", None),  # empty string or None
            ("    ", None),  # empty string or None
            ("+g2988c13e.d20240101", None),  # a local
            (1.12345, None),  # unsupported
        )
        for local, expected in locals_:
            for v_in, expected in testdata_v:
                sv.parse_ver(v_in, local=local)
                sv._local = expected

    def test_readthedocs_package_name(self):
        """rtd url just because."""
        project_name = g_app_name.replace("_", "-")
        sv = SemVersion()

        # parse_ver never called. ver None --> latest
        is_latests = (
            None,
            "latest",
            1.2345,
        )
        for is_latest in is_latests:
            str_url = sv.readthedocs_url(project_name, is_latest=is_latest)
            self.assertTrue(str_url.endswith("latest"))
            protocol_len = len("https://")
            uri = str_url[protocol_len:]
            project_name_actual = uri.split(".")[0]
            self.assertNotIn("_", project_name_actual)

        # package_name contains hyphens. Gets converted to underscores
        str_url = sv.readthedocs_url(g_app_name)
        protocol_len = len("https://")
        uri = str_url[protocol_len:]
        project_name_actual = uri.split(".")[0]
        self.assertEqual(project_name_actual, project_name)

        for v_in, v_expected, anchor in testdata_valids:
            # clean up semantic version str
            v_actual, _ = sanitize_tag(v_in)
            self.assertEqual(v_actual, v_expected)

            #    parse_ver not called yet
            sv = SemVersion()
            self.assertIsNone(sv.version_xyz())
            self.assertIsNone(sv.anchor())

            sv.parse_ver(v_in)

            self.assertEqual(anchor, sv.anchor())

            # Contains xyz, not pre or post or rc releases
            actual_url = sv.readthedocs_url(
                project_name,
                is_latest=False,
            )
            ver_xyz = sv.version_xyz()
            self.assertTrue(actual_url.endswith(ver_xyz))

            # Force get latest URL; parse_ver previously called
            str_url = sv.readthedocs_url(project_name, is_latest=True)
            self.assertTrue(str_url.endswith("latest"))

    def test_version_clean(self):
        """version_clean can take kind: current, now, tag, version str."""

        # Specify version explicitly. To transition to pre or post or rc ...
        #    Sanitizes version str
        kind = "0.0.1"  # use this instead of from git
        sv = SemVersion(path=self.cwd)
        actual_ver = sv.version_clean(kind)
        self.assertEqual(actual_ver, kind)
        self.assertEqual(actual_ver, sv.__version__)

        # invalid explicit version str
        # nowhere boys (aussie series vs some ancient power ranger like cartoon)
        kind = "five element spirit or nature?"
        with self.assertRaises(ValueError):
            sanitize_tag(kind)

        with self.assertRaises(ValueError):
            sv.version_clean(kind)

        """tag --> 0.0.1
        Avoid changing _version.py"""
        kind = "tag"
        expected = "0.0.1"
        #    Avoid changing _version.py
        with (
            patch(f"{g_app_name}.version_semantic._tag_version", return_value="0.0.1"),
        ):
            actual = sv.version_clean(kind)
            self.assertEqual(actual, expected)

        """tag. No tagged, so get current. Current found.
        Avoid changing _version.py"""
        #    Avoid changing _version.py
        with (
            patch(f"{g_app_name}.version_semantic._tag_version", return_value=None),
            patch(
                f"{g_app_name}.version_semantic._current_version", return_value=expected
            ),
        ):
            actual_ver = sv.version_clean(kind)
            self.assertEqual(actual, expected)

        """tag. Both return None; no commits at all.
        Avoid changing _version.py
        """
        kind = "tag"
        sane_fallback = "0.0.1"
        with (
            patch(f"{g_app_name}.version_semantic._tag_version", return_value=None),
            patch(
                f"{g_app_name}.version_semantic._current_version",
                return_value=sane_fallback,
            ),
        ):
            actual_ver = sv.version_clean(kind)
            self.assertEqual(actual_ver, sane_fallback)

        # current aliases. git uninitialized --> sane fallback "0.0.1"
        kinds = (
            "current",
            "now",
        )
        for kind in kinds:
            #    Avoid changing _version.py
            with (
                patch(
                    f"{g_app_name}.version_semantic._current_version",
                    return_value=sane_fallback,
                ),
            ):
                actual_ver = sv.version_clean(kind)
                self.assertEqual(actual_ver, sane_fallback)

    def test_get_app_name(self):
        """Grabs app project basename from git."""
        expected = g_app_name
        actual = _get_app_name(path=self.cwd)
        self.assertEqual(actual, expected)

        """Unlikely to ever occur. Bigger risk would be if the package
        base name is not the same as g_app_name"""
        cmd = []
        with patch(
            "subprocess.run",
            side_effect=subprocess.CalledProcessError(128, cmd),
        ):
            actual = _get_app_name(path=self.cwd)
            self.assertIsNone(actual)

        # returns nothing. Not a possibility but hardened against this
        with patch(
            "subprocess.run",
            return_value=subprocess.CompletedProcess(
                cmd,
                returncode=0,
                stdout="",
            ),
        ):
            actual = _get_app_name(path=self.cwd)
            self.assertIsNone(actual)

    def test_sanitize_kind(self):
        """Can provide a version str or get latest tag or current dev version."""
        to_tags = (
            None,
            "tag",
            (1.2345,),  # accidental tuple, but unsupported type
            1.2345,  # unsupported type
        )
        for kind in to_tags:
            actual = SemVersion.sanitize_kind(kind)
            self.assertEqual(actual, "tag")

        sames = (
            "0.0.1",
            "current",
        )
        for kind in sames:
            actual = SemVersion.sanitize_kind(kind)
            self.assertEqual(actual, kind)

        # accidental tuple
        kind = ("0.0.1",)
        actual = SemVersion.sanitize_kind(kind)
        self.assertEqual(actual, "0.0.1")

        # now is an alias of current
        kind = "now"
        actual = SemVersion.sanitize_kind(kind)
        self.assertEqual(actual, "current")

    def test_releaselevel(self):
        """releaselevel setter/getter. Ensures long form."""
        sv = SemVersion()
        for short_long, long in testdata_releaselevel:
            sv.releaselevel = short_long
            self.assertEqual(sv.releaselevel, long)

    def test_as_tuple(self):
        """Test version tuple."""
        testdata_ = (
            (
                "v0.1.1.dev0+g4b33a80.d20240129",
                (0, 1, 1, "dev0", "g4b33a80.d20240129"),
            ),
            (
                "v0.1.1.dev0",
                (0, 1, 1, "dev0"),
            ),
            (
                "v0.1.1",
                (0, 1, 1),
            ),
            ("v0.1.1.post0+g4b33a80.d20240129", (0, 1, 1, "g4b33a80.d20240129")),
        )
        for ver, t_ver_expected in testdata_:
            t_ver_actual = SemVersion.as_tuple(ver)
            self.assertEqual(t_ver_actual, t_ver_expected)

        # Version(ver_bad) --> ValueError --> (ver_bad,)
        ver_bad = "0.1.dev0.d20240213"
        t_ver = SemVersion.as_tuple(ver_bad)
        ver_actual = t_ver[0]
        self.assertEqual(ver_actual, ver_bad)


if __name__ == "__main__":  # pragma: no cover
    """Test commands so don't have to remember cli command syntax.

    w/o coverage

    .. code-block:: shell

       python -m unittest tests.test_versioning_unittest --locals

       python -m unittest tests.test_versioning_unittest \
       -k PackageVersioning.test_get_version_normal --locals --buffer

       python -m unittest tests.test_versioning_unittest \
       -k PackageVersioning.test_get_version_edge_cases --locals --buffer

       python -m unittest tests.test_versioning_unittest \
       -k PackageVersioning.test_sanitize_tag --locals --buffer

    W/ coverage

    .. code-block:: shell

       coverage run --data-file=".coverage-combine-31" \
       -m unittest discover -t. -s tests -p "test_versioning_unittest*.py" --locals

       coverage report --data-file=".coverage-combine-31" --no-skip-covered \
       --include="**/drain_swamp/constants*"

       coverage report --data-file=".coverage-combine-31" --no-skip-covered \
       --include="**/drain_swamp/*_version*"

    """
    unittest.main(tb_locals=True)
