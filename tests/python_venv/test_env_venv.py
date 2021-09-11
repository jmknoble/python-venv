"""Provide unit tests for `~python_venv.env`:py:mod:."""

import os
import os.path
import subprocess
import unittest

import parameterized  # https://pypi.org/project/parameterized/

from python_venv import const, env
from python_venv import exceptions as exc
from python_venv import reqs
from tests.python_venv import contextmgr as ctx
from tests.python_venv import flags

########################################


class TestEnv_100_VenvEnvironment(unittest.TestCase):
    def setUp(self):
        self.saved_requirements = reqs.REQUIREMENTS

    def tearDown(self):
        reqs.REQUIREMENTS = self.saved_requirements

    def test_PV_ENV_VNV_000_instantiate_empty(self):
        with self.assertRaises(TypeError) as raised:
            env.VenvEnvironment()
        msg = raised.exception.args[0]
        self.assertTrue(
            msg.startswith("__init__() missing 1 required positional argument")
        )

    @parameterized.parameterized.expand(
        [
            ("dry_run", {"dry_run": True}, "dry_run", True),
            ("force", {"force": True}, "force", True),
            (
                "message_prefix",
                {"message_prefix": "dummy_message_prefix"},
                "message_prefix",
                "dummy_message_prefix",
            ),
            ("python", {"python": "dummy_python"}, "python", "dummy_python"),
            ("basename", {"basename": "dummy_basename"}, "_basename", "dummy_basename"),
            ("env_name", {"env_name": "dummy_env_name"}, "_env_name", "dummy_env_name"),
            (
                "env_prefix",
                {"env_prefix": "dummy_env_prefix"},
                "_env_prefix",
                "dummy_env_prefix",
            ),
        ]
    )
    def test_PV_ENV_VNV_002_instantiate_kwargs(self, name, kwargs, attr, value):
        x = env.VenvEnvironment("dummy_req_scheme", **kwargs)
        self.assertEqual(getattr(x, attr), value)

    def test_PV_ENV_VNV_010_requirements(self):
        dummy_requirements = {"dummy_req_source": ["dummy_requirement"]}
        reqs.REQUIREMENTS = {"dummy_req_scheme": [dummy_requirements]}
        x = env.VenvEnvironment("dummy_req_scheme")
        self.assertListEqual(x.requirements.requirements, [dummy_requirements])

    def test_PV_ENV_VNV_020_package_name(self):
        x = env.VenvEnvironment("dummy_req_scheme")
        self.assertEqual(x.package_name, "python_venv")

    @parameterized.parameterized.expand(
        [
            ("default", None, "python-venv"),
            ("specified", "dummy-package", "dummy-package"),
        ]
    )
    def test_PV_ENV_VNV_030_basename(self, name, basename, expected):
        kwargs = {} if basename is None else {"basename": basename}
        x = env.VenvEnvironment("dummy_req_scheme", **kwargs)
        self.assertEqual(x.basename, expected)

    @parameterized.parameterized.expand(
        [
            ("default", None, ".venv"),
            ("specified", "dummy-env", "dummy-env"),
        ]
    )
    def test_PV_ENV_VNV_040_env_name(self, name, env_name, expected):
        kwargs = {} if env_name is None else {"env_name": env_name}
        x = env.VenvEnvironment("dummy_req_scheme", **kwargs)
        self.assertEqual(x.env_name, expected)

    @parameterized.parameterized.expand(
        [
            ("default", None, None, ".venv"),
            ("specified", "dummy-env", None, "dummy-env"),
            (
                "with_prefix",
                None,
                "dummy-prefix",
                os.path.join("dummy-prefix", ".venv"),
            ),
            (
                "specified_with_prefix",
                "dummy-env",
                "dummy-prefix",
                os.path.join("dummy-prefix", "dummy-env"),
            ),
        ]
    )
    def test_PV_ENV_VNV_050_env_dir(self, name, env_name, env_prefix, expected):
        kwargs = {}
        if env_name is not None:
            kwargs["env_name"] = env_name
        if env_prefix is not None:
            kwargs["env_prefix"] = env_prefix
        x = env.VenvEnvironment("dummy_req_scheme", **kwargs)
        self.assertEqual(x.env_dir, expected)

    @parameterized.parameterized.expand(
        [
            ("default", None, None, os.path.join(".venv", "bin")),
            ("specified", "dummy-env", None, os.path.join("dummy-env", "bin")),
            (
                "with_prefix",
                None,
                "dummy-prefix",
                os.path.join("dummy-prefix", ".venv", "bin"),
            ),
            (
                "specified_with_prefix",
                "dummy-env",
                "dummy-prefix",
                os.path.join("dummy-prefix", "dummy-env", "bin"),
            ),
        ]
    )
    def test_PV_ENV_VNV_051_env_bin_dir(self, name, env_name, env_prefix, expected):
        kwargs = {}
        if env_name is not None:
            kwargs["env_name"] = env_name
        if env_prefix is not None:
            kwargs["env_prefix"] = env_prefix
        x = env.VenvEnvironment("dummy_req_scheme", **kwargs)
        self.assertEqual(x.env_bin_dir, expected)

    @parameterized.parameterized.expand(
        [
            (
                "default",
                "dummy-python",
                None,
                None,
                os.path.join(".venv", "bin", "dummy-python"),
            ),
            (
                "specified",
                "dummy-python",
                "dummy-env",
                None,
                os.path.join("dummy-env", "bin", "dummy-python"),
            ),
            (
                "with_prefix",
                "dummy-python",
                None,
                "dummy-prefix",
                os.path.join("dummy-prefix", ".venv", "bin", "dummy-python"),
            ),
            (
                "specified_with_prefix",
                "dummy-python",
                "dummy-env",
                "dummy-prefix",
                os.path.join("dummy-prefix", "dummy-env", "bin", "dummy-python"),
            ),
            (
                "with_path",
                os.path.join(os.sep, "usr", "bin", "dummy-python"),
                None,
                None,
                os.path.join(".venv", "bin", "dummy-python"),
            ),
            (
                "specified_with_path",
                os.path.join(os.sep, "usr", "bin", "dummy-python"),
                "dummy-env",
                None,
                os.path.join("dummy-env", "bin", "dummy-python"),
            ),
        ]
    )
    def test_PV_ENV_VNV_052_env_python(
        self, name, python, env_name, env_prefix, expected
    ):
        kwargs = {}
        if python is not None:
            kwargs["python"] = python
        if env_name is not None:
            kwargs["env_name"] = env_name
        if env_prefix is not None:
            kwargs["env_prefix"] = env_prefix
        x = env.VenvEnvironment("dummy_req_scheme", **kwargs)
        self.assertEqual(x.env_python, expected)

    @parameterized.parameterized.expand(
        [
            ("default", None, None, os.path.join(os.getcwd(), ".venv")),
            ("specified", "dummy-env", None, os.path.join(os.getcwd(), "dummy-env")),
            (
                "with_prefix",
                None,
                "dummy-prefix",
                os.path.join(os.getcwd(), "dummy-prefix", ".venv"),
            ),
            (
                "specified_with_prefix",
                "dummy-env",
                "dummy-prefix",
                os.path.join(os.getcwd(), "dummy-prefix", "dummy-env"),
            ),
        ]
    )
    def test_PV_ENV_VNV_051_abs_env_dir(self, name, env_name, env_prefix, expected):
        kwargs = {}
        if env_name is not None:
            kwargs["env_name"] = env_name
        if env_prefix is not None:
            kwargs["env_prefix"] = env_prefix
        x = env.VenvEnvironment("dummy_req_scheme", **kwargs)
        self.assertEqual(x.abs_env_dir, expected)

    @parameterized.parameterized.expand(
        [
            ("default", None, None, ".venv"),
            ("specified", "dummy-env", None, "dummy-env"),
            (
                "with_prefix",
                None,
                "dummy-prefix",
                os.path.join("dummy-prefix", ".venv"),
            ),
            (
                "specified_with_prefix",
                "dummy-env",
                "dummy-prefix",
                os.path.join("dummy-prefix", "dummy-env"),
            ),
        ]
    )
    def test_PV_ENV_VNV_060_env_description(self, name, env_name, env_prefix, expected):
        kwargs = {}
        if env_name is not None:
            kwargs["env_name"] = env_name
        if env_prefix is not None:
            kwargs["env_prefix"] = env_prefix
        x = env.VenvEnvironment("dummy_req_scheme", **kwargs)
        x.env_description
        self.assertTrue(x.env_description.endswith(expected))

    @parameterized.parameterized.expand(
        [
            ("dry_run_text", "[DRY-RUN]"),
            ("create_msg", "Creating Python venv at .dummy-venv"),
            ("create_venv", "+ python3 -m venv .dummy-venv"),
            ("install_msg", "Installing dummy_req_scheme requirements"),
            (
                "pip_install",
                "+ {python} -m pip install -r dummy_requirements.txt".format(
                    python=os.path.join(".dummy-venv", "bin", "python3")
                ),
            ),
            ("success", "==> Done."),
        ]
    )
    def test_PV_ENV_VNV_100_create_dry_run(self, name, expected_text):
        dummy_requirements = {const.FROM_FILES: ["dummy_requirements.txt"]}
        reqs.REQUIREMENTS = {"dummy_req_scheme": [dummy_requirements]}
        x = env.VenvEnvironment(
            "dummy_req_scheme",
            dry_run=True,
            env_name=".dummy-venv",
            ignore_preflight_checks=True,
        )
        with ctx.capture_to_file(x.create) as (
            status,
            _stdout,
            stderr,
        ):
            self.assertTrue(expected_text in stderr)

    @parameterized.parameterized.expand(
        [
            ("dry_run_text", "[DRY-RUN]"),
            ("remove_msg", "Removing Python venv at .dummy-venv"),
        ]
    )
    def test_PV_ENV_VNV_200_remove_dry_run(self, name, expected_text):
        x = env.VenvEnvironment(
            "dummy_req_scheme", dry_run=True, env_name=".dummy-venv"
        )
        with ctx.capture(x.remove) as (status, _stdout, stderr):
            self.assertTrue(expected_text in stderr)

    @parameterized.parameterized.expand(
        [
            ("dry_run_text", "[DRY-RUN]"),
            ("replace_msg", "Replacing Python venv at .dummy-venv"),
            ("remove_msg", "Removing Python venv at .dummy-venv"),
            ("create_msg", "Creating Python venv at .dummy-venv"),
            ("success", "==> Done."),
        ]
    )
    def test_PV_ENV_VNV_300_replace_dry_run(self, name, expected_text):
        dummy_requirements = {const.FROM_FILES: ["dummy_requirements.txt"]}
        reqs.REQUIREMENTS = {"dummy_req_scheme": [dummy_requirements]}
        x = env.VenvEnvironment(
            "dummy_req_scheme",
            dry_run=True,
            env_name=".dummy-venv",
            ignore_preflight_checks=True,
        )
        with ctx.capture_to_file(x.replace) as (status, _stdout, stderr):
            self.assertTrue(expected_text in stderr)


