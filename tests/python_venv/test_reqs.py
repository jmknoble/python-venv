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
        _ = reqs.REQUIREMENTS_PLAIN
        _ = reqs.REQUIREMENTS_DEV
        _ = reqs.REQUIREMENTS_DEVPLUS
        _ = reqs.REQUIREMENTS_TEST
        _ = reqs.REQUIREMENTS_FROZEN
        _ = reqs.REQUIREMENTS_BUILD
        _ = reqs.REQUIREMENTS_PACKAGE
        _ = reqs.REQUIREMENTS_PIP
        _ = reqs.REQUIREMENTS_BUILD_SDIST
        _ = reqs.REQUIREMENTS_SDISTFILE
        _ = reqs.REQUIREMENTS_BUILD_WHEEL
        _ = reqs.REQUIREMENTS_WHEELFILE
        _ = reqs.REQUIREMENTS_VENV

        _ = reqs.REQ_SCHEME_PLAIN
        _ = reqs.REQ_SCHEME_DEV
        _ = reqs.REQ_SCHEME_DEVPLUS
        _ = reqs.REQ_SCHEME_FROZEN
        _ = reqs.REQ_SCHEME_PACKAGE
        _ = reqs.REQ_SCHEME_PIP
        _ = reqs.REQ_SCHEME_SOURCE
        _ = reqs.REQ_SCHEME_WHEEL
        _ = reqs.REQ_SCHEME_VENV

        _ = reqs.DEV_REQ_SCHEMES
        _ = reqs.ALL_REQ_SCHEMES

    @parameterized.parameterized.expand(
        [
            ("req_scheme_plain", reqs.REQ_SCHEME_PLAIN, "plain"),
            ("req_scheme_dev", reqs.REQ_SCHEME_DEV, "dev"),
            ("req_scheme_devplus", reqs.REQ_SCHEME_DEVPLUS, "devplus"),
            ("req_scheme_frozen", reqs.REQ_SCHEME_FROZEN, "frozen"),
            ("req_scheme_package", reqs.REQ_SCHEME_PACKAGE, "package"),
            ("req_scheme_pip", reqs.REQ_SCHEME_PIP, "pip"),
            ("req_scheme_source", reqs.REQ_SCHEME_SOURCE, "source"),
            ("req_scheme_wheel", reqs.REQ_SCHEME_WHEEL, "wheel"),
            ("req_scheme_venv", reqs.REQ_SCHEME_VENV, "venv"),
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
            ("devplus", reqs.REQ_SCHEME_DEVPLUS),
        ]
    )
    def test_PV_RQ_012_instantiate_with_real(self, name, scheme):
        reqs.ReqScheme(scheme)

    def test_PV_RQ_020_get_requirements(self):
        self._set_dummy_requirements()
        x = reqs.ReqScheme("dummy_req_scheme")
        self.assertListEqual(x._get_requirements(), self.dummy_requirements)
        self.assertListEqual(x.requirements, self.dummy_requirements)

    @parameterized.parameterized.expand(
        [
            ("plain", None, False),
            ("wheel", reqs.REQ_SCHEME_WHEEL, True),
        ]
    )
    def test_PV_RQ_021_get_requirements_venv(
        self, name, supplemental_scheme, expect_build_package
    ):
        self._set_dummy_requirements()
        x = reqs.ReqScheme(
            reqs.REQ_SCHEME_VENV, supplemental_scheme=supplemental_scheme
        )
        expected_requirements = reqs.SPECIAL_REQUIREMENTS[reqs.REQ_SCHEME_VENV][
            "default" if supplemental_scheme is None else supplemental_scheme
        ]
        self.assertListEqual(x.requirements, expected_requirements)
        venv_packages = []
        for entry in x.requirements:
            if const.FROM_PACKAGES in entry:
                venv_packages.extend(entry[const.FROM_PACKAGES])
        self.assertIn("pip", venv_packages)
        self.assertIn("setuptools", venv_packages)
        self.assertIn("wheel", venv_packages)
        if expect_build_package:
            self.assertIn("build", venv_packages)

    def test_PV_RQ_022_get_requirements_raises(self):
        self._set_dummy_requirements()
        with self.assertRaises(KeyError) as raised:
            reqs.ReqScheme("invalid_req_scheme")
        self.assertEqual(raised.exception.args[0], "invalid_req_scheme")

    @parameterized.parameterized.expand(
        [
            ("plain", reqs.REQ_SCHEME_PLAIN, False),
            ("dev", reqs.REQ_SCHEME_DEV, True),
            ("devplus", reqs.REQ_SCHEME_DEVPLUS, True),
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
    def test_PV_RQ_050_format(self, name, kwargs, expected):
        self._set_dummy_requirements()
        x = reqs.ReqScheme("dummy_req_scheme", **kwargs)
        result = x._format(["{python} {basename}"])
        self.assertListEqual(result, [expected])

    # TODO: Better testing of reqs.ReqScheme().fulfill()

    def test_PV_RQ_60_pip_argify_files(self):
        self._set_dummy_requirements()
        x = reqs.ReqScheme("dummy_req_scheme")
        files = ["dummy_one", "dummy_two"]
        expected = ["-r", "dummy_one", "-r", "dummy_two"]
        result = x._pip_argify_files(files)
        self.assertListEqual(result, expected)

    @parameterized.parameterized.expand(
        [
            ("none", {}, []),
            ("empty", {const.FROM_FILES: []}, []),
            (
                "full",
                {const.FROM_FILES: ["dummy_one", "dummy_two"]},
                ["dummy_one", "dummy_two"],
            ),
            (
                "multi",
                {
                    const.FROM_PACKAGES: ["dummy_package"],
                    const.FROM_FILES: ["dummy_one", "dummy_two"],
                },
                ["dummy_one", "dummy_two"],
            ),
        ]
    )
    def test_PV_RQ_70_get_requirements_files(self, name, entry, expected):
        self._set_dummy_requirements()
        x = reqs.ReqScheme("dummy_req_scheme")
        result = x._get_requirements_files(entry)
        self.assertListEqual(result, expected)

    @parameterized.parameterized.expand(
        [
            ("none", {}, []),
            ("empty", {const.FROM_PACKAGES: []}, []),
            (
                "full",
                {const.FROM_PACKAGES: ["dummy_one", "dummy_two"]},
                ["dummy_one", "dummy_two"],
            ),
            (
                "templated",
                {const.FROM_PACKAGES: ["{basename}_one", "{basename}_two"]},
                ["dummy_one", "dummy_two"],
            ),
            (
                "multi",
                {
                    const.FROM_PACKAGES: ["dummy_package"],
                    const.FROM_FILES: ["dummy_one", "dummy_two"],
                },
                ["dummy_package"],
            ),
        ]
    )
    def test_PV_RQ_71_get_requirements_packages(self, name, entry, expected):
        self._set_dummy_requirements()
        x = reqs.ReqScheme("dummy_req_scheme", basename="dummy")
        result = x._get_requirements_packages(entry)
        self.assertListEqual(result, expected)

    @parameterized.parameterized.expand(
        [
            ("none", {}, []),
            ("empty", {const.FROM_COMMANDS: []}, []),
            (
                "full",
                {const.FROM_COMMANDS: [["dummy_command", "dummy_arg"]]},
                [["dummy_command", "dummy_arg"]],
            ),
            (
                "templated",
                {
                    const.FROM_COMMANDS: [
                        ["{python}", "-m", "dummy_module", "dummy_arg"]
                    ]
                },
                [["schmython", "-m", "dummy_module", "dummy_arg"]],
            ),
            (
                "multi",
                {
                    const.FROM_COMMANDS: [
                        ["dummy_command1", "dummy_arg1"],
                        ["dummy_command2"],
                    ]
                },
                [["dummy_command1", "dummy_arg1"], ["dummy_command2"]],
            ),
        ]
    )
    def test_PV_RQ_72_get_requirements_commands(self, name, entry, expected):
        self._set_dummy_requirements()
        x = reqs.ReqScheme("dummy_req_scheme", python="schmython")
        result = x._get_requirements_commands(entry)
        self.assertListEqual(result, expected)

    @parameterized.parameterized.expand(
        [
            ("none", {}, ["dummy_pip_arg", "dummy_pip_arg_two"], []),
            (
                "empty",
                {const.FROM_PIP_ARGS: None},
                ["dummy_pip_arg", "dummy_pip_arg_two"],
                [],
            ),
            (
                "false",
                {const.FROM_PIP_ARGS: False},
                ["dummy_pip_arg", "dummy_pip_arg_two"],
                [],
            ),
            (
                "true",
                {const.FROM_PIP_ARGS: True},
                ["dummy_pip_arg", "dummy_pip_arg_two"],
                ["dummy_pip_arg", "dummy_pip_arg_two"],
            ),
            (
                "real",
                {const.FROM_PIP_ARGS: reqs.REQUIREMENTS_PIP},
                ["dummy_pip_arg", "dummy_pip_arg_two"],
                ["dummy_pip_arg", "dummy_pip_arg_two"],
            ),
        ]
    )
    def test_PV_RQ_73_get_requirements_pip_args(self, name, entry, pip_args, expected):
        self._set_dummy_requirements()
        x = reqs.ReqScheme("dummy_req_scheme", pip_args=pip_args, basename="dummy")
        result = x._get_requirements_pip_args(entry)
        self.assertListEqual(result, expected)

    @parameterized.parameterized.expand(
        [
            ("none", {}, [], []),
            ("empty", {const.FROM_FILES: []}, [], []),
            (
                "files_only",
                {const.FROM_FILES: ["dummy_one", "dummy_two"]},
                [],
                ["-r", "dummy_one", "-r", "dummy_two"],
            ),
            (
                "packages_only",
                {const.FROM_PACKAGES: ["dummy_package_1", "dummy_package_2"]},
                [],
                ["dummy_package_1", "dummy_package_2"],
            ),
            (
                "packages_templated",
                {const.FROM_PACKAGES: ["{basename}_package"]},
                [],
                ["dummy_package"],
            ),
            (
                "pip_args_only",
                {const.FROM_PIP_ARGS: True},
                ["dummy_pip_arg_1", "dummy_pip_arg_2"],
                ["dummy_pip_arg_1", "dummy_pip_arg_2"],
            ),
            (
                "multi",
                {
                    const.FROM_PACKAGES: ["dummy_package"],
                    const.FROM_FILES: ["dummy_one", "dummy_two"],
                    const.FROM_PIP_ARGS: True,
                },
                ["dummy_pip_arg_1", "dummy_pip_arg_2"],
                [
                    "-r",
                    "dummy_one",
                    "-r",
                    "dummy_two",
                    "dummy_package",
                    "dummy_pip_arg_1",
                    "dummy_pip_arg_2",
                ],
            ),
        ]
    )
    def test_PV_RQ_80_collect_pip_arguments(self, name, entry, pip_args, expected):
        self._set_dummy_requirements()
        x = reqs.ReqScheme("dummy_req_scheme", pip_args=pip_args, basename="dummy")
        result = x._collect_pip_arguments(entry)
        self.assertListEqual(result, expected)

    @parameterized.parameterized.expand(
        [
            ("none", {}, []),
            ("empty", {const.FROM_COMMANDS: []}, []),
            (
                "full",
                {const.FROM_COMMANDS: [["dummy_command", "dummy_arg"]]},
                [["dummy_command", "dummy_arg"]],
            ),
            (
                "templated",
                {
                    const.FROM_COMMANDS: [
                        ["{python}", "-m", "dummy_module", "dummy_arg"]
                    ]
                },
                [["schmython", "-m", "dummy_module", "dummy_arg"]],
            ),
            (
                "multi",
                {
                    const.FROM_COMMANDS: [
                        ["dummy_command1", "dummy_arg1"],
                        ["dummy_command2"],
                    ]
                },
                [["dummy_command1", "dummy_arg1"], ["dummy_command2"]],
            ),
        ]
    )
    def test_PV_RQ_81_collect_commands(self, name, entry, expected):
        self._set_dummy_requirements()
        x = reqs.ReqScheme("dummy_req_scheme", python="schmython")
        result = x._collect_commands(entry)
        self.assertListEqual(result, expected)

    @parameterized.parameterized.expand(
        [
            ("none", {}, []),
            ("empty", {const.FROM_BDIST_WHEEL: []}, []),
            (
                "full",
                {const.FROM_BDIST_WHEEL: ["dummy_command", "dummy_arg"]},
                ["dummy_command", "dummy_arg"],
            ),
            (
                "templated",
                {
                    const.FROM_BDIST_WHEEL: [
                        "{python}",
                        "-m",
                        "dummy_module",
                        "dummy_arg",
                    ]
                },
                ["schmython", "-m", "dummy_module", "dummy_arg"],
            ),
        ]
    )
    def test_PV_RQ_82_collect_bdist_wheel(self, name, entry, expected):
        self._set_dummy_requirements()
        x = reqs.ReqScheme("dummy_req_scheme", python="schmython")
        result = x._collect_bdist_wheel(entry)
        self.assertListEqual(result, expected)

    @parameterized.parameterized.expand(
        [
            ("none", {}, []),
            ("empty", {const.FROM_SDIST: []}, []),
            (
                "full",
                {const.FROM_SDIST: ["dummy_command", "dummy_arg"]},
                ["dummy_command", "dummy_arg"],
            ),
            (
                "templated",
                {
                    const.FROM_SDIST: [
                        "{python}",
                        "-m",
                        "dummy_module",
                        "dummy_arg",
                    ]
                },
                ["schmython", "-m", "dummy_module", "dummy_arg"],
            ),
        ]
    )
    def test_PV_RQ_83_collect_sdist(self, name, entry, expected):
        self._set_dummy_requirements()
        x = reqs.ReqScheme("dummy_req_scheme", python="schmython")
        result = x._collect_sdist(entry)
        self.assertListEqual(result, expected)

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
