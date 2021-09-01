"""Provide unit tests for `~python_venv.reqs`:py:mod:."""

import unittest

import parameterized  # https://pypi.org/project/parameterized/

from python_venv import const, exceptions, reqs

########################################
# Tests


class TestRequirements(unittest.TestCase):
    def setUp(self):
        self.saved_requirements = reqs.REQUIREMENTS

    def tearDown(self):
        reqs.REQUIREMENTS = self.saved_requirements

    def _set_dummy_requirements(self):
        self.dummy_requirements = [
            {"from_dummy": ["dummy_one", "dummy_two"]},
        ]
        reqs.REQUIREMENTS = {
            "dummy_req_scheme": self.dummy_requirements,
        }

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

    def test_PV_RQ_010_instantiate(self):
        self._set_dummy_requirements()
        reqs.ReqScheme("dummy_req_scheme")

    def test_PV_RQ_011_instantiate_with_args(self):
        self._set_dummy_requirements()
        dummy_env_dict = {"dummy_envariable": "dummy_value"}
        x = reqs.ReqScheme(
            "dummy_req_scheme",
            python="schmython",
            basename="dummy_basename",
            dry_run=True,
            show_trace=False,
            env=dummy_env_dict,
            stdout="dummy_stdout",
            stderr="dummy_stderr",
        )
        self.assertEqual(x.scheme, "dummy_req_scheme")
        self.assertEqual(x.python, "schmython")
        self.assertEqual(x.basename, "dummy_basename")
        self.assertTrue(x.dry_run)
        self.assertFalse(x.show_trace)
        self.assertDictEqual(x.env, dummy_env_dict)
        self.assertEqual(x.stdout, "dummy_stdout")
        self.assertEqual(x.stderr, "dummy_stderr")

    @parameterized.parameterized.expand(
        [
            ("plain", reqs.REQ_SCHEME_PLAIN),
            ("dev", reqs.REQ_SCHEME_DEV),
        ]
    )
    def test_PV_RQ_012_instantiate_with_real(self, name, scheme):
        reqs.ReqScheme(scheme)

    def test_PV_RQ_020_get_requirements(self):
        self._set_dummy_requirements()
        x = reqs.ReqScheme("dummy_req_scheme")
        self.assertListEqual(x._get_requirements(), self.dummy_requirements)
        self.assertListEqual(x.requirements, self.dummy_requirements)

    def test_PV_RQ_021_get_requirements_venv(self):
        self._set_dummy_requirements()
        x = reqs.ReqScheme(reqs.REQ_SCHEME_VENV)
        expected_requirements = reqs.SPECIAL_REQUIREMENTS[reqs.REQ_SCHEME_VENV]
        self.assertListEqual(x.requirements, expected_requirements)
        venv_packages = []
        for entry in x.requirements:
            if const.FROM_PACKAGES in entry:
                venv_packages.extend(entry[const.FROM_PACKAGES])
        self.assertIn("pip", venv_packages)
        self.assertIn("setuptools", venv_packages)
        self.assertIn("wheel", venv_packages)

    def test_PV_RQ_022_get_requirements_raises(self):
        self._set_dummy_requirements()
        with self.assertRaises(KeyError) as raised:
            reqs.ReqScheme("invalid_req_scheme")
        self.assertEqual(raised.exception.args[0], "invalid_req_scheme")

    @parameterized.parameterized.expand(
        [
            ("plain", reqs.REQ_SCHEME_PLAIN, False),
            ("dev", reqs.REQ_SCHEME_DEV, True),
        ]
    )
    def test_PV_RQ_030_is_dev(self, name, scheme, expected):
        x = reqs.ReqScheme(scheme)
        if expected:
            self.assertTrue(x.is_dev())
        else:
            self.assertFalse(x.is_dev())

    def test_PV_RQ_040_use_python(self):
        self._set_dummy_requirements()
        x = reqs.ReqScheme("dummy_req_scheme")
        self.assertIsNone(x.python)
        x.use_python("schmython")
        self.assertEqual(x.python, "schmython")

    def test_PV_RQ_041_pip_install_command(self):
        self._set_dummy_requirements()
        x = reqs.ReqScheme("dummy_req_scheme")
        self.assertIsNone(x.pip_install_command)
        x.use_python("schmython")
        self.assertListEqual(
            x.pip_install_command, ["schmython", "-m", "pip", "install"]
        )

    @parameterized.parameterized.expand(
        [
            ("default", {}, "None None"),
            ("none", {"python": None, "basename": None}, "None None"),
            (
                "actual",
                {"python": "schmython", "basename": "dummy_basename"},
                "schmython dummy_basename",
            ),
        ]
    )
    def test_PV_RQ_050_replace(self, name, kwargs, expected):
        self._set_dummy_requirements()
        x = reqs.ReqScheme("dummy_req_scheme", **kwargs)
        result = x._replace(["{python} {basename}"])
        self.assertListEqual(result, [expected])

    # TODO: Better testing of reqs.ReqScheme().fulfill()

    def test_PV_RQ_100_check_requirements_for_scheme_plain(self):
        # we expect to run from python_venv's project directory,
        # where 'requirements.txt' exists.
        x = reqs.ReqScheme(reqs.REQ_SCHEME_PLAIN)
        x.check()

    def test_PV_RQ_102_check_requirements_for_scheme_nonexistent(self):
        self._set_dummy_requirements()
        reqs.REQUIREMENTS["weird"] = [
            {const.FROM_FILES: ["weird-nonexistent.flummox"]},
        ]
        x = reqs.ReqScheme("weird")
        with self.assertRaises(exceptions.MissingRequirementsError):
            x.check()
