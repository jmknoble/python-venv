"""Provide unit tests for `~python_venv.env.pyenv`:py:mod:."""

import os
import os.path
import random
import subprocess
import unittest

import parameterized  # https://pypi.org/project/parameterized/

from python_venv import const, env
from python_venv import exceptions as exc
from python_venv import reqs
from tests.python_venv import contextmgr as ctx
from tests.python_venv import flags

########################################


@unittest.skipUnless(flags.should_run_pyenv_tests(), flags.SKIP_PYENV_MESSAGE)
class TestEnv_200_PyenvEnvironment(unittest.TestCase):
    def setUp(self):
        self.saved_requirements = reqs.REQUIREMENTS

    def tearDown(self):
        reqs.REQUIREMENTS = self.saved_requirements

    def test_PV_ENV_PYNV_000_instantiate_empty(self):
        with self.assertRaises(TypeError) as raised:
            env.PyenvEnvironment()
        msg = raised.exception.args[0]
        self.assertIn("__init__() missing 1 required positional argument", msg)

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
    def test_PV_ENV_PYNV_002_instantiate_kwargs(self, name, kwargs, attr, value):
        x = env.PyenvEnvironment("dummy_req_scheme", **kwargs)
        self.assertEqual(getattr(x, attr), value)

    def test_PV_ENV_PYNV_010_requirements(self):
        dummy_requirements = {"dummy_req_source": ["dummy_requirement"]}
        reqs.REQUIREMENTS = {"dummy_req_scheme": [dummy_requirements]}
        x = env.PyenvEnvironment("dummy_req_scheme")
        self.assertListEqual(x.requirements.requirements, [dummy_requirements])

    def test_PV_ENV_PYNV_020_package_name(self):
        x = env.PyenvEnvironment("dummy_req_scheme")
        self.assertEqual(x.package_name, "python_venv")

    @parameterized.parameterized.expand(
        [
            ("default", None, "python-venv"),
            ("specified", "dummy-package", "dummy-package"),
        ]
    )
    def test_PV_ENV_PYNV_030_basename(self, name, basename, expected):
        kwargs = {} if basename is None else {"basename": basename}
        x = env.PyenvEnvironment("dummy_req_scheme", **kwargs)
        self.assertEqual(x.basename, expected)

    @parameterized.parameterized.expand(
        [
            ("default", reqs.REQ_SCHEME_PLAIN, {}, "python-venv"),
            ("default_dev", reqs.REQ_SCHEME_DEV, {}, "python-venv-dev"),
            ("default_devplus", reqs.REQ_SCHEME_DEVPLUS, {}, "python-venv-dev"),
            (
                "default_prefix",
                reqs.REQ_SCHEME_PLAIN,
                {"env_prefix": "dummy-prefix-"},
                "dummy-prefix-python-venv",
            ),
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
            (
                "basename_prefix",
                reqs.REQ_SCHEME_PLAIN,
                {"basename": "dummy-package", "env_prefix": "dummy-prefix-"},
                "dummy-prefix-dummy-package",
            ),
            ("specified", "dummy_req_scheme", {"env_name": "dummy-env"}, "dummy-env"),
            (
                "specified_prefix",
                "dummy_req_scheme",
                {"env_name": "dummy-env", "env_prefix": "dummy-prefix-"},
                "dummy-env",
            ),
        ]
    )
    def test_PV_ENV_PYNV_040_env_name(self, name, req_scheme, kwargs, expected):
        x = env.PyenvEnvironment(req_scheme, **kwargs)
        self.assertEqual(x.env_name, expected)

    @parameterized.parameterized.expand(
        [
            ("default", "dummy-basename", None, None, "<ENV_DIR>"),
            ("specified", None, "dummy-env", None, "<ENV_DIR>"),
            ("with_prefix", "dummy-basename", None, "dummy-prefix", "<ENV_DIR>"),
            (
                "specified_with_prefix",
                "dummy-basename",
                "dummy-env",
                "dummy-prefix",
                "<ENV_DIR>",
            ),
        ]
    )
    def test_PV_ENV_PYNV_050_env_dir_dry_run(
        self, name, basename, env_name, env_prefix, expected
    ):
        kwargs = {}
        if basename is not None:
            kwargs["basename"] = basename
        if env_name is not None:
            kwargs["env_name"] = env_name
        if env_prefix is not None:
            kwargs["env_prefix"] = env_prefix
        x = env.PyenvEnvironment(reqs.REQ_SCHEME_PLAIN, dry_run=True, **kwargs)
        self.assertEqual(x.env_dir, expected)

    @parameterized.parameterized.expand(
        [
            (
                "default",
                "dummy-basename",
                None,
                None,
                os.path.join(os.getcwd(), "<ENV_DIR>"),
            ),
            (
                "specified",
                None,
                "dummy-env",
                None,
                os.path.join(os.getcwd(), "<ENV_DIR>"),
            ),
            (
                "with_prefix",
                "dummy-basename",
                None,
                "dummy-prefix",
                os.path.join(os.getcwd(), "<ENV_DIR>"),
            ),
            (
                "specified_with_prefix",
                "dummy-basename",
                "dummy-env",
                "dummy-prefix",
                os.path.join(os.getcwd(), "<ENV_DIR>"),
            ),
        ]
    )
    def test_PV_ENV_PYNV_051_abs_env_dir_dry_run(
        self, name, basename, env_name, env_prefix, expected
    ):
        kwargs = {}
        if basename is not None:
            kwargs["basename"] = basename
        if env_name is not None:
            kwargs["env_name"] = env_name
        if env_prefix is not None:
            kwargs["env_prefix"] = env_prefix
        x = env.PyenvEnvironment(reqs.REQ_SCHEME_PLAIN, dry_run=True, **kwargs)
        self.assertEqual(x.abs_env_dir, expected)

    @parameterized.parameterized.expand(
        [
            ("specified", "dummy-env", "dummy-env"),
        ]
    )
    def test_PV_ENV_PYNV_060_env_description(self, name, env_name, expected):
        kwargs = {} if env_name is None else {"env_name": env_name}
        x = env.PyenvEnvironment("dummy_req_scheme", **kwargs)
        x.env_description
        self.assertTrue(x.env_description.endswith(expected))

    @parameterized.parameterized.expand(
        [
            ("dry_run_text", {}, "[DRY-RUN]"),
            ("create_msg", {}, "Creating pyenv environment dummy-package"),
            ("create_venv", {}, "+ pyenv virtualenv"),
            ("install_msg", {}, "Installing dummy_req_scheme requirements"),
            (
                "pip_install",
                {},
                "+ <ENV_DIR>/bin/python3 -m pip install -r dummy_requirements.txt",
            ),
            ("success", {}, "==> Done."),
        ]
    )
    def test_PV_ENV_PYNV_100_create_dry_run(self, name, kwargs, expected_text):
        dummy_requirements = {const.FROM_FILES: ["dummy_requirements.txt"]}
        reqs.REQUIREMENTS = {"dummy_req_scheme": [dummy_requirements]}
        x = env.PyenvEnvironment(
            "dummy_req_scheme",
            dry_run=True,
            basename="dummy-package",
            ignore_preflight_checks=True,
            **kwargs,
        )
        with ctx.capture(x.create) as (
            status,
            _stdout,
            stderr,
        ):
            self.assertTrue(expected_text in stderr)

    @parameterized.parameterized.expand(
        [
            ("dry_run_text", "[DRY-RUN]"),
            ("remove_msg", "Removing pyenv environment dummy-package"),
        ]
    )
    def test_PV_ENV_PYNV_200_remove_dry_run(self, name, expected_text):
        x = env.PyenvEnvironment(
            reqs.REQ_SCHEME_PLAIN, dry_run=True, basename="dummy-package"
        )
        with ctx.capture(x.remove) as (status, _stdout, stderr):
            self.assertTrue(expected_text in stderr)

    @parameterized.parameterized.expand(
        [
            ("dry_run_text", "[DRY-RUN]"),
            ("replace_msg", "Replacing pyenv environment dummy-package"),
            ("remove_msg", "Removing pyenv environment dummy-package"),
            ("create_msg", "Creating pyenv environment dummy-package"),
            ("success", "==> Done."),
        ]
    )
    def test_PV_ENV_PYNV_300_replace_dry_run(self, name, expected_text):
        dummy_requirements = {const.FROM_FILES: ["dummy_requirements.txt"]}
        reqs.REQUIREMENTS = {"dummy_req_scheme": [dummy_requirements]}
        x = env.PyenvEnvironment(
            "dummy_req_scheme",
            dry_run=True,
            basename="dummy-package",
            ignore_preflight_checks=True,
        )
        with ctx.capture(x.replace) as (status, _stdout, stderr):
            self.assertTrue(expected_text in stderr)


