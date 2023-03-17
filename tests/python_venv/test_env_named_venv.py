"""Provide unit tests for `~python_venv.env.named_env`:py:mod:."""

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


class TestEnv_400_NamedVenvEnvironment(unittest.TestCase):
    def setUp(self):
        self.saved_requirements = reqs.REQUIREMENTS

    def tearDown(self):
        reqs.REQUIREMENTS = self.saved_requirements

    def test_PV_ENV_NMV_000_instantiate_empty(self):
        with self.assertRaises(TypeError) as raised:
            env.NamedVenvEnvironment()
        msg = raised.exception.args[0]
        self.assertTrue("__init__() missing 1 required positional argument" in msg)

    def test_PV_ENV_NMV_001_instantiate_missing_required(self):
        with self.assertRaises(ValueError) as raised:
            env.NamedVenvEnvironment("dummy_req_scheme")
        self.assertEqual(
            raised.exception.args[0],
            "The 'env_prefix' argument is required and must not be None",
        )

    def test_PV_ENV_NMV_002_instantiate_with_required(self):
        x = env.NamedVenvEnvironment("dummy_req_scheme", env_prefix="dummy_env_prefix")
        self.assertEqual(x._env_prefix, "dummy_env_prefix")
        self.assertEqual(x.env_prefix, "dummy_env_prefix")
        self.assertTrue(x.have_env_prefix())

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
        ]
    )
    def test_PV_ENV_NMV_003_instantiate_kwargs(self, name, kwargs, attr, value):
        x = env.NamedVenvEnvironment(
            "dummy_req_scheme", env_prefix="dummy_env_prefix", **kwargs
        )
        self.assertEqual(getattr(x, attr), value)

    def test_PV_ENV_NMV_010_requirements(self):
        dummy_requirements = {"dummy_req_source": ["dummy_requirement"]}
        reqs.REQUIREMENTS = {"dummy_req_scheme": [dummy_requirements]}
        x = env.NamedVenvEnvironment("dummy_req_scheme", env_prefix="dummy_env_prefix")
        self.assertListEqual(x.requirements.requirements, [dummy_requirements])

    def test_PV_ENV_NMV_020_package_name(self):
        x = env.NamedVenvEnvironment("dummy_req_scheme", env_prefix="dummy_env_prefix")
        self.assertEqual(x.package_name, "python_venv")

    @parameterized.parameterized.expand(
        [
            ("default", None, "python-venv"),
            ("specified", "dummy-package", "dummy-package"),
        ]
    )
    def test_PV_ENV_NMV_030_basename(self, name, basename, expected):
        kwargs = {} if basename is None else {"basename": basename}
        x = env.NamedVenvEnvironment(
            "dummy_req_scheme", env_prefix="dummy_env_prefix", **kwargs
        )
        self.assertEqual(x.basename, expected)

    @parameterized.parameterized.expand(
        [
            ("default", reqs.REQ_SCHEME_PLAIN, {}, "python-venv"),
            ("default_dev", reqs.REQ_SCHEME_DEV, {}, "python-venv-dev"),
            ("default_devplus", reqs.REQ_SCHEME_DEVPLUS, {}, "python-venv-dev"),
            (
                "basename",
                reqs.REQ_SCHEME_PLAIN,
                {"basename": "dummy-package"},
                "dummy-package",
            ),
            (
                "basename_dev",
                reqs.REQ_SCHEME_DEV,
                {"basename": "dummy-package"},
                "dummy-package-dev",
            ),
            (
                "basename_devplus",
                reqs.REQ_SCHEME_DEVPLUS,
                {"basename": "dummy-package"},
                "dummy-package-dev",
            ),
            ("specified", "dummy_req_scheme", {"env_name": "dummy-env"}, "dummy-env"),
        ]
    )
    def test_PV_ENV_NMV_040_env_name(self, name, req_scheme, kwargs, expected):
        x = env.NamedVenvEnvironment(
            req_scheme, env_prefix="dummy_env_prefix", **kwargs
        )
        self.assertEqual(x.env_name, expected)

    @parameterized.parameterized.expand(
        [
            ("default", "dummy-basename", None, "dummy-prefix", "dummy-basename"),
            ("specified", "dummy-basename", "dummy-env", "dummy-prefix", "dummy-env"),
        ]
    )
    def test_PV_ENV_NMV_050_env_dir(
        self, name, basename, env_name, env_prefix, expected
    ):
        kwargs = {"env_prefix": env_prefix}
        if basename is not None:
            kwargs["basename"] = basename
        if env_name is not None:
            kwargs["env_name"] = env_name
        x = env.NamedVenvEnvironment(reqs.REQ_SCHEME_PLAIN, **kwargs)
        expected = os.path.join(env_prefix, expected)
        self.assertEqual(x.env_dir, expected)
        self.assertEqual(x.abs_env_dir, os.path.join(os.getcwd(), expected))

    @parameterized.parameterized.expand(
        [
            ("default", "dummy-basename", None, "dummy-prefix", "dummy-basename"),
            ("specified", "dummy-basename", "dummy-env", "dummy-prefix", "dummy-env"),
        ]
    )
    def test_PV_ENV_NMV_051_env_bin_dir(
        self, name, basename, env_name, env_prefix, expected
    ):
        kwargs = {"env_prefix": env_prefix}
        if basename is not None:
            kwargs["basename"] = basename
        if env_name is not None:
            kwargs["env_name"] = env_name
        x = env.NamedVenvEnvironment(reqs.REQ_SCHEME_PLAIN, **kwargs)
        expected = os.path.join(env_prefix, expected, "bin")
        self.assertEqual(x.env_bin_dir, expected)

    @parameterized.parameterized.expand(
        [
            (
                "default",
                "dummy-python",
                "dummy-env",
                "dummy-prefix",
                os.path.join("dummy-prefix", "dummy-env", "bin", "dummy-python"),
            ),
            (
                "with_path",
                os.path.join(os.sep, "usr", "bin", "dummy-python"),
                "dummy-env",
                "dummy-prefix",
                os.path.join("dummy-prefix", "dummy-env", "bin", "dummy-python"),
            ),
        ]
    )
    def test_PV_ENV_NMV_052_env_python(
        self, name, python, env_name, env_prefix, expected
    ):
        kwargs = {"env_prefix": env_prefix, "basename": "dummy-basename"}
        if python is not None:
            kwargs["python"] = python
        if env_name is not None:
            kwargs["env_name"] = env_name
        x = env.NamedVenvEnvironment(reqs.REQ_SCHEME_PLAIN, **kwargs)
        self.assertEqual(x.env_python, expected)

    @parameterized.parameterized.expand(
        [
            ("default", "dummy-basename", None, "dummy-prefix", "dummy-basename"),
            ("specified", "dummy-basename", "dummy-env", "dummy-prefix", "dummy-env"),
        ]
    )
    def test_PV_ENV_NMV_060_env_description(
        self, name, basename, env_name, env_prefix, expected
    ):
        kwargs = {"env_prefix": env_prefix}
        if basename is not None:
            kwargs["basename"] = basename
        if env_name is not None:
            kwargs["env_name"] = env_name
        if env_prefix is not None:
            kwargs["env_prefix"] = env_prefix
        x = env.NamedVenvEnvironment(reqs.REQ_SCHEME_PLAIN, **kwargs)
        x.env_description
        self.assertTrue(x.env_description.endswith(os.path.join(env_prefix, expected)))

    @parameterized.parameterized.expand(
        [
            ("dry_run_text", "[DRY-RUN]"),
            (
                "create_msg",
                " ".join(
                    [
                        "Creating Python venv at",
                        os.path.join("dummy-prefix", "dummy-env"),
                    ]
                ),
            ),
            (
                "create_venv",
                " ".join(
                    ["+ python3 -m venv", os.path.join("dummy-prefix", "dummy-env")]
                ),
            ),
            ("install_msg", "Installing dummy_req_scheme requirements"),
            (
                "pip_install",
                "+ {python} -m pip install -r dummy_requirements.txt".format(
                    python=os.path.join("dummy-prefix", "dummy-env", "bin", "python3")
                ),
            ),
            ("success", "==> Done."),
        ]
    )
    def test_PV_ENV_NMV_100_create_dry_run(self, name, expected_text):
        dummy_requirements = {const.FROM_FILES: ["dummy_requirements.txt"]}
        reqs.REQUIREMENTS = {"dummy_req_scheme": [dummy_requirements]}
        x = env.NamedVenvEnvironment(
            "dummy_req_scheme",
            env_prefix="dummy-prefix",
            dry_run=True,
            basename="dummy-basename",
            env_name="dummy-env",
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
            (
                "remove_msg",
                " ".join(
                    [
                        "Removing Python venv at",
                        os.path.join("dummy-prefix", "dummy-env"),
                    ]
                ),
            ),
        ]
    )
    def test_PV_ENV_NMV_200_remove_dry_run(self, name, expected_text):
        x = env.NamedVenvEnvironment(
            reqs.REQ_SCHEME_PLAIN,
            env_prefix="dummy-prefix",
            dry_run=True,
            basename="dummy-basename",
            env_name="dummy-env",
        )
        with ctx.capture(x.remove) as (status, _stdout, stderr):
            self.assertTrue(expected_text in stderr)

    @parameterized.parameterized.expand(
        [
            ("dry_run_text", "[DRY-RUN]"),
            (
                "replace_msg",
                " ".join(
                    [
                        "Replacing Python venv at",
                        os.path.join("dummy-prefix", "dummy-env"),
                    ]
                ),
            ),
            (
                "remove_msg",
                " ".join(
                    [
                        "Removing Python venv at",
                        os.path.join("dummy-prefix", "dummy-env"),
                    ]
                ),
            ),
            (
                "create_msg",
                " ".join(
                    [
                        "Creating Python venv at",
                        os.path.join("dummy-prefix", "dummy-env"),
                    ]
                ),
            ),
            ("success", "==> Done."),
        ]
    )
    def test_PV_ENV_NMV_300_replace_dry_run(self, name, expected_text):
        dummy_requirements = {const.FROM_FILES: ["dummy_requirements.txt"]}
        reqs.REQUIREMENTS = {"dummy_req_scheme": [dummy_requirements]}
        x = env.NamedVenvEnvironment(
            "dummy_req_scheme",
            env_prefix="dummy-prefix",
            dry_run=True,
            basename="dummy-basename",
            env_name="dummy-env",
            ignore_preflight_checks=True,
        )
        with ctx.capture_to_file(x.replace) as (status, _stdout, stderr):
            self.assertTrue(expected_text in stderr)


