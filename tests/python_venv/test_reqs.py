"""Provide unit tests for `~python_venv.reqs`:py:mod:."""

import unittest

import parameterized  # https://pypi.org/project/parameterized/

from python_venv import exceptions, reqs

########################################
# Tests


class TestRequirements(unittest.TestCase):
    def setUp(self):
        self.saved_requirements = reqs.REQUIREMENTS

    def tearDown(self):
        reqs.REQUIREMENTS = self.saved_requirements

    def test_PV_RQ_000_symbols_exist(self):
        _ = reqs.REQUIREMENTS_VENV
        _ = reqs.REQUIREMENTS_PLAIN
        _ = reqs.REQUIREMENTS_DEV
        _ = reqs.REQUIREMENTS_TEST
        _ = reqs.REQUIREMENTS_FROZEN
        _ = reqs.REQUIREMENTS_BUILD
        _ = reqs.REQUIREMENTS_PACKAGE
        _ = reqs.REQUIREMENTS_SOURCE
        _ = reqs.REQ_SCHEME_PLAIN
        _ = reqs.REQ_SCHEME_DEV
        _ = reqs.REQ_SCHEME_FROZEN
        _ = reqs.REQ_SCHEME_PACKAGE
        _ = reqs.REQ_SCHEME_SOURCE
        _ = reqs.DEV_REQ_SCHEMES
        _ = reqs.ALL_REQ_SCHEMES

    @parameterized.parameterized.expand(
        [
            ("req_scheme_plain", reqs.REQ_SCHEME_PLAIN, "plain"),
            ("req_scheme_dev", reqs.REQ_SCHEME_DEV, "dev"),
            ("req_scheme_frozen", reqs.REQ_SCHEME_FROZEN, "frozen"),
            ("req_scheme_package", reqs.REQ_SCHEME_PACKAGE, "package"),
            ("req_scheme_source", reqs.REQ_SCHEME_SOURCE, "source"),
        ]
    )
    def test_PV_RQ_001_symbol_interfaces(self, name, symbol, expected):
        self.assertEqual(symbol, expected)

    @parameterized.parameterized.expand(
        [
            ("dev_req_schemes", reqs.DEV_REQ_SCHEMES),
            ("all_req_schemes", reqs.ALL_REQ_SCHEMES),
        ]
    )
    def test_PV_RQ_002_symbol_groups(self, name, group):
        self.assertGreater(len(group), 0)

    def test_PV_RQ_010_is_dev_req_scheme(self):
        self.assertTrue(reqs.is_dev_req_scheme(reqs.REQ_SCHEME_DEV))
        self.assertFalse(reqs.is_dev_req_scheme(reqs.REQ_SCHEME_PLAIN))
        self.assertFalse(reqs.is_dev_req_scheme(None))

    def test_PV_RQ_020_requirements_for_venv(self):
        self.assertEqual(reqs.requirements_for_venv(), reqs.REQUIREMENTS_VENV)

    @parameterized.parameterized.expand(
        [
            ("plain", reqs.REQ_SCHEME_PLAIN),
            ("dev", reqs.REQ_SCHEME_DEV),
            ("frozen", reqs.REQ_SCHEME_FROZEN),
            ("package", reqs.REQ_SCHEME_PACKAGE),
            ("source", reqs.REQ_SCHEME_SOURCE),
        ]
    )
    def test_PV_RQ_030_requirements_sources_for_scheme(self, name, scheme):
        _ = reqs.requirements_sources_for_scheme(scheme)

    @parameterized.parameterized.expand(
        [
            ("empty_requirements", {}, set("dummy"), False),
            ("empty_whence", {"dummy_key": "dummy_val"}, set(), False),
            ("happy_case1", {"dummy_key": "dummy_val"}, {"dummy_key"}, True),
            (
                "happy_case2",
                {"dummy_key1": "dummy_val"},
                {"dummy_key1", "dummy_key_2"},
                True,
            ),
            (
                "happy_case3",
                {"dummy_key1": "dummy_val", "dummy_key2": "dummy_val2"},
                {"dummy_key1"},
                True,
            ),
            ("sad_case", {"dummy_key1": "dummy_val"}, {"not_dummy_key1"}, False),
        ]
    )
    def test_PV_RQ_040_any_requirements_from(
        self, name, requirements, whence, expected
    ):
        result = reqs.any_requirements_from(requirements, whence)
        if expected:
            self.assertTrue(result)
        else:
            self.assertFalse(result)

    @parameterized.parameterized.expand(
        [
            ("from_files", {reqs.FROM_FILES: "dummy"}, True),
            ("from_packages", {reqs.FROM_PACKAGES: "dummy"}, True),
            (
                "from_both",
                {reqs.FROM_FILES: "dummy", reqs.FROM_PACKAGES: "dummy"},
                True,
            ),
            ("nope", {reqs.FROM_COMMANDS: "dummy"}, False),
            ("empty", {}, False),
        ]
    )
    def test_PV_RQ_050_requirements_need_pip(self, name, requirements, expected):
        result = reqs.requirements_need_pip(requirements)
        if expected:
            self.assertTrue(result)
        else:
            self.assertFalse(result)

    @parameterized.parameterized.expand(
        [
            ("none", {}, {}, []),
            ("simple", {reqs.FROM_COMMANDS: [["dummy"]]}, {}, [["dummy"]]),
            (
                "multi",
                {reqs.FROM_COMMANDS: [["dummy1"], ["dummy2"]]},
                {},
                [["dummy1"], ["dummy2"]],
            ),
            (
                "formatted1",
                {reqs.FROM_COMMANDS: [["{dummy}"]]},
                {"dummy": "dummyval"},
                [["dummyval"]],
            ),
            (
                "formatted2",
                {reqs.FROM_COMMANDS: [["{dummy1}"], ["{dummy2}"], ["dummy3"]]},
                {"dummy1": "dummyval1", "dummy2": "dummyval2"},
                [["dummyval1"], ["dummyval2"], ["dummy3"]],
            ),
            (
                "real",
                reqs.REQUIREMENTS[reqs.REQ_SCHEME_SOURCE],
                {"python": "dummy-python"},
                [["dummy-python", "setup.py", "install"]],
            ),
        ]
    )
    def test_PV_RQ_060_command_requirements(self, name, requirements, kwargs, expected):
        result = reqs.command_requirements(requirements, **kwargs)
        self.assertListEqual(result, expected)

    @parameterized.parameterized.expand(
        [
            ("none", {}, None, []),
            (
                "files_only",
                {reqs.FROM_FILES: ["dummy1", "dummy2"]},
                "dummy-package",
                ["-r", "dummy1", "-r", "dummy2"],
            ),
            (
                "package_only",
                {reqs.FROM_PACKAGES: ["{basename}"]},
                "dummy-package",
                ["dummy-package"],
            ),
            (
                "both",
                {
                    reqs.FROM_PACKAGES: ["{basename}"],
                    reqs.FROM_FILES: ["dummy1", "dummy2"],
                },
                "dummy-package",
                ["-r", "dummy1", "-r", "dummy2", "dummy-package"],
            ),
            (
                "extra",
                {
                    reqs.FROM_COMMANDS: ["dummy-command"],
                    reqs.FROM_PACKAGES: ["{basename}"],
                },
                "dummy-package",
                ["dummy-package"],
            ),
            (
                "real_plain",
                reqs.REQUIREMENTS[reqs.REQ_SCHEME_PLAIN],
                "dummy-package",
                ["-r", "requirements.txt"],
            ),
            (
                "real_package",
                reqs.REQUIREMENTS[reqs.REQ_SCHEME_PACKAGE],
                "dummy-package",
                ["dummy-package"],
            ),
        ]
    )
    def test_PV_RQ_070_pip_requirements(self, name, requirements, basename, expected):
        result = reqs.pip_requirements(requirements, basename)
        self.assertListEqual(result, expected)

    def test_PV_RQ_100_check_requirements_for_scheme_plain(self):
        # we expect to run from python_venv's project directory,
        # where 'requirements.txt' exists.
        reqs.check_requirements_for_scheme(reqs.REQ_SCHEME_PLAIN)

    def test_PV_RQ_101_check_requirements_for_scheme_invalid(self):
        with self.assertRaises(KeyError):
            reqs.check_requirements_for_scheme("yuck")

    def test_PV_RQ_102_check_requirements_for_scheme_nonexistent(self):
        reqs.REQUIREMENTS = {
            "weird": {
                reqs.FROM_FILES: ["weird-nonexistent.flummox"],
            },
        }
        with self.assertRaises(exceptions.MissingRequirementsError):
            reqs.check_requirements_for_scheme("weird")
