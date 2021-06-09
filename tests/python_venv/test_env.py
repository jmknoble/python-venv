"""Provide unit tests for `~python_venv.reqs`:py:mod:."""

import os
import os.path
import unittest

import parameterized  # https://pypi.org/project/parameterized/

from python_venv import env, reqs
from tests.python_venv import contextmgr as ctx

########################################
# Tests


class TestEnv(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_PV_ENV_000_symbols_exist(self):
        _ = env.PYTHON
        _ = env.CONDA
        _ = env.VENV_DIR
        _ = env.DEV_SUFFIX


class TestBaseVirtualEnvironment(unittest.TestCase):
    def setUp(self):
        self.saved_requirements = reqs.REQUIREMENTS

    def tearDown(self):
        reqs.REQUIREMENTS = self.saved_requirements

    def test_PV_ENV_BAS_000_instantiate_empty(self):
        with self.assertRaises(TypeError) as context:
            env.BaseVirtualEnvironment()
            msg = context.args[0]
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

    def test_PV_ENV_BAS_050_abstract_env_dir(self):
        x = env.BaseVirtualEnvironment("dummy_req_scheme")
        with self.assertRaises(NotImplementedError):
            x.env_dir

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


class TestVenvEnvironment(unittest.TestCase):
    def setUp(self):
        self.saved_requirements = reqs.REQUIREMENTS

    def tearDown(self):
        reqs.REQUIREMENTS = self.saved_requirements

    def test_PV_ENV_VNV_000_instantiate_empty(self):
        with self.assertRaises(TypeError) as context:
            env.VenvEnvironment()
            msg = context.args[0]
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
            ("default", None, ".venv"),
            ("specified", "dummy-env", "dummy-env"),
        ]
    )
    def test_PV_ENV_VNV_050_env_dir(self, name, env_name, expected):
        kwargs = {} if env_name is None else {"env_name": env_name}
        x = env.VenvEnvironment("dummy_req_scheme", **kwargs)
        self.assertEqual(x.env_dir, expected)

    @parameterized.parameterized.expand(
        [
            ("default", None, os.path.join(os.getcwd(), ".venv")),
            ("specified", "dummy-env", os.path.join(os.getcwd(), "dummy-env")),
        ]
    )
    def test_PV_ENV_VNV_051_full_env_dir(self, name, env_name, expected):
        kwargs = {} if env_name is None else {"env_name": env_name}
        x = env.VenvEnvironment("dummy_req_scheme", **kwargs)
        self.assertEqual(x.full_env_dir, expected)

    @parameterized.parameterized.expand(
        [
            ("default", None, ".venv"),
            ("specified", "dummy-env", "dummy-env"),
        ]
    )
    def test_PV_ENV_VNV_060_env_description(self, name, env_name, expected):
        kwargs = {} if env_name is None else {"env_name": env_name}
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
            "dummy_req_scheme", dry_run=True, env_name=".dummy-venv"
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


########################################


class TestCondaEnvironment(unittest.TestCase):
    def setUp(self):
        self.saved_requirements = reqs.REQUIREMENTS

    def tearDown(self):
        reqs.REQUIREMENTS = self.saved_requirements

    def test_PV_ENV_CDA_000_instantiate_empty(self):
        with self.assertRaises(TypeError) as context:
            env.CondaEnvironment()
            msg = context.args[0]
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

    def test_PV_ENV_CDA_050_env_dir_dry_run(self):
        x = env.CondaEnvironment("dummy_req_scheme", dry_run=True)
        self.assertEqual(x.env_dir, "CONDA_ENV_DIR")

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
            ("dry_run_text", "[DRY-RUN]"),
            ("create_msg", "Creating conda environment dummy-package"),
            ("create_venv", "+ conda create -n dummy-package"),
            ("install_msg", "Installing dummy_req_scheme requirements"),
            (
                "pip_install",
                "+ CONDA_ENV_DIR/bin/python3 -m pip install -r dummy_requirements.txt",
            ),
            ("success", "==> Done."),
        ]
    )
    def test_PV_ENV_CDA_100_create_dry_run(self, name, expected_text):
        dummy_requirements = {reqs.FROM_FILES: ["dummy_requirements.txt"]}
        reqs.REQUIREMENTS = {"dummy_req_scheme": dummy_requirements}
        x = env.CondaEnvironment(
            "dummy_req_scheme", dry_run=True, basename="dummy-package"
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