########################################


class TestEnv_410_NamedVenvCreate(unittest.TestCase):
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
                "dummy-env",
                [],
            ),
            ("plain_env_name", reqs.REQ_SCHEME_PLAIN, False, None, "dummy-env", []),
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
    def test_PV_ENV_NMV_110_create(
        self, name, req_scheme, dry_run, basename, env_name, pip_args
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
            x = env.NamedVenvEnvironment(
                req_scheme,
                env_prefix="dummy-prefix",
                basename=basename,
                env_name=env_name,
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
            ("plain_dry_run", reqs.REQ_SCHEME_PLAIN, True, None, None, []),
            ("plain", reqs.REQ_SCHEME_PLAIN, False, None, None, []),
            (
                "plain_dry_run_env_name",
                reqs.REQ_SCHEME_PLAIN,
                True,
                None,
                "dummy-env",
                [],
            ),
            ("plain_env_name", reqs.REQ_SCHEME_PLAIN, False, None, "dummy-env", []),
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
            ("package_dry_run", reqs.REQ_SCHEME_PACKAGE, True, None, None, []),
            ("package", reqs.REQ_SCHEME_PACKAGE, False, None, None, []),
            ("pip_dry_run", reqs.REQ_SCHEME_PIP, True, None, None, ["argcomplete"]),
            ("pip", reqs.REQ_SCHEME_PIP, False, None, None, ["argcomplete"]),
        ]
    )
    def test_PV_ENV_NMV_111_create_no_setup(
        self, name, req_scheme, dry_run, basename, env_name, pip_args
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
        with ctx.project(
            "dummy_package", dirs=dirs, filespecs=filespecs, omit_setup=True
        ):
            with ctx.capture_output_to_file():
                x = env.NamedVenvEnvironment(
                    req_scheme,
                    env_prefix="dummy-prefix",
                    basename=basename,
                    env_name=env_name,
                    dry_run=dry_run,
                )
                with self.assertRaises(subprocess.CalledProcessError):
                    x.create()

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
    def test_PV_ENV_NMV_120_create_missing_reqs(
        self, name, req_scheme, dry_run, basename, env_name
    ):
        with ctx.project("dummy_package"):
            x = env.NamedVenvEnvironment(
                req_scheme,
                env_prefix="dummy-prefix",
                basename=basename,
                env_name=env_name,
                dry_run=dry_run,
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
                "dummy-env",
                True,
            ),
            ("plain_env_name", reqs.REQ_SCHEME_PLAIN, False, "dummy-env", True),
        ]
    )
    def test_PV_ENV_NMV_130_create_duplicate(
        self, name, req_scheme, dry_run, env_name, should_raise
    ):
        env_prefix = "dummy-prefix"
        dirs = [env_prefix]
        filespecs = {
            "requirements.txt": "argcomplete",
            "requirements_dev.txt": "argcomplete",
            "requirements_frozen.txt": "argcomplete == 1.12.3",
            os.path.join("dev", "requirements_build.txt"): "",
            os.path.join("dev", "requirements_dev.txt"): "",
            os.path.join("dev", "requirements_test.txt"): "parameterized",
        }
        with ctx.project("dummy_package", dirs=dirs, filespecs=filespecs):
            x = env.NamedVenvEnvironment(
                req_scheme, env_prefix=env_prefix, env_name=env_name, dry_run=False
            )
            if not flags.should_suppress_output():
                x.create()
            else:
                with ctx.capture_to_file(x.create) as (_status, _stdout, _stderr):
                    pass
            x = env.NamedVenvEnvironment(
                req_scheme, env_prefix=env_prefix, env_name=env_name, dry_run=dry_run
            )
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