########################################


class TestEnv_110_VenvCreate(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    @parameterized.parameterized.expand(
        [
            ("plain_dry_run", reqs.REQ_SCHEME_PLAIN, True, None, None, []),
            ("plain", reqs.REQ_SCHEME_PLAIN, False, None, None, []),
            (
                "plain_dry_run_env_name",
                reqs.REQ_SCHEME_PLAIN,
                True,
                None,
                ".dummy-venv",
                [],
            ),
            ("plain_env_name", reqs.REQ_SCHEME_PLAIN, False, None, ".dummy-venv", []),
            ("dev_dry_run", reqs.REQ_SCHEME_DEV, True, None, None, []),
            ("dev", reqs.REQ_SCHEME_DEV, False, None, None, []),
            ("devplus_dry_run", reqs.REQ_SCHEME_DEVPLUS, True, None, None, []),
            ("devplus", reqs.REQ_SCHEME_DEVPLUS, False, None, None, []),
            ("frozen_dry_run", reqs.REQ_SCHEME_FROZEN, True, None, None, []),
            ("frozen", reqs.REQ_SCHEME_FROZEN, False, None, None, []),
            ("source_dry_run", reqs.REQ_SCHEME_SOURCE, True, None, None, []),
            ("source", reqs.REQ_SCHEME_SOURCE, False, None, None, []),
            ("wheel_dry_run", reqs.REQ_SCHEME_WHEEL, True, None, None, []),
            ("wheel", reqs.REQ_SCHEME_WHEEL, False, None, None, []),
            ("package_dry_run", reqs.REQ_SCHEME_PACKAGE, True, "argcomplete", None, []),
            ("package", reqs.REQ_SCHEME_PACKAGE, False, "argcomplete", None, []),
            ("pip_dry_run", reqs.REQ_SCHEME_PIP, True, None, None, ["argcomplete"]),
            ("pip", reqs.REQ_SCHEME_PIP, False, None, None, ["argcomplete"]),
        ]
    )
    def test_PV_ENV_VNV_110_create(
        self, name, req_scheme, dry_run, basename, env_name, pip_args
    ):
        filespecs = {
            "requirements.txt": "argcomplete",
            "requirements_dev.txt": "argcomplete",
            "requirements_frozen.txt": "argcomplete == 1.12.3",
            os.path.join("dev", "requirements_build.txt"): "",
            os.path.join("dev", "requirements_dev.txt"): "",
            os.path.join("dev", "requirements_test.txt"): "parameterized",
        }
        with ctx.project("dummy_package", filespecs=filespecs):
            x = env.VenvEnvironment(
                req_scheme, basename=basename, env_name=env_name, dry_run=dry_run
            )
            if not flags.should_suppress_output():
                x.create()
            else:
                original_stderr = None
                with ctx.capture_to_file(x.create) as (
                    _status,
                    _stdout,
                    stderr,
                ):
                    original_stderr = stderr
                testable_stderr = original_stderr.lower()
                if "error" in testable_stderr:
                    print(original_stderr, file=stderr)
                self.assertNotIn("error", testable_stderr)

    @parameterized.parameterized.expand(
        [
            ("plain_dry_run", reqs.REQ_SCHEME_PLAIN, True, None, None, []),
            ("plain", reqs.REQ_SCHEME_PLAIN, False, None, None, []),
            (
                "plain_dry_run_env_name",
                reqs.REQ_SCHEME_PLAIN,
                True,
                None,
                ".dummy-venv",
                [],
            ),
            ("plain_env_name", reqs.REQ_SCHEME_PLAIN, False, None, ".dummy-venv", []),
            ("dev_dry_run", reqs.REQ_SCHEME_DEV, True, None, None, []),
            ("dev", reqs.REQ_SCHEME_DEV, False, None, None, []),
            ("devplus_dry_run", reqs.REQ_SCHEME_DEVPLUS, True, None, None, []),
            ("devplus", reqs.REQ_SCHEME_DEVPLUS, False, None, None, []),
            ("frozen_dry_run", reqs.REQ_SCHEME_FROZEN, True, None, None, []),
            ("frozen", reqs.REQ_SCHEME_FROZEN, False, None, None, []),
            ("source_dry_run", reqs.REQ_SCHEME_SOURCE, True, None, None, []),
            ("source", reqs.REQ_SCHEME_SOURCE, False, None, None, []),
            ("wheel_dry_run", reqs.REQ_SCHEME_WHEEL, True, None, None, []),
            ("wheel", reqs.REQ_SCHEME_WHEEL, False, None, None, []),
            ("package_dry_run", reqs.REQ_SCHEME_PACKAGE, True, "argcomplete", None, []),
            ("package", reqs.REQ_SCHEME_PACKAGE, False, "argcomplete", None, []),
            ("pip_dry_run", reqs.REQ_SCHEME_PIP, True, None, None, ["argcomplete"]),
            ("pip", reqs.REQ_SCHEME_PIP, False, None, None, ["argcomplete"]),
        ]
    )
    def test_PV_ENV_VNV_111_create_no_setup(
        self, name, req_scheme, dry_run, basename, env_name, pip_args
    ):
        filespecs = {
            "requirements.txt": "argcomplete",
            "requirements_dev.txt": "argcomplete",
            "requirements_frozen.txt": "argcomplete == 1.12.3",
            os.path.join("dev", "requirements_build.txt"): "",
            os.path.join("dev", "requirements_dev.txt"): "",
            os.path.join("dev", "requirements_test.txt"): "parameterized",
        }
        should_raise = not (
            req_scheme in {reqs.REQ_SCHEME_PIP}
            or (req_scheme in {reqs.REQ_SCHEME_PACKAGE} and basename is not None)
        )
        with ctx.project("dummy_package", filespecs=filespecs, omit_setup=True):
            with ctx.capture_output_to_file():
                x = env.VenvEnvironment(
                    req_scheme, basename=basename, env_name=env_name, dry_run=dry_run
                )
                if should_raise:
                    with self.assertRaises(subprocess.CalledProcessError):
                        x.create()
                else:
                    x.create()

    @parameterized.parameterized.expand(
        [
            ("plain_dry_run", reqs.REQ_SCHEME_PLAIN, True, None, None, "dummy-prefix"),
            ("plain", reqs.REQ_SCHEME_PLAIN, False, None, None, "dummy-prefix"),
            ("plain_curdir", reqs.REQ_SCHEME_PLAIN, False, None, None, os.curdir),
            (
                "plain_dry_run_env_name",
                reqs.REQ_SCHEME_PLAIN,
                True,
                None,
                ".dummy-venv",
                "dummy-prefix",
            ),
            (
                "plain_env_name",
                reqs.REQ_SCHEME_PLAIN,
                False,
                None,
                ".dummy-venv",
                "dummy-prefix",
            ),
            (
                "plain_nonexistent",
                reqs.REQ_SCHEME_PLAIN,
                False,
                None,
                None,
                "surprising-prefix",
            ),
        ]
    )
    def test_PV_ENV_VNV_115_create_with_prefix(
        self, name, req_scheme, dry_run, basename, env_name, env_prefix
    ):
        dirs = ["dummy-prefix"]
        filespecs = {
            "requirements.txt": "argcomplete",
            "requirements_dev.txt": "argcomplete",
            "requirements_frozen.txt": "argcomplete == 1.12.3",
            os.path.join("dev", "requirements_build.txt"): "",
            os.path.join("dev", "requirements_dev.txt"): "",
            os.path.join("dev", "requirements_test.txt"): "parameterized",
        }
        with ctx.project("dummy_package", dirs=dirs, filespecs=filespecs):
            x = env.VenvEnvironment(
                req_scheme,
                basename=basename,
                env_name=env_name,
                env_prefix=env_prefix,
                dry_run=dry_run,
            )
            if not flags.should_suppress_output():
                x.create()
            else:
                original_stderr = None
                with ctx.capture_to_file(x.create) as (
                    _status,
                    _stdout,
                    stderr,
                ):
                    original_stderr = stderr
                testable_stderr = original_stderr.lower()
                if "error" in testable_stderr:
                    print(original_stderr, file=stderr)
                self.assertNotIn("error", testable_stderr)

    @parameterized.parameterized.expand(
        [
            ("plain_dry_run", reqs.REQ_SCHEME_PLAIN, True, None, None),
            ("plain", reqs.REQ_SCHEME_PLAIN, False, None, None),
            ("dev_dry_run", reqs.REQ_SCHEME_DEV, True, None, None),
            ("dev", reqs.REQ_SCHEME_DEV, False, None, None),
            ("devplus_dry_run", reqs.REQ_SCHEME_DEVPLUS, True, None, None),
            ("devplus", reqs.REQ_SCHEME_DEVPLUS, False, None, None),
            ("frozen_dry_run", reqs.REQ_SCHEME_FROZEN, True, None, None),
            ("frozen", reqs.REQ_SCHEME_FROZEN, False, None, None),
        ]
    )
    def test_PV_ENV_VNV_120_create_missing_reqs(
        self, name, req_scheme, dry_run, basename, env_name
    ):
        with ctx.project("dummy_package"):
            x = env.VenvEnvironment(
                req_scheme, basename=basename, env_name=env_name, dry_run=dry_run
            )
            with self.assertRaises(exc.MissingRequirementsError):
                if not flags.should_suppress_output():
                    x.create()
                else:
                    with ctx.capture_to_file(x.create) as (
                        _status,
                        _stdout,
                        _stderr,
                    ):
                        pass

    @parameterized.parameterized.expand(
        [
            ("plain_dry_run", reqs.REQ_SCHEME_PLAIN, True, None, True),
            ("plain", reqs.REQ_SCHEME_PLAIN, False, None, True),
            (
                "plain_dry_run_env_name",
                reqs.REQ_SCHEME_PLAIN,
                True,
                ".dummy-venv",
                True,
            ),
            ("plain_env_name", reqs.REQ_SCHEME_PLAIN, False, ".dummy-venv", True),
        ]
    )
    def test_PV_ENV_VNV_130_create_duplicate(
        self, name, req_scheme, dry_run, env_name, should_raise
    ):
        filespecs = {
            "requirements.txt": "argcomplete",
            "requirements_dev.txt": "argcomplete",
            "requirements_frozen.txt": "argcomplete == 1.12.3",
            os.path.join("dev", "requirements_build.txt"): "",
            os.path.join("dev", "requirements_dev.txt"): "",
            os.path.join("dev", "requirements_test.txt"): "parameterized",
        }
        with ctx.project("dummy_package", filespecs=filespecs):
            x = env.VenvEnvironment(req_scheme, env_name=env_name, dry_run=False)
            if not flags.should_suppress_output():
                x.create()
            else:
                with ctx.capture_to_file(x.create) as (_status, _stdout, _stderr):
                    pass
            x = env.VenvEnvironment(req_scheme, env_name=env_name, dry_run=dry_run)
            if should_raise:
                with self.assertRaises(exc.EnvExistsError):
                    if not flags.should_suppress_output():
                        x.create()
                    else:
                        with ctx.capture_to_file(x.create) as (
                            _status,
                            _stdout,
                            _stderr,
                        ):
                            pass
            else:
                if not flags.should_suppress_output():
                    x.create()
                else:
                    original_stderr = None
                    with ctx.capture_to_file(x.create) as (_status, _stdout, stderr):
                        original_stderr = stderr
                    testable_stderr = original_stderr.lower()
                    if "error" in testable_stderr:
                        print(original_stderr, file=stderr)
                    self.assertNotIn("error", testable_stderr)


########################################


class TestEnv_120_VenvRemove(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    @parameterized.parameterized.expand(
        [
            ("plain_dry_run", reqs.REQ_SCHEME_PLAIN, True, None, None, None, []),
            ("plain", reqs.REQ_SCHEME_PLAIN, False, None, None, None, []),
            (
                "plain_dry_run_env_name",
                reqs.REQ_SCHEME_PLAIN,
                True,
                None,
                ".dummy-venv",
                None,
                [],
            ),
            (
                "plain_env_name",
                reqs.REQ_SCHEME_PLAIN,
                False,
                None,
                ".dummy-venv",
                None,
                [],
            ),
            (
                "prefix_dry_run",
                reqs.REQ_SCHEME_PLAIN,
                True,
                None,
                None,
                "dummy-prefix",
                [],
            ),
            ("prefix", reqs.REQ_SCHEME_PLAIN, False, None, None, "dummy-prefix", []),
            (
                "prefix_dry_run_env_name",
                reqs.REQ_SCHEME_PLAIN,
                True,
                None,
                ".dummy-venv",
                "dummy-prefix",
                [],
            ),
            (
                "prefix_env_name",
                reqs.REQ_SCHEME_PLAIN,
                False,
                None,
                ".dummy-venv",
                "dummy-prefix",
                [],
            ),
            ("dev_dry_run", reqs.REQ_SCHEME_DEV, True, None, None, None, []),
            ("dev", reqs.REQ_SCHEME_DEV, False, None, None, None, []),
            ("devplus_dry_run", reqs.REQ_SCHEME_DEVPLUS, True, None, None, None, []),
            ("devplus", reqs.REQ_SCHEME_DEVPLUS, False, None, None, None, []),
            ("frozen_dry_run", reqs.REQ_SCHEME_FROZEN, True, None, None, None, []),
            ("frozen", reqs.REQ_SCHEME_FROZEN, False, None, None, None, []),
            ("source_dry_run", reqs.REQ_SCHEME_SOURCE, True, None, None, None, []),
            ("source", reqs.REQ_SCHEME_SOURCE, False, None, None, None, []),
            ("wheel_dry_run", reqs.REQ_SCHEME_WHEEL, True, None, None, None, []),
            ("wheel", reqs.REQ_SCHEME_WHEEL, False, None, None, None, []),
            (
                "package_dry_run",
                reqs.REQ_SCHEME_PACKAGE,
                True,
                "argcomplete",
                None,
                None,
                [],
            ),
            ("package", reqs.REQ_SCHEME_PACKAGE, False, "argcomplete", None, None, []),
            (
                "pip_dry_run",
                reqs.REQ_SCHEME_PIP,
                True,
                None,
                None,
                None,
                ["argcomplete"],
            ),
            ("pip", reqs.REQ_SCHEME_PIP, False, None, None, None, ["argcomplete"]),
        ]
    )
    def test_PV_ENV_VNV_210_remove(
        self, name, req_scheme, dry_run, basename, env_name, env_prefix, pip_args
    ):
        filespecs = {
            "requirements.txt": "argcomplete",
            "requirements_dev.txt": "argcomplete",
            "requirements_frozen.txt": "argcomplete == 1.12.3",
            os.path.join("dev", "requirements_build.txt"): "",
            os.path.join("dev", "requirements_dev.txt"): "",
            os.path.join("dev", "requirements_test.txt"): "parameterized",
        }
        with ctx.project("dummy_package", filespecs=filespecs):
            x = env.VenvEnvironment(
                req_scheme,
                pip_args=pip_args,
                basename=basename,
                env_name=env_name,
                env_prefix=env_prefix,
                dry_run=dry_run,
            )
            y = env.VenvEnvironment(
                req_scheme,
                pip_args=pip_args,
                basename=basename,
                env_name=env_name,
                env_prefix=env_prefix,
                dry_run=False,
            )
            if not flags.should_suppress_output():
                x.remove()  # remove non-existent
                y.create()
                x.remove()  # remove existing
            else:
                original_stderrs = []
                with ctx.capture_to_file(x.remove) as (_status, _stdout, stderr):
                    original_stderrs.append(stderr)
                with ctx.capture_to_file(y.create) as (_status, _stdout, stderr):
                    original_stderrs.append(stderr)
                with ctx.capture_to_file(x.remove) as (_status, _stdout, stderr):
                    original_stderrs.append(stderr)
                testable_stderrs = [text.lower() for text in original_stderrs]
                for (i, text) in enumerate(testable_stderrs):
                    if "error" in text:
                        print(original_stderrs[i], file=stderr)
                    self.assertNotIn("error", text)


########################################


class TestEnv_130_VenvReplace(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    @parameterized.parameterized.expand(
        [
            ("plain_dry_run", reqs.REQ_SCHEME_PLAIN, True, None, None, None, []),
            ("plain", reqs.REQ_SCHEME_PLAIN, False, None, None, None, []),
            (
                "plain_dry_run_env_name",
                reqs.REQ_SCHEME_PLAIN,
                True,
                None,
                ".dummy-venv",
                None,
                [],
            ),
            (
                "plain_env_name",
                reqs.REQ_SCHEME_PLAIN,
                False,
                None,
                ".dummy-venv",
                None,
                [],
            ),
            (
                "prefix_dry_run",
                reqs.REQ_SCHEME_PLAIN,
                True,
                None,
                None,
                "dummy-prefix",
                [],
            ),
            ("prefix", reqs.REQ_SCHEME_PLAIN, False, None, None, "dummy-prefix", []),
            (
                "prefix_dry_run_env_name",
                reqs.REQ_SCHEME_PLAIN,
                True,
                None,
                ".dummy-venv",
                "dummy-prefix",
                [],
            ),
            (
                "prefix_env_name",
                reqs.REQ_SCHEME_PLAIN,
                False,
                None,
                ".dummy-venv",
                "dummy-prefix",
                [],
            ),
            ("dev_dry_run", reqs.REQ_SCHEME_DEV, True, None, None, None, []),
            ("dev", reqs.REQ_SCHEME_DEV, False, None, None, None, []),
            ("devplus_dry_run", reqs.REQ_SCHEME_DEVPLUS, True, None, None, None, []),
            ("devplus", reqs.REQ_SCHEME_DEVPLUS, False, None, None, None, []),
            ("frozen_dry_run", reqs.REQ_SCHEME_FROZEN, True, None, None, None, []),
            ("frozen", reqs.REQ_SCHEME_FROZEN, False, None, None, None, []),
            ("source_dry_run", reqs.REQ_SCHEME_SOURCE, True, None, None, None, []),
            ("source", reqs.REQ_SCHEME_SOURCE, False, None, None, None, []),
            ("wheel_dry_run", reqs.REQ_SCHEME_WHEEL, True, None, None, None, []),
            ("wheel", reqs.REQ_SCHEME_WHEEL, False, None, None, None, []),
            (
                "package_dry_run",
                reqs.REQ_SCHEME_PACKAGE,
                True,
                "argcomplete",
                None,
                None,
                [],
            ),
            ("package", reqs.REQ_SCHEME_PACKAGE, False, "argcomplete", None, None, []),
            (
                "pip_dry_run",
                reqs.REQ_SCHEME_PIP,
                True,
                None,
                None,
                None,
                ["argcomplete"],
            ),
            ("pip", reqs.REQ_SCHEME_PIP, False, None, None, None, ["argcomplete"]),
        ]
    )
    def test_PV_ENV_VNV_310_replace_nonexistent(
        self, name, req_scheme, dry_run, basename, env_name, env_prefix, pip_args
    ):
        filespecs = {
            "requirements.txt": "argcomplete",
            "requirements_dev.txt": "argcomplete",
            "requirements_frozen.txt": "argcomplete == 1.12.3",
            os.path.join("dev", "requirements_build.txt"): "",
            os.path.join("dev", "requirements_dev.txt"): "",
            os.path.join("dev", "requirements_test.txt"): "parameterized",
        }
        with ctx.project("dummy_package", filespecs=filespecs):
            x = env.VenvEnvironment(
                req_scheme,
                pip_args=pip_args,
                basename=basename,
                env_name=env_name,
                env_prefix=env_prefix,
                dry_run=dry_run,
            )
            if not flags.should_suppress_output():
                x.replace()
            else:
                original_stderrs = []
                with ctx.capture_to_file(x.replace) as (_status, _stdout, stderr):
                    original_stderrs.append(stderr)
                testable_stderrs = [text.lower() for text in original_stderrs]
                for (i, text) in enumerate(testable_stderrs):
                    if "error" in text:
                        print(original_stderrs[i], file=stderr)
                    self.assertNotIn("error", text)

    @parameterized.parameterized.expand(
        [
            ("plain_dry_run", reqs.REQ_SCHEME_PLAIN, True, None, None, None, []),
            ("plain", reqs.REQ_SCHEME_PLAIN, False, None, None, None, []),
            (
                "plain_dry_run_env_name",
                reqs.REQ_SCHEME_PLAIN,
                True,
                None,
                ".dummy-venv",
                None,
                [],
            ),
            (
                "plain_env_name",
                reqs.REQ_SCHEME_PLAIN,
                False,
                None,
                ".dummy-venv",
                None,
                [],
            ),
            (
                "prefix_dry_run",
                reqs.REQ_SCHEME_PLAIN,
                True,
                None,
                None,
                "dummy-prefix",
                [],
            ),
            ("prefix", reqs.REQ_SCHEME_PLAIN, False, None, None, "dummy-prefix", []),
            (
                "prefix_dry_run_env_name",
                reqs.REQ_SCHEME_PLAIN,
                True,
                None,
                ".dummy-venv",
                "dummy-prefix",
                [],
            ),
            (
                "prefix_env_name",
                reqs.REQ_SCHEME_PLAIN,
                False,
                None,
                ".dummy-venv",
                "dummy-prefix",
                [],
            ),
            ("dev_dry_run", reqs.REQ_SCHEME_DEV, True, None, None, None, []),
            ("dev", reqs.REQ_SCHEME_DEV, False, None, None, None, []),
            ("devplus_dry_run", reqs.REQ_SCHEME_DEVPLUS, True, None, None, None, []),
            ("devplus", reqs.REQ_SCHEME_DEVPLUS, False, None, None, None, []),
            ("frozen_dry_run", reqs.REQ_SCHEME_FROZEN, True, None, None, None, []),
            ("frozen", reqs.REQ_SCHEME_FROZEN, False, None, None, None, []),
            ("source_dry_run", reqs.REQ_SCHEME_SOURCE, True, None, None, None, []),
            ("source", reqs.REQ_SCHEME_SOURCE, False, None, None, None, []),
            ("wheel_dry_run", reqs.REQ_SCHEME_WHEEL, True, None, None, None, []),
            ("wheel", reqs.REQ_SCHEME_WHEEL, False, None, None, None, []),
            (
                "package_dry_run",
                reqs.REQ_SCHEME_PACKAGE,
                True,
                "argcomplete",
                None,
                None,
                [],
            ),
            ("package", reqs.REQ_SCHEME_PACKAGE, False, "argcomplete", None, None, []),
            (
                "pip_dry_run",
                reqs.REQ_SCHEME_PIP,
                True,
                None,
                None,
                None,
                ["argcomplete"],
            ),
            ("pip", reqs.REQ_SCHEME_PIP, False, None, None, None, ["argcomplete"]),
        ]
    )
    def test_PV_ENV_VNV_320_replace_existing(
        self, name, req_scheme, dry_run, basename, env_name, env_prefix, pip_args
    ):
        filespecs = {
            "requirements.txt": "argcomplete",
            "requirements_dev.txt": "argcomplete",
            "requirements_frozen.txt": "argcomplete == 1.12.3",
            os.path.join("dev", "requirements_build.txt"): "",
            os.path.join("dev", "requirements_dev.txt"): "",
            os.path.join("dev", "requirements_test.txt"): "parameterized",
        }
        with ctx.project("dummy_package", filespecs=filespecs):
            x = env.VenvEnvironment(
                req_scheme,
                pip_args=pip_args,
                basename=basename,
                env_name=env_name,
                env_prefix=env_prefix,
                dry_run=dry_run,
            )
            y = env.VenvEnvironment(
                req_scheme,
                pip_args=pip_args,
                basename=basename,
                env_name=env_name,
                env_prefix=env_prefix,
                dry_run=False,
            )
            if not flags.should_suppress_output():
                y.create()
                x.replace()
            else:
                original_stderrs = []
                with ctx.capture_to_file(y.create) as (_status, _stdout, stderr):
                    original_stderrs.append(stderr)
                with ctx.capture_to_file(x.remove) as (_status, _stdout, stderr):
                    original_stderrs.append(stderr)
                testable_stderrs = [text.lower() for text in original_stderrs]
                for (i, text) in enumerate(testable_stderrs):
                    if "error" in text:
                        print(original_stderrs[i], file=stderr)
                    self.assertNotIn("error", text)
