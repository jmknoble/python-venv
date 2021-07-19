"""Provide unit tests for `~python_venv.env`:py:mod:."""

import os
import os.path
import subprocess
import unittest

import parameterized  # https://pypi.org/project/parameterized/

from python_venv import env
from python_venv import exceptions as exc
from python_venv import reqs
from tests.python_venv import contextmgr as ctx

########################################


HERE = os.getcwd()

FLAG_TEST_WITHOUT_CONDA = "TEST_WITHOUT_CONDA.tmp"
FLAG_TEST_WITH_LONG_RUNNING = "TEST_WITH_LONG_RUNNING.tmp"
FLAG_TEST_WITH_OUTPUT = "TEST_WITH_OUTPUT.tmp"

SKIP_CONDA_MESSAGE = "requires conda"
SKIP_LONG_RUNNING_MESSAGE = (
    f"takes a long time (touch {FLAG_TEST_WITH_LONG_RUNNING} to run anyway)"
)


def _have_conda():
    try:
        subprocess.call(
            ["conda", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
    except FileNotFoundError:
        return False
    return True


def _should_run_conda_tests():
    return _have_conda and not os.path.exists(
        os.path.join(HERE, FLAG_TEST_WITHOUT_CONDA)
    )


def _should_run_long_tests():
    return os.path.exists(os.path.join(HERE, FLAG_TEST_WITH_LONG_RUNNING))


def _should_suppress_output():
    return not os.path.exists(os.path.join(HERE, FLAG_TEST_WITH_OUTPUT))


########################################
# Tests


class TestEnv_000_General(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_PV_ENV_000_symbols_exist(self):
        _ = env.PYTHON
        _ = env.CONDA
        _ = env.VENV_DIR
        _ = env.DEV_SUFFIX


class TestEnv_010_BaseVirtualEnvironment(unittest.TestCase):
    def setUp(self):
        self.saved_requirements = reqs.REQUIREMENTS

    def tearDown(self):
        reqs.REQUIREMENTS = self.saved_requirements

    def test_PV_ENV_BAS_000_instantiate_empty(self):
        with self.assertRaises(TypeError) as raised:
            env.BaseVirtualEnvironment()
        msg = raised.exception.args[0]
        self.assertTrue(
            msg.startswith("__init__() missing 1 required positional argument")
        )

    def test_PV_ENV_BAS_001_instantiate(self):
        x = env.BaseVirtualEnvironment("dummy_req_scheme")
        self.assertEqual(x.req_scheme, "dummy_req_scheme")

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
    def test_PV_ENV_BAS_002_instantiate_kwargs(self, name, kwargs, attr, value):
        x = env.BaseVirtualEnvironment("dummy_req_scheme", **kwargs)
        self.assertEqual(getattr(x, attr), value)

    def test_PV_ENV_BAS_010_requirements(self):
        dummy_requirements = {"dummy_req_source": ["dummy_value"]}
        reqs.REQUIREMENTS = {"dummy_req_scheme": dummy_requirements}
        x = env.BaseVirtualEnvironment("dummy_req_scheme")
        self.assertDictEqual(x.requirements, dummy_requirements)

    def test_PV_ENV_BAS_020_package_name(self):
        x = env.BaseVirtualEnvironment("dummy_req_scheme")
        self.assertEqual(x.package_name, "python_venv")

    @parameterized.parameterized.expand(
        [
            ("default", None, "python-venv"),
            ("specified", "dummy-package", "dummy-package"),
        ]
    )
    def test_PV_ENV_BAS_030_basename(self, name, basename, expected):
        kwargs = {} if basename is None else {"basename": basename}
        x = env.BaseVirtualEnvironment("dummy_req_scheme", **kwargs)
        self.assertEqual(x.basename, expected)

    def test_PV_ENV_BAS_040_abstract_env_name(self):
        x = env.BaseVirtualEnvironment("dummy_req_scheme")
        with self.assertRaises(NotImplementedError):
            x.env_name

    @parameterized.parameterized.expand(
        [
            ("default", None, ""),
            ("specified", "dummy-prefix", "dummy-prefix"),
        ]
    )
    def test_PV_ENV_BAS_045_env_prefix(self, name, env_prefix, expected):
        kwargs = {} if env_prefix is None else {"env_prefix": env_prefix}
        x = env.BaseVirtualEnvironment("dummy_req_scheme", **kwargs)
        self.assertEqual(x.env_prefix, expected)

    def test_PV_ENV_BAS_050_abstract_env_dir(self):
        x = env.BaseVirtualEnvironment("dummy_req_scheme")
        with self.assertRaises(NotImplementedError):
            x.env_dir

    def test_PV_ENV_BAS_055_abstract_abs_env_dir(self):
        x = env.BaseVirtualEnvironment("dummy_req_scheme")
        with self.assertRaises(NotImplementedError):
            x.abs_env_dir

    def test_PV_ENV_BAS_060_abstract_env_description(self):
        x = env.BaseVirtualEnvironment("dummy_req_scheme")
        with self.assertRaises(NotImplementedError):
            x.env_description

    def test_PV_ENV_BAS_100_abstract_create(self):
        x = env.BaseVirtualEnvironment("dummy_req_scheme")
        with self.assertRaises(NotImplementedError):
            x.create()

    def test_PV_ENV_BAS_200_abstract_remove(self):
        x = env.BaseVirtualEnvironment("dummy_req_scheme")
        with self.assertRaises(NotImplementedError):
            x.remove()


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
        reqs.REQUIREMENTS = {"dummy_req_scheme": dummy_requirements}
        x = env.VenvEnvironment("dummy_req_scheme")
        self.assertDictEqual(x.requirements, dummy_requirements)

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
        dummy_requirements = {reqs.FROM_FILES: ["dummy_requirements.txt"]}
        reqs.REQUIREMENTS = {"dummy_req_scheme": dummy_requirements}
        x = env.VenvEnvironment(
            "dummy_req_scheme",
            dry_run=True,
            env_name=".dummy-venv",
            ignore_preflight_checks=True,
        )
        with ctx.capture(x.create, check_preexisting=False) as (
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
        dummy_requirements = {reqs.FROM_FILES: ["dummy_requirements.txt"]}
        reqs.REQUIREMENTS = {"dummy_req_scheme": dummy_requirements}
        x = env.VenvEnvironment(
            "dummy_req_scheme",
            dry_run=True,
            env_name=".dummy-venv",
            ignore_preflight_checks=True,
        )
        with ctx.capture(x.replace) as (status, _stdout, stderr):
            self.assertTrue(expected_text in stderr)


########################################


class TestEnv_110_VenvCreate(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    @parameterized.parameterized.expand(
        [
            ("plain_dry_run", reqs.REQ_SCHEME_PLAIN, True, None, None),
            ("plain", reqs.REQ_SCHEME_PLAIN, False, None, None),
            (
                "plain_dry_run_env_name",
                reqs.REQ_SCHEME_PLAIN,
                True,
                None,
                ".dummy-venv",
            ),
            ("plain_env_name", reqs.REQ_SCHEME_PLAIN, False, None, ".dummy-venv"),
            ("dev_dry_run", reqs.REQ_SCHEME_DEV, True, None, None),
            ("dev", reqs.REQ_SCHEME_DEV, False, None, None),
            ("frozen_dry_run", reqs.REQ_SCHEME_FROZEN, True, None, None),
            ("frozen", reqs.REQ_SCHEME_FROZEN, False, None, None),
            ("source_dry_run", reqs.REQ_SCHEME_SOURCE, True, None, None),
            ("source", reqs.REQ_SCHEME_SOURCE, False, None, None),
            ("package_dry_run", reqs.REQ_SCHEME_PACKAGE, True, "argcomplete", None),
            ("package", reqs.REQ_SCHEME_PACKAGE, False, "argcomplete", None),
        ]
    )
    def test_PV_ENV_VNV_110_create(self, name, req_scheme, dry_run, basename, env_name):
        filespecs = {
            "requirements.txt": "argcomplete",
            "requirements_frozen.txt": "argcomplete == 1.12.3",
            os.path.join("dev", "requirements_build.txt"): "",
            os.path.join("dev", "requirements_dev.txt"): "",
            os.path.join("dev", "requirements_test.txt"): "parameterized",
        }
        with ctx.project("dummy_package", filespecs=filespecs):
            x = env.VenvEnvironment(
                req_scheme, basename=basename, env_name=env_name, dry_run=dry_run
            )
            if not _should_suppress_output():
                x.create(check_preexisting=True)
            else:
                original_stderr = None
                with ctx.capture_to_file(x.create, check_preexisting=True) as (
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
            if not _should_suppress_output():
                x.create(check_preexisting=True)
            else:
                original_stderr = None
                with ctx.capture_to_file(x.create, check_preexisting=True) as (
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
                if not _should_suppress_output():
                    x.create(check_preexisting=True)
                else:
                    with ctx.capture_to_file(x.create, check_preexisting=True) as (
                        _status,
                        _stdout,
                        _stderr,
                    ):
                        pass

    @parameterized.parameterized.expand(
        [
            ("plain_dry_run", reqs.REQ_SCHEME_PLAIN, True, None, True, True),
            ("plain", reqs.REQ_SCHEME_PLAIN, False, None, True, True),
            (
                "plain_dry_run_env_name",
                reqs.REQ_SCHEME_PLAIN,
                True,
                ".dummy-venv",
                True,
                True,
            ),
            ("plain_env_name", reqs.REQ_SCHEME_PLAIN, False, ".dummy-venv", True, True),
            (
                "plain_dry_run_no_check_preexisting",
                reqs.REQ_SCHEME_PLAIN,
                True,
                None,
                False,
                False,
            ),
            (
                "plain_no_check_preexisting",
                reqs.REQ_SCHEME_PLAIN,
                False,
                None,
                False,
                True,
            ),
        ]
    )
    def test_PV_ENV_VNV_130_create_duplicate(
        self, name, req_scheme, dry_run, env_name, check_preexisting, should_raise
    ):
        filespecs = {
            "requirements.txt": "argcomplete",
            "requirements_frozen.txt": "argcomplete == 1.12.3",
            os.path.join("dev", "requirements_build.txt"): "",
            os.path.join("dev", "requirements_dev.txt"): "",
            os.path.join("dev", "requirements_test.txt"): "parameterized",
        }
        with ctx.project("dummy_package", filespecs=filespecs):
            x = env.VenvEnvironment(req_scheme, env_name=env_name, dry_run=False)
            if not _should_suppress_output():
                x.create()
            else:
                with ctx.capture_to_file(x.create) as (_status, _stdout, _stderr):
                    pass
            x = env.VenvEnvironment(req_scheme, env_name=env_name, dry_run=dry_run)
            if should_raise:
                with self.assertRaises(exc.EnvExistsError):
                    if not _should_suppress_output():
                        x.create(check_preexisting=check_preexisting)
                    else:
                        with ctx.capture_to_file(
                            x.create, check_preexisting=check_preexisting
                        ) as (_status, _stdout, _stderr):
                            pass
            else:
                if not _should_suppress_output():
                    x.create(check_preexisting=check_preexisting)
                else:
                    original_stderr = None
                    with ctx.capture_to_file(
                        x.create, check_preexisting=check_preexisting
                    ) as (_status, _stdout, stderr):
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
            ("plain_dry_run", reqs.REQ_SCHEME_PLAIN, True, None, None, None),
            ("plain", reqs.REQ_SCHEME_PLAIN, False, None, None, None),
            (
                "plain_dry_run_env_name",
                reqs.REQ_SCHEME_PLAIN,
                True,
                None,
                ".dummy-venv",
                None,
            ),
            ("plain_env_name", reqs.REQ_SCHEME_PLAIN, False, None, ".dummy-venv", None),
            ("prefix_dry_run", reqs.REQ_SCHEME_PLAIN, True, None, None, "dummy-prefix"),
            ("prefix", reqs.REQ_SCHEME_PLAIN, False, None, None, "dummy-prefix"),
            (
                "prefix_dry_run_env_name",
                reqs.REQ_SCHEME_PLAIN,
                True,
                None,
                ".dummy-venv",
                "dummy-prefix",
            ),
            (
                "prefix_env_name",
                reqs.REQ_SCHEME_PLAIN,
                False,
                None,
                ".dummy-venv",
                "dummy-prefix",
            ),
            ("dev_dry_run", reqs.REQ_SCHEME_DEV, True, None, None, None),
            ("dev", reqs.REQ_SCHEME_DEV, False, None, None, None),
            ("frozen_dry_run", reqs.REQ_SCHEME_FROZEN, True, None, None, None),
            ("frozen", reqs.REQ_SCHEME_FROZEN, False, None, None, None),
            ("source_dry_run", reqs.REQ_SCHEME_SOURCE, True, None, None, None),
            ("source", reqs.REQ_SCHEME_SOURCE, False, None, None, None),
            (
                "package_dry_run",
                reqs.REQ_SCHEME_PACKAGE,
                True,
                "argcomplete",
                None,
                None,
            ),
            ("package", reqs.REQ_SCHEME_PACKAGE, False, "argcomplete", None, None),
        ]
    )
    def test_PV_ENV_VNV_210_remove(
        self, name, req_scheme, dry_run, basename, env_name, env_prefix
    ):
        filespecs = {
            "requirements.txt": "argcomplete",
            "requirements_frozen.txt": "argcomplete == 1.12.3",
            os.path.join("dev", "requirements_build.txt"): "",
            os.path.join("dev", "requirements_dev.txt"): "",
            os.path.join("dev", "requirements_test.txt"): "parameterized",
        }
        with ctx.project("dummy_package", filespecs=filespecs):
            x = env.VenvEnvironment(
                req_scheme,
                basename=basename,
                env_name=env_name,
                env_prefix=env_prefix,
                dry_run=dry_run,
            )
            y = env.VenvEnvironment(
                req_scheme,
                basename=basename,
                env_name=env_name,
                env_prefix=env_prefix,
                dry_run=False,
            )
            if not _should_suppress_output():
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
            ("plain_dry_run", reqs.REQ_SCHEME_PLAIN, True, None, None, None),
            ("plain", reqs.REQ_SCHEME_PLAIN, False, None, None, None),
            (
                "plain_dry_run_env_name",
                reqs.REQ_SCHEME_PLAIN,
                True,
                None,
                ".dummy-venv",
                None,
            ),
            ("plain_env_name", reqs.REQ_SCHEME_PLAIN, False, None, ".dummy-venv", None),
            ("prefix_dry_run", reqs.REQ_SCHEME_PLAIN, True, None, None, "dummy-prefix"),
            ("prefix", reqs.REQ_SCHEME_PLAIN, False, None, None, "dummy-prefix"),
            (
                "prefix_dry_run_env_name",
                reqs.REQ_SCHEME_PLAIN,
                True,
                None,
                ".dummy-venv",
                "dummy-prefix",
            ),
            (
                "prefix_env_name",
                reqs.REQ_SCHEME_PLAIN,
                False,
                None,
                ".dummy-venv",
                "dummy-prefix",
            ),
            ("dev_dry_run", reqs.REQ_SCHEME_DEV, True, None, None, None),
            ("dev", reqs.REQ_SCHEME_DEV, False, None, None, None),
            ("frozen_dry_run", reqs.REQ_SCHEME_FROZEN, True, None, None, None),
            ("frozen", reqs.REQ_SCHEME_FROZEN, False, None, None, None),
            ("source_dry_run", reqs.REQ_SCHEME_SOURCE, True, None, None, None),
            ("source", reqs.REQ_SCHEME_SOURCE, False, None, None, None),
            (
                "package_dry_run",
                reqs.REQ_SCHEME_PACKAGE,
                True,
                "argcomplete",
                None,
                None,
            ),
            ("package", reqs.REQ_SCHEME_PACKAGE, False, "argcomplete", None, None),
        ]
    )
    def test_PV_ENV_VNV_310_replace_nonexistent(
        self, name, req_scheme, dry_run, basename, env_name, env_prefix
    ):
        filespecs = {
            "requirements.txt": "argcomplete",
            "requirements_frozen.txt": "argcomplete == 1.12.3",
            os.path.join("dev", "requirements_build.txt"): "",
            os.path.join("dev", "requirements_dev.txt"): "",
            os.path.join("dev", "requirements_test.txt"): "parameterized",
        }
        with ctx.project("dummy_package", filespecs=filespecs):
            x = env.VenvEnvironment(
                req_scheme,
                basename=basename,
                env_name=env_name,
                env_prefix=env_prefix,
                dry_run=dry_run,
            )
            if not _should_suppress_output():
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
            ("plain_dry_run", reqs.REQ_SCHEME_PLAIN, True, None, None, None),
            ("plain", reqs.REQ_SCHEME_PLAIN, False, None, None, None),
            (
                "plain_dry_run_env_name",
                reqs.REQ_SCHEME_PLAIN,
                True,
                None,
                ".dummy-venv",
                None,
            ),
            ("plain_env_name", reqs.REQ_SCHEME_PLAIN, False, None, ".dummy-venv", None),
            ("prefix_dry_run", reqs.REQ_SCHEME_PLAIN, True, None, None, "dummy-prefix"),
            ("prefix", reqs.REQ_SCHEME_PLAIN, False, None, None, "dummy-prefix"),
            (
                "prefix_dry_run_env_name",
                reqs.REQ_SCHEME_PLAIN,
                True,
                None,
                ".dummy-venv",
                "dummy-prefix",
            ),
            (
                "prefix_env_name",
                reqs.REQ_SCHEME_PLAIN,
                False,
                None,
                ".dummy-venv",
                "dummy-prefix",
            ),
            ("dev_dry_run", reqs.REQ_SCHEME_DEV, True, None, None, None),
            ("dev", reqs.REQ_SCHEME_DEV, False, None, None, None),
            ("frozen_dry_run", reqs.REQ_SCHEME_FROZEN, True, None, None, None),
            ("frozen", reqs.REQ_SCHEME_FROZEN, False, None, None, None),
            ("source_dry_run", reqs.REQ_SCHEME_SOURCE, True, None, None, None),
            ("source", reqs.REQ_SCHEME_SOURCE, False, None, None, None),
            (
                "package_dry_run",
                reqs.REQ_SCHEME_PACKAGE,
                True,
                "argcomplete",
                None,
                None,
            ),
            ("package", reqs.REQ_SCHEME_PACKAGE, False, "argcomplete", None, None),
        ]
    )
    def test_PV_ENV_VNV_320_replace_existing(
        self, name, req_scheme, dry_run, basename, env_name, env_prefix
    ):
        filespecs = {
            "requirements.txt": "argcomplete",
            "requirements_frozen.txt": "argcomplete == 1.12.3",
            os.path.join("dev", "requirements_build.txt"): "",
            os.path.join("dev", "requirements_dev.txt"): "",
            os.path.join("dev", "requirements_test.txt"): "parameterized",
        }
        with ctx.project("dummy_package", filespecs=filespecs):
            x = env.VenvEnvironment(
                req_scheme,
                basename=basename,
                env_name=env_name,
                env_prefix=env_prefix,
                dry_run=dry_run,
            )
            y = env.VenvEnvironment(
                req_scheme,
                basename=basename,
                env_name=env_name,
                env_prefix=env_prefix,
                dry_run=False,
            )
            if not _should_suppress_output():
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


########################################


@unittest.skipUnless(_should_run_conda_tests(), SKIP_CONDA_MESSAGE)
class TestEnv_200_CondaEnvironment(unittest.TestCase):
    def setUp(self):
        self.saved_requirements = reqs.REQUIREMENTS

    def tearDown(self):
        reqs.REQUIREMENTS = self.saved_requirements

    def test_PV_ENV_CDA_000_instantiate_empty(self):
        with self.assertRaises(TypeError) as raised:
            env.CondaEnvironment()
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
            (
                "python_version",
                {"python_version": "dummy_python_version"},
                "python_version",
                "dummy_python_version",
            ),
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
    def test_PV_ENV_CDA_002_instantiate_kwargs(self, name, kwargs, attr, value):
        x = env.CondaEnvironment("dummy_req_scheme", **kwargs)
        self.assertEqual(getattr(x, attr), value)

    def test_PV_ENV_CDA_010_requirements(self):
        dummy_requirements = {"dummy_req_source": ["dummy_requirement"]}
        reqs.REQUIREMENTS = {"dummy_req_scheme": dummy_requirements}
        x = env.CondaEnvironment("dummy_req_scheme")
        self.assertDictEqual(x.requirements, dummy_requirements)

    def test_PV_ENV_CDA_020_package_name(self):
        x = env.CondaEnvironment("dummy_req_scheme")
        self.assertEqual(x.package_name, "python_venv")

    @parameterized.parameterized.expand(
        [
            ("default", None, "python-venv"),
            ("specified", "dummy-package", "dummy-package"),
        ]
    )
    def test_PV_ENV_CDA_030_basename(self, name, basename, expected):
        kwargs = {} if basename is None else {"basename": basename}
        x = env.CondaEnvironment("dummy_req_scheme", **kwargs)
        self.assertEqual(x.basename, expected)

    @parameterized.parameterized.expand(
        [
            ("default", "dummy_req_scheme", {}, "python-venv"),
            ("default_dev", reqs.REQ_SCHEME_DEV, {}, "python-venv-dev"),
            (
                "basename",
                "dummy_req_scheme",
                {"basename": "dummy-package"},
                "dummy-package",
            ),
            (
                "basename_dev",
                reqs.REQ_SCHEME_DEV,
                {"basename": "dummy-package"},
                "dummy-package-dev",
            ),
            ("specified", "dummy_req_scheme", {"env_name": "dummy-env"}, "dummy-env"),
        ]
    )
    def test_PV_ENV_CDA_040_env_name(self, name, req_scheme, kwargs, expected):
        x = env.CondaEnvironment(req_scheme, **kwargs)
        self.assertEqual(x.env_name, expected)

    @parameterized.parameterized.expand(
        [
            ("default", None, None, None, "CONDA_ENV_DIR"),
            ("specified", None, "dummy-env", None, "CONDA_ENV_DIR"),
            (
                "with_prefix",
                "dummy-basename",
                None,
                "dummy-prefix",
                os.path.join("dummy-prefix", "dummy-basename"),
            ),
            (
                "specified_with_prefix",
                "dummy-basename",
                "dummy-env",
                "dummy-prefix",
                os.path.join("dummy-prefix", "dummy-env"),
            ),
        ]
    )
    def test_PV_ENV_CDA_050_env_dir_dry_run(
        self, name, basename, env_name, env_prefix, expected
    ):
        kwargs = {}
        if basename is not None:
            kwargs["basename"] = basename
        if env_name is not None:
            kwargs["env_name"] = env_name
        if env_prefix is not None:
            kwargs["env_prefix"] = env_prefix
        x = env.CondaEnvironment("dummy_req_scheme", dry_run=True, **kwargs)
        self.assertEqual(x.env_dir, expected)

    @parameterized.parameterized.expand(
        [
            ("default", None, None, None, os.path.join(os.getcwd(), "CONDA_ENV_DIR")),
            (
                "specified",
                None,
                "dummy-env",
                None,
                os.path.join(os.getcwd(), "CONDA_ENV_DIR"),
            ),
            (
                "with_prefix",
                "dummy-basename",
                None,
                "dummy-prefix",
                os.path.join(os.getcwd(), "dummy-prefix", "dummy-basename"),
            ),
            (
                "specified_with_prefix",
                "dummy-basename",
                "dummy-env",
                "dummy-prefix",
                os.path.join(os.getcwd(), "dummy-prefix", "dummy-env"),
            ),
        ]
    )
    def test_PV_ENV_CDA_051_abs_env_dir_dry_run(
        self, name, basename, env_name, env_prefix, expected
    ):
        kwargs = {}
        if basename is not None:
            kwargs["basename"] = basename
        if env_name is not None:
            kwargs["env_name"] = env_name
        if env_prefix is not None:
            kwargs["env_prefix"] = env_prefix
        x = env.CondaEnvironment("dummy_req_scheme", dry_run=True, **kwargs)
        self.assertEqual(x.abs_env_dir, expected)

    @parameterized.parameterized.expand(
        [
            ("specified", "dummy-env", "dummy-env"),
        ]
    )
    def test_PV_ENV_CDA_060_env_description(self, name, env_name, expected):
        kwargs = {} if env_name is None else {"env_name": env_name}
        x = env.CondaEnvironment("dummy_req_scheme", **kwargs)
        x.env_description
        self.assertTrue(x.env_description.endswith(expected))

    @parameterized.parameterized.expand(
        [
            ("dry_run_text", {}, "[DRY-RUN]"),
            ("create_msg", {}, "Creating conda environment dummy-package"),
            ("create_venv", {}, "+ conda create"),
            (
                "create_with_python_version",
                {"python_version": "3.8"},
                "+ conda create --quiet -n dummy-package python=3.8",
            ),
            ("install_msg", {}, "Installing dummy_req_scheme requirements"),
            (
                "pip_install",
                {},
                "+ CONDA_ENV_DIR/bin/python3 -m pip install -r dummy_requirements.txt",
            ),
            ("success", {}, "==> Done."),
        ]
    )
    def test_PV_ENV_CDA_100_create_dry_run(self, name, kwargs, expected_text):
        dummy_requirements = {reqs.FROM_FILES: ["dummy_requirements.txt"]}
        reqs.REQUIREMENTS = {"dummy_req_scheme": dummy_requirements}
        x = env.CondaEnvironment(
            "dummy_req_scheme",
            dry_run=True,
            basename="dummy-package",
            ignore_preflight_checks=True,
            **kwargs,
        )
        with ctx.capture(x.create, check_preexisting=False) as (
            status,
            _stdout,
            stderr,
        ):
            self.assertTrue(expected_text in stderr)

    @parameterized.parameterized.expand(
        [
            ("dry_run_text", "[DRY-RUN]"),
            ("remove_msg", "Removing conda environment dummy-package"),
        ]
    )
    def test_PV_ENV_CDA_200_remove_dry_run(self, name, expected_text):
        x = env.CondaEnvironment(
            "dummy_req_scheme", dry_run=True, basename="dummy-package"
        )
        with ctx.capture(x.remove) as (status, _stdout, stderr):
            self.assertTrue(expected_text in stderr)

    @parameterized.parameterized.expand(
        [
            ("dry_run_text", "[DRY-RUN]"),
            ("replace_msg", "Replacing conda environment dummy-package"),
            ("remove_msg", "Removing conda environment dummy-package"),
            ("create_msg", "Creating conda environment dummy-package"),
            ("success", "==> Done."),
        ]
    )
    def test_PV_ENV_CDA_300_replace_dry_run(self, name, expected_text):
        dummy_requirements = {reqs.FROM_FILES: ["dummy_requirements.txt"]}
        reqs.REQUIREMENTS = {"dummy_req_scheme": dummy_requirements}
        x = env.CondaEnvironment(
            "dummy_req_scheme",
            dry_run=True,
            basename="dummy-package",
            ignore_preflight_checks=True,
        )
        with ctx.capture(x.replace) as (status, _stdout, stderr):
            self.assertTrue(expected_text in stderr)


########################################


@unittest.skipUnless(_should_run_conda_tests(), SKIP_CONDA_MESSAGE)
class TestEnv_210_CondaCreate(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    @parameterized.parameterized.expand(
        [
            ("plain_dry_run", reqs.REQ_SCHEME_PLAIN, True, None, None),
            ("plain", reqs.REQ_SCHEME_PLAIN, False, None, None),
            (
                "plain_dry_run_env_name",
                reqs.REQ_SCHEME_PLAIN,
                True,
                None,
                "dummy-env",
            ),
            ("plain_env_name", reqs.REQ_SCHEME_PLAIN, False, None, "dummy-env"),
            ("dev_dry_run", reqs.REQ_SCHEME_DEV, True, None, None),
            ("dev", reqs.REQ_SCHEME_DEV, False, None, None),
            ("frozen_dry_run", reqs.REQ_SCHEME_FROZEN, True, None, None),
            ("frozen", reqs.REQ_SCHEME_FROZEN, False, None, None),
            ("source_dry_run", reqs.REQ_SCHEME_SOURCE, True, None, None),
            ("source", reqs.REQ_SCHEME_SOURCE, False, None, None),
            ("package_dry_run", reqs.REQ_SCHEME_PACKAGE, True, "argcomplete", None),
            ("package", reqs.REQ_SCHEME_PACKAGE, False, "argcomplete", None),
        ]
    )
    @unittest.skipUnless(_should_run_long_tests(), SKIP_LONG_RUNNING_MESSAGE)
    def test_PV_ENV_CDA_110_create(self, name, req_scheme, dry_run, basename, env_name):
        env_prefix = ".conda-env"  # Must use env_prefix to avoid polluting conda envs
        dirs = [env_prefix]
        filespecs = {
            "requirements.txt": "argcomplete",
            "requirements_frozen.txt": "argcomplete == 1.12.3",
            os.path.join("dev", "requirements_build.txt"): "",
            os.path.join("dev", "requirements_dev.txt"): "",
            os.path.join("dev", "requirements_test.txt"): "parameterized",
        }
        with ctx.project("dummy_package", dirs=dirs, filespecs=filespecs):
            x = env.CondaEnvironment(
                req_scheme,
                basename=basename,
                env_name=env_name,
                env_prefix=env_prefix,
                dry_run=dry_run,
                force=True,
            )
            if not _should_suppress_output():
                x.create(check_preexisting=True)
            else:
                original_stderr = None
                with ctx.capture_to_file(x.create, check_preexisting=True) as (
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
            ("frozen_dry_run", reqs.REQ_SCHEME_FROZEN, True, None, None),
            ("frozen", reqs.REQ_SCHEME_FROZEN, False, None, None),
        ]
    )
    def test_PV_ENV_CDA_120_create_missing_reqs(
        self, name, req_scheme, dry_run, basename, env_name
    ):
        env_prefix = ".conda-env"
        dirs = [env_prefix]
        with ctx.project("dummy_package", dirs=dirs):
            x = env.CondaEnvironment(
                req_scheme,
                basename=basename,
                env_name=env_name,
                env_prefix=env_prefix,
                dry_run=dry_run,
                force=True,
            )
            with self.assertRaises(exc.MissingRequirementsError):
                if not _should_suppress_output():
                    x.create(check_preexisting=True)
                else:
                    with ctx.capture_to_file(x.create, check_preexisting=True) as (
                        _status,
                        _stdout,
                        _stderr,
                    ):
                        pass

    @parameterized.parameterized.expand(
        [
            ("plain_dry_run", reqs.REQ_SCHEME_PLAIN, True, None, True, True),
            ("plain", reqs.REQ_SCHEME_PLAIN, False, None, True, True),
            (
                "plain_dry_run_env_name",
                reqs.REQ_SCHEME_PLAIN,
                True,
                "dummy-env",
                True,
                True,
            ),
            ("plain_env_name", reqs.REQ_SCHEME_PLAIN, False, "dummy-env", True, True),
            (
                "plain_dry_run_no_check_preexisting",
                reqs.REQ_SCHEME_PLAIN,
                True,
                None,
                False,
                False,
            ),
            (
                "plain_no_check_preexisting",
                reqs.REQ_SCHEME_PLAIN,
                False,
                None,
                False,
                True,
            ),
        ]
    )
    @unittest.skipUnless(_should_run_long_tests(), SKIP_LONG_RUNNING_MESSAGE)
    def test_PV_ENV_CDA_130_create_duplicate(
        self, name, req_scheme, dry_run, env_name, check_preexisting, should_raise
    ):
        env_prefix = ".conda-env"
        dirs = [env_prefix]
        filespecs = {
            "requirements.txt": "argcomplete",
            "requirements_frozen.txt": "argcomplete == 1.12.3",
            os.path.join("dev", "requirements_build.txt"): "",
            os.path.join("dev", "requirements_dev.txt"): "",
            os.path.join("dev", "requirements_test.txt"): "parameterized",
        }
        with ctx.project("dummy_package", dirs=dirs, filespecs=filespecs):
            x = env.CondaEnvironment(
                req_scheme,
                env_name=env_name,
                env_prefix=env_prefix,
                dry_run=False,
                force=True,
            )
            if not _should_suppress_output():
                x.create()
            else:
                with ctx.capture_to_file(x.create) as (_status, _stdout, _stderr):
                    pass
            x = env.CondaEnvironment(
                req_scheme,
                env_name=env_name,
                env_prefix=env_prefix,
                dry_run=dry_run,
                force=True,
            )
            if should_raise:
                with self.assertRaises(exc.EnvExistsError):
                    if not _should_suppress_output():
                        x.create(check_preexisting=check_preexisting)
                    else:
                        with ctx.capture_to_file(
                            x.create, check_preexisting=check_preexisting
                        ) as (_status, _stdout, _stderr):
                            pass
            else:
                if not _should_suppress_output():
                    x.create(check_preexisting=check_preexisting)
                else:
                    original_stderr = None
                    with ctx.capture_to_file(
                        x.create, check_preexisting=check_preexisting
                    ) as (_status, _stdout, stderr):
                        original_stderr = stderr
                    testable_stderr = original_stderr.lower()
                    if "error" in testable_stderr:
                        print(original_stderr, file=stderr)
                    self.assertNotIn("error", testable_stderr)


########################################


@unittest.skipUnless(_should_run_conda_tests(), SKIP_CONDA_MESSAGE)
class TestEnv_220_CondaRemove(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    @parameterized.parameterized.expand(
        [
            ("plain_dry_run", reqs.REQ_SCHEME_PLAIN, True, None, None),
            ("plain", reqs.REQ_SCHEME_PLAIN, False, None, None),
            (
                "plain_dry_run_env_name",
                reqs.REQ_SCHEME_PLAIN,
                True,
                None,
                "dummy-env",
            ),
            ("plain_env_name", reqs.REQ_SCHEME_PLAIN, False, None, "dummy-env"),
            ("dev_dry_run", reqs.REQ_SCHEME_DEV, True, None, None),
            ("dev", reqs.REQ_SCHEME_DEV, False, None, None),
            ("frozen_dry_run", reqs.REQ_SCHEME_FROZEN, True, None, None),
            ("frozen", reqs.REQ_SCHEME_FROZEN, False, None, None),
            ("source_dry_run", reqs.REQ_SCHEME_SOURCE, True, None, None),
            ("source", reqs.REQ_SCHEME_SOURCE, False, None, None),
            ("package_dry_run", reqs.REQ_SCHEME_PACKAGE, True, "argcomplete", None),
            ("package", reqs.REQ_SCHEME_PACKAGE, False, "argcomplete", None),
        ]
    )
    @unittest.skipUnless(_should_run_long_tests(), SKIP_LONG_RUNNING_MESSAGE)
    def test_PV_ENV_CDA_210_remove(self, name, req_scheme, dry_run, basename, env_name):
        env_prefix = ".conda-env"
        dirs = [env_prefix]
        filespecs = {
            "requirements.txt": "argcomplete",
            "requirements_frozen.txt": "argcomplete == 1.12.3",
            os.path.join("dev", "requirements_build.txt"): "",
            os.path.join("dev", "requirements_dev.txt"): "",
            os.path.join("dev", "requirements_test.txt"): "parameterized",
        }
        with ctx.project("dummy_package", dirs=dirs, filespecs=filespecs):
            x = env.CondaEnvironment(
                req_scheme,
                basename=basename,
                env_name=env_name,
                env_prefix=env_prefix,
                dry_run=dry_run,
                force=True,
            )
            y = env.CondaEnvironment(
                req_scheme,
                basename=basename,
                env_name=env_name,
                env_prefix=env_prefix,
                dry_run=False,
                force=True,
            )
            if not _should_suppress_output():
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


@unittest.skipUnless(_should_run_conda_tests(), SKIP_CONDA_MESSAGE)
class TestEnv_230_CondaReplace(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    @parameterized.parameterized.expand(
        [
            ("plain_dry_run", reqs.REQ_SCHEME_PLAIN, True, None, None),
            ("plain", reqs.REQ_SCHEME_PLAIN, False, None, None),
            (
                "plain_dry_run_env_name",
                reqs.REQ_SCHEME_PLAIN,
                True,
                None,
                "dummy-env",
            ),
            ("plain_env_name", reqs.REQ_SCHEME_PLAIN, False, None, "dummy-env"),
            ("dev_dry_run", reqs.REQ_SCHEME_DEV, True, None, None),
            ("dev", reqs.REQ_SCHEME_DEV, False, None, None),
            ("frozen_dry_run", reqs.REQ_SCHEME_FROZEN, True, None, None),
            ("frozen", reqs.REQ_SCHEME_FROZEN, False, None, None),
            ("source_dry_run", reqs.REQ_SCHEME_SOURCE, True, None, None),
            ("source", reqs.REQ_SCHEME_SOURCE, False, None, None),
            ("package_dry_run", reqs.REQ_SCHEME_PACKAGE, True, "argcomplete", None),
            ("package", reqs.REQ_SCHEME_PACKAGE, False, "argcomplete", None),
        ]
    )
    @unittest.skipUnless(_should_run_long_tests(), SKIP_LONG_RUNNING_MESSAGE)
    def test_PV_ENV_CDA_310_replace_nonexistent(
        self, name, req_scheme, dry_run, basename, env_name
    ):
        env_prefix = ".conda-env"
        dirs = [env_prefix]
        filespecs = {
            "requirements.txt": "argcomplete",
            "requirements_frozen.txt": "argcomplete == 1.12.3",
            os.path.join("dev", "requirements_build.txt"): "",
            os.path.join("dev", "requirements_dev.txt"): "",
            os.path.join("dev", "requirements_test.txt"): "parameterized",
        }
        with ctx.project("dummy_package", dirs=dirs, filespecs=filespecs):
            x = env.CondaEnvironment(
                req_scheme,
                basename=basename,
                env_name=env_name,
                env_prefix=env_prefix,
                dry_run=dry_run,
                force=True,
            )
            if not _should_suppress_output():
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
            ("plain_dry_run", reqs.REQ_SCHEME_PLAIN, True, None, None),
            ("plain", reqs.REQ_SCHEME_PLAIN, False, None, None),
            (
                "plain_dry_run_env_name",
                reqs.REQ_SCHEME_PLAIN,
                True,
                None,
                "dummy-env",
            ),
            ("plain_env_name", reqs.REQ_SCHEME_PLAIN, False, None, "dummy-env"),
            ("dev_dry_run", reqs.REQ_SCHEME_DEV, True, None, None),
            ("dev", reqs.REQ_SCHEME_DEV, False, None, None),
            ("frozen_dry_run", reqs.REQ_SCHEME_FROZEN, True, None, None),
            ("frozen", reqs.REQ_SCHEME_FROZEN, False, None, None),
            ("source_dry_run", reqs.REQ_SCHEME_SOURCE, True, None, None),
            ("source", reqs.REQ_SCHEME_SOURCE, False, None, None),
            ("package_dry_run", reqs.REQ_SCHEME_PACKAGE, True, "argcomplete", None),
            ("package", reqs.REQ_SCHEME_PACKAGE, False, "argcomplete", None),
        ]
    )
    @unittest.skipUnless(_should_run_long_tests(), SKIP_LONG_RUNNING_MESSAGE)
    def test_PV_ENV_CDA_320_replace_existing(
        self, name, req_scheme, dry_run, basename, env_name
    ):
        env_prefix = ".conda-env"
        dirs = [env_prefix]
        filespecs = {
            "requirements.txt": "argcomplete",
            "requirements_frozen.txt": "argcomplete == 1.12.3",
            os.path.join("dev", "requirements_build.txt"): "",
            os.path.join("dev", "requirements_dev.txt"): "",
            os.path.join("dev", "requirements_test.txt"): "parameterized",
        }
        with ctx.project("dummy_package", dirs=dirs, filespecs=filespecs):
            x = env.CondaEnvironment(
                req_scheme,
                basename=basename,
                env_name=env_name,
                env_prefix=env_prefix,
                dry_run=dry_run,
                force=True,
            )
            y = env.CondaEnvironment(
                req_scheme,
                basename=basename,
                env_name=env_name,
                env_prefix=env_prefix,
                dry_run=False,
                force=True,
            )
            if not _should_suppress_output():
                y.create()
                x.replace()
            else:
                original_stderrs = []
                with ctx.capture_to_file(y.create) as (_status, _stdout, stderr):
                    original_stderrs.append(stderr)
                with ctx.capture_to_file(x.replace) as (_status, _stdout, stderr):
                    original_stderrs.append(stderr)
                testable_stderrs = [text.lower() for text in original_stderrs]
                for (i, text) in enumerate(testable_stderrs):
                    if "error" in text:
                        print(original_stderrs[i], file=stderr)
                    self.assertNotIn("error", text)
