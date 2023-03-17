"""Provide unit tests for `~python_venv.env.base`:py:mod:."""

import unittest

import parameterized  # https://pypi.org/project/parameterized/

from python_venv import const, reqs
from python_venv.env import base as env_base


class TestEnv_000_General(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_PV_ENV_000_symbols_exist(self):
        _ = const.PYTHON
        _ = const.CONDA
        _ = const.PYENV
        _ = const.VENV_DIR
        _ = const.DEV_SUFFIX
        _ = const.DIST_DIR
        _ = const.ENV_DIR_PLACEHOLDER
        _ = const.ENV_TYPES_NAMED


class TestEnv_010_BaseVirtualEnvironment(unittest.TestCase):
    def setUp(self):
        self.saved_requirements = reqs.REQUIREMENTS

    def tearDown(self):
        reqs.REQUIREMENTS = self.saved_requirements

    def test_PV_ENV_BAS_000_instantiate_empty(self):
        with self.assertRaises(TypeError) as raised:
            env_base.BaseVirtualEnvironment()
        msg = raised.exception.args[0]
        self.assertTrue("__init__() missing 1 required positional argument" in msg)

    def test_PV_ENV_BAS_001_instantiate(self):
        x = env_base.BaseVirtualEnvironment("dummy_req_scheme")
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
        x = env_base.BaseVirtualEnvironment("dummy_req_scheme", **kwargs)
        self.assertEqual(getattr(x, attr), value)

    def test_PV_ENV_BAS_010_requirements(self):
        dummy_requirements = {"dummy_req_source": ["dummy_value"]}
        reqs.REQUIREMENTS = {"dummy_req_scheme": [dummy_requirements]}
        x = env_base.BaseVirtualEnvironment("dummy_req_scheme")
        self.assertListEqual(x.requirements.requirements, [dummy_requirements])

    def test_PV_ENV_BAS_020_package_name(self):
        x = env_base.BaseVirtualEnvironment("dummy_req_scheme")
        self.assertEqual(x.package_name, "python_venv")

    @parameterized.parameterized.expand(
        [
            ("default", None, "python-venv"),
            ("specified", "dummy-package", "dummy-package"),
        ]
    )
    def test_PV_ENV_BAS_030_basename(self, name, basename, expected):
        kwargs = {} if basename is None else {"basename": basename}
        x = env_base.BaseVirtualEnvironment("dummy_req_scheme", **kwargs)
        self.assertEqual(x.basename, expected)

    def test_PV_ENV_BAS_040_abstract_env_name(self):
        x = env_base.BaseVirtualEnvironment("dummy_req_scheme")
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
        x = env_base.BaseVirtualEnvironment("dummy_req_scheme", **kwargs)
        self.assertEqual(x.env_prefix, expected)

    def test_PV_ENV_BAS_050_abstract_env_dir(self):
        x = env_base.BaseVirtualEnvironment("dummy_req_scheme")
        with self.assertRaises(NotImplementedError):
            x.env_dir

    def test_PV_ENV_BAS_051_abstract_env_bin_dir(self):
        x = env_base.BaseVirtualEnvironment("dummy_req_scheme")
        with self.assertRaises(NotImplementedError):
            x.env_bin_dir

    def test_PV_ENV_BAS_052_abstract_env_python(self):
        x = env_base.BaseVirtualEnvironment("dummy_req_scheme")
        with self.assertRaises(NotImplementedError):
            x.env_python

    def test_PV_ENV_BAS_055_abstract_abs_env_dir(self):
        x = env_base.BaseVirtualEnvironment("dummy_req_scheme")
        with self.assertRaises(NotImplementedError):
            x.abs_env_dir

    def test_PV_ENV_BAS_060_abstract_env_description(self):
        x = env_base.BaseVirtualEnvironment("dummy_req_scheme")
        with self.assertRaises(NotImplementedError):
            x.env_description

    def test_PV_ENV_BAS_100_abstract_create(self):
        x = env_base.BaseVirtualEnvironment("dummy_req_scheme")
        with self.assertRaises(NotImplementedError):
            x.create()

    def test_PV_ENV_BAS_200_abstract_remove(self):
        x = env_base.BaseVirtualEnvironment("dummy_req_scheme")
        with self.assertRaises(NotImplementedError):
            x.remove()
