"""Provide unit tests for `~python_venv.reqs`:py:mod:."""

import unittest

import parameterized  # https://pypi.org/project/parameterized/

from python_venv import exceptions as exc

########################################
# Tests


class TestExceptions(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_PV_XC_000_symbols_exist(self):
        _ = exc.BaseError
        _ = exc.EnvError
        _ = exc.RequirementsError
        _ = exc.EnvNotFoundError
        _ = exc.EnvExistsError
        _ = exc.EnvOccludedError
        _ = exc.MissingRequirementsError

    @parameterized.parameterized.expand(
        [
            ("base_error", exc.BaseError, exc.BaseError),
            ("base_error_as_exc", exc.BaseError, Exception),
            ("env_error", exc.EnvError, exc.EnvError),
            ("req_error", exc.RequirementsError, exc.RequirementsError),
            ("env_error_as_base", exc.EnvError, exc.BaseError),
            ("req_error_as_base", exc.RequirementsError, exc.BaseError),
            ("env_not_found", exc.EnvNotFoundError, exc.EnvNotFoundError),
            ("env_exists", exc.EnvExistsError, exc.EnvExistsError),
            ("env_occluded", exc.EnvOccludedError, exc.EnvOccludedError),
            ("env_not_found_as_env", exc.EnvNotFoundError, exc.EnvError),
            ("env_exists_as_env", exc.EnvExistsError, exc.EnvError),
            ("env_occluded_as_env", exc.EnvOccludedError, exc.EnvError),
            ("missing_req", exc.MissingRequirementsError, exc.MissingRequirementsError),
            ("missing_req_as_req", exc.MissingRequirementsError, exc.RequirementsError),
        ]
    )
    def test_PV_XC_010_raise(self, name, exception, catch):
        with self.assertRaises(catch) as _:
            raise exception