########################################


@unittest.skipUnless(flags.should_run_pyenv_tests(), flags.SKIP_PYENV_MESSAGE)
class TestEnv_210_PyenvCreate(unittest.TestCase):
    def setUp(self):
        self.env_name = None
        try:
            self.choices
        except AttributeError:
            self.choices = (
                [chr(x) for x in range(ord("0"), ord("9") + 1)]
                + [chr(x) for x in range(ord("A"), ord("Z") + 1)]
                + [chr(x) for x in range(ord("a"), ord("z") + 1)]
            )
        # Random prefix for environments is required
        # since pyenv virtualenv doesn't give us a choice
        # to place an environment somewhere specific.
        self.env_prefix = "".join(random.choice(self.choices) for x in range(10)) + "-"

    def tearDown(self):
        if self.env_name is not None:
            # remove pyenv virtual environment
            subprocess.call(
                ["pyenv", "virtualenv-delete", "-f", self.env_name],
                stderr=subprocess.DEVNULL,
            )
            self.env_name = None

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
    def test_PV_ENV_PYNV_110_create(
        self, name, req_scheme, dry_run, basename, env_name, pip_args
    ):
        env_prefix = self.env_prefix
        if env_name:
            env_name = env_prefix + env_name
        dirs = []
        filespecs = {
            "requirements.txt": "argcomplete",
            "requirements_dev.txt": "argcomplete",
            "requirements_frozen.txt": "argcomplete == 1.12.3",
            os.path.join("dev", "requirements_build.txt"): "",
            os.path.join("dev", "requirements_dev.txt"): "",
            os.path.join("dev", "requirements_test.txt"): "parameterized",
        }
        with ctx.project("dummy_package", dirs=dirs, filespecs=filespecs):
            x = env.PyenvEnvironment(
                req_scheme,
                pip_args=pip_args,
                basename=basename,
                env_name=env_name,
                env_prefix=env_prefix,
                dry_run=dry_run,
                force=True,
            )
            self.env_name = x.env_name
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
    def test_PV_ENV_PYNV_120_create_missing_reqs(
        self, name, req_scheme, dry_run, basename, env_name
    ):
        env_prefix = self.env_prefix
        if env_name:
            env_name = env_prefix + env_name
        dirs = []
        with ctx.project("dummy_package", dirs=dirs):
            x = env.PyenvEnvironment(
                req_scheme,
                basename=basename,
                env_name=env_name,
                env_prefix=env_prefix,
                dry_run=dry_run,
                force=True,
            )
            self.env_name = x.env_name
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
    def test_PV_ENV_PYNV_130_create_duplicate(
        self, name, req_scheme, dry_run, env_name, should_raise
    ):
        env_prefix = self.env_prefix
        if env_name:
            env_name = env_prefix + env_name
        dirs = []
        filespecs = {
            "requirements.txt": "argcomplete",
            "requirements_dev.txt": "argcomplete",
            "requirements_frozen.txt": "argcomplete == 1.12.3",
            os.path.join("dev", "requirements_build.txt"): "",
            os.path.join("dev", "requirements_dev.txt"): "",
            os.path.join("dev", "requirements_test.txt"): "parameterized",
        }
        with ctx.project("dummy_package", dirs=dirs, filespecs=filespecs):
            x = env.PyenvEnvironment(
                req_scheme,
                env_name=env_name,
                env_prefix=env_prefix,
                dry_run=False,
                force=True,
            )
            self.env_name = x.env_name
            if not flags.should_suppress_output():
                x.create()
            else:
                with ctx.capture_to_file(x.create) as (_status, _stdout, _stderr):
                    pass
            x = env.PyenvEnvironment(
                req_scheme,
                env_name=env_name,
                env_prefix=env_prefix,
                dry_run=dry_run,
                force=True,
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


@unittest.skipUnless(flags.should_run_pyenv_tests(), flags.SKIP_PYENV_MESSAGE)
class TestEnv_220_PyenvRemove(unittest.TestCase):
    def setUp(self):
        self.env_name = None
        try:
            self.choices
        except AttributeError:
            self.choices = (
                [chr(x) for x in range(ord("0"), ord("9") + 1)]
                + [chr(x) for x in range(ord("A"), ord("Z") + 1)]
                + [chr(x) for x in range(ord("a"), ord("z") + 1)]
            )
        # Random prefix for environments is required
        # since pyenv virtualenv doesn't give us a choice
        # to place an environment somewhere specific.
        self.env_prefix = "".join(random.choice(self.choices) for x in range(10)) + "-"

    def tearDown(self):
        if self.env_name is not None:
            # remove pyenv virtual environment
            subprocess.call(
                ["pyenv", "virtualenv-delete", "-f", self.env_name],
                stderr=subprocess.DEVNULL,
            )
            self.env_name = None

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
    def test_PV_ENV_PYNV_210_remove(
        self, name, req_scheme, dry_run, basename, env_name, pip_args
    ):
        env_prefix = self.env_prefix
        if env_name:
            env_name = env_prefix + env_name
        dirs = []
        filespecs = {
            "requirements.txt": "argcomplete",
            "requirements_dev.txt": "argcomplete",
            "requirements_frozen.txt": "argcomplete == 1.12.3",
            os.path.join("dev", "requirements_build.txt"): "",
            os.path.join("dev", "requirements_dev.txt"): "",
            os.path.join("dev", "requirements_test.txt"): "parameterized",
        }
        with ctx.project("dummy_package", dirs=dirs, filespecs=filespecs):
            x = env.PyenvEnvironment(
                req_scheme,
                pip_args=pip_args,
                basename=basename,
                env_name=env_name,
                env_prefix=env_prefix,
                dry_run=dry_run,
                force=True,
            )
            y = env.PyenvEnvironment(
                req_scheme,
                pip_args=pip_args,
                basename=basename,
                env_name=env_name,
                env_prefix=env_prefix,
                dry_run=False,
                force=True,
            )
            self.env_name = y.env_name
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


@unittest.skipUnless(flags.should_run_pyenv_tests(), flags.SKIP_PYENV_MESSAGE)
class TestEnv_230_PyenvReplace(unittest.TestCase):
    def setUp(self):
        self.env_name = None
        try:
            self.choices
        except AttributeError:
            self.choices = (
                [chr(x) for x in range(ord("0"), ord("9") + 1)]
                + [chr(x) for x in range(ord("A"), ord("Z") + 1)]
                + [chr(x) for x in range(ord("a"), ord("z") + 1)]
            )
        # Random prefix for environments is required
        # since pyenv virtualenv doesn't give us a choice
        # to place an environment somewhere specific.
        self.env_prefix = "".join(random.choice(self.choices) for x in range(10)) + "-"

    def tearDown(self):
        if self.env_name is not None:
            # remove pyenv virtual environment
            subprocess.call(
                ["pyenv", "virtualenv-delete", "-f", self.env_name],
                stderr=subprocess.DEVNULL,
            )
            self.env_name = None

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
    def test_PV_ENV_PYNV_310_replace_nonexistent(
        self, name, req_scheme, dry_run, basename, env_name, pip_args
    ):
        env_prefix = self.env_prefix
        if env_name:
            env_name = env_prefix + env_name
        dirs = []
        filespecs = {
            "requirements.txt": "argcomplete",
            "requirements_dev.txt": "argcomplete",
            "requirements_frozen.txt": "argcomplete == 1.12.3",
            os.path.join("dev", "requirements_build.txt"): "",
            os.path.join("dev", "requirements_dev.txt"): "",
            os.path.join("dev", "requirements_test.txt"): "parameterized",
        }
        with ctx.project("dummy_package", dirs=dirs, filespecs=filespecs):
            x = env.PyenvEnvironment(
                req_scheme,
                pip_args=pip_args,
                basename=basename,
                env_name=env_name,
                env_prefix=env_prefix,
                dry_run=dry_run,
                force=True,
            )
            self.env_name = x.env_name
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
    def test_PV_ENV_PYNV_320_replace_existing(
        self, name, req_scheme, dry_run, basename, env_name, pip_args
    ):
        env_prefix = self.env_prefix
        if env_name:
            env_name = env_prefix + env_name
        dirs = []
        filespecs = {
            "requirements.txt": "argcomplete",
            "requirements_dev.txt": "argcomplete",
            "requirements_frozen.txt": "argcomplete == 1.12.3",
            os.path.join("dev", "requirements_build.txt"): "",
            os.path.join("dev", "requirements_dev.txt"): "",
            os.path.join("dev", "requirements_test.txt"): "parameterized",
        }
        with ctx.project("dummy_package", dirs=dirs, filespecs=filespecs):
            x = env.PyenvEnvironment(
                req_scheme,
                pip_args=pip_args,
                basename=basename,
                env_name=env_name,
                env_prefix=env_prefix,
                dry_run=dry_run,
                force=True,
            )
            y = env.PyenvEnvironment(
                req_scheme,
                pip_args=pip_args,
                basename=basename,
                env_name=env_name,
                env_prefix=env_prefix,
                dry_run=False,
                force=True,
            )
            self.env_name = y.env_name
            if not flags.should_suppress_output():
                y.create()
                x.replace()
            else:
                original_stderrs = []
                with ctx.capture_to_file(y.create) as (_status, _stdout, stderr):
                    original_stderrs.append(stderr)
                with ctx.capture_to_file(x.replace) as (_status, _stdout, stderr):
                    original_stderrs.append(stderr)
                testable_stderrs = [text.lower() for text in original_stderrs]
                for i, text in enumerate(testable_stderrs):
                    if "error" in text:
                        print(original_stderrs[i], file=stderr)
                    self.assertNotIn("error", text)