class TestEnv_420_NamedVenvRemove(unittest.TestCase):
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
                "dummy-env",
                [],
            ),
            (
                "plain_env_name",
                reqs.REQ_SCHEME_PLAIN,
                False,
                None,
                "dummy-env",
                [],
            ),
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
            (
                "package_dry_run",
                reqs.REQ_SCHEME_PACKAGE,
                True,
                "argcomplete",
                None,
                [],
            ),
            ("package", reqs.REQ_SCHEME_PACKAGE, False, "argcomplete", None, []),
            (
                "pip_dry_run",
                reqs.REQ_SCHEME_PIP,
                True,
                None,
                None,
                ["argcomplete"],
            ),
            ("pip", reqs.REQ_SCHEME_PIP, False, None, None, ["argcomplete"]),
        ]
    )
    def test_PV_ENV_NMV_210_remove(
        self, name, req_scheme, dry_run, basename, env_name, pip_args
    ):
        env_prefix = "dummy-prefix"
        dirs = [env_prefix]
        filespecs = {
            "requirements.txt": "argcomplete",
            "requirements_dev.txt": "argcomplete",
            "requirements_frozen.txt": "argcomplete == 1.12.3",
            os.path.join("dev", "requirements_build.txt"): "",
            os.path.join("dev", "requirements_dev.txt"): "",
            os.path.join("dev", "requirements_test.txt"): "parameterized",
        }
        with ctx.project("dummy_package", dirs=dirs, filespecs=filespecs):
            x = env.NamedVenvEnvironment(
                req_scheme,
                pip_args=pip_args,
                basename=basename,
                env_name=env_name,
                env_prefix=env_prefix,
                dry_run=dry_run,
            )
            y = env.NamedVenvEnvironment(
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
                for i, text in enumerate(testable_stderrs):
                    if "error" in text:
                        print(original_stderrs[i], file=stderr)
                    self.assertNotIn("error", text)


########################################


class TestEnv_430_NamedVenvReplace(unittest.TestCase):
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
                "dummy-env",
                [],
            ),
            (
                "plain_env_name",
                reqs.REQ_SCHEME_PLAIN,
                False,
                None,
                "dummy-env",
                [],
            ),
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
            (
                "package_dry_run",
                reqs.REQ_SCHEME_PACKAGE,
                True,
                "argcomplete",
                None,
                [],
            ),
            ("package", reqs.REQ_SCHEME_PACKAGE, False, "argcomplete", None, []),
            (
                "pip_dry_run",
                reqs.REQ_SCHEME_PIP,
                True,
                None,
                None,
                ["argcomplete"],
            ),
            ("pip", reqs.REQ_SCHEME_PIP, False, None, None, ["argcomplete"]),
        ]
    )
    def test_PV_ENV_NMV_310_replace_nonexistent(
        self, name, req_scheme, dry_run, basename, env_name, pip_args
    ):
        env_prefix = "dummy-prefix"
        dirs = [env_prefix]
        filespecs = {
            "requirements.txt": "argcomplete",
            "requirements_dev.txt": "argcomplete",
            "requirements_frozen.txt": "argcomplete == 1.12.3",
            os.path.join("dev", "requirements_build.txt"): "",
            os.path.join("dev", "requirements_dev.txt"): "",
            os.path.join("dev", "requirements_test.txt"): "parameterized",
        }
        with ctx.project("dummy_package", dirs=dirs, filespecs=filespecs):
            x = env.NamedVenvEnvironment(
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
                for i, text in enumerate(testable_stderrs):
                    if "error" in text:
                        print(original_stderrs[i], file=stderr)
                    self.assertNotIn("error", text)

    @parameterized.parameterized.expand(
        [
            ("plain_dry_run", reqs.REQ_SCHEME_PLAIN, True, None, None, []),
            ("plain", reqs.REQ_SCHEME_PLAIN, False, None, None, []),
            (
                "plain_dry_run_env_name",
                reqs.REQ_SCHEME_PLAIN,
                True,
                None,
                "dummy-env",
                [],
            ),
            (
                "plain_env_name",
                reqs.REQ_SCHEME_PLAIN,
                False,
                None,
                "dummy-env",
                [],
            ),
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
            (
                "package_dry_run",
                reqs.REQ_SCHEME_PACKAGE,
                True,
                "argcomplete",
                None,
                [],
            ),
            ("package", reqs.REQ_SCHEME_PACKAGE, False, "argcomplete", None, []),
            (
                "pip_dry_run",
                reqs.REQ_SCHEME_PIP,
                True,
                None,
                None,
                ["argcomplete"],
            ),
            ("pip", reqs.REQ_SCHEME_PIP, False, None, None, ["argcomplete"]),
        ]
    )
    def test_PV_ENV_NMV_320_replace_existing(
        self, name, req_scheme, dry_run, basename, env_name, pip_args
    ):
        env_prefix = "dummy-prefix"
        dirs = [env_prefix]
        filespecs = {
            "requirements.txt": "argcomplete",
            "requirements_dev.txt": "argcomplete",
            "requirements_frozen.txt": "argcomplete == 1.12.3",
            os.path.join("dev", "requirements_build.txt"): "",
            os.path.join("dev", "requirements_dev.txt"): "",
            os.path.join("dev", "requirements_test.txt"): "parameterized",
        }
        with ctx.project("dummy_package", dirs=dirs, filespecs=filespecs):
            x = env.NamedVenvEnvironment(
                req_scheme,
                pip_args=pip_args,
                basename=basename,
                env_name=env_name,
                env_prefix=env_prefix,
                dry_run=dry_run,
            )
            y = env.NamedVenvEnvironment(
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
                for i, text in enumerate(testable_stderrs):
                    if "error" in text:
                        print(original_stderrs[i], file=stderr)
                    self.assertNotIn("error", text)
