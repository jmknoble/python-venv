"""Provide unit tests for `~python_venv.const`:py:mod:."""

import unittest

from python_venv import const

########################################
# Tests


class TestConst(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_PV_CO_000_symbols_exist(self):
        _ = const.STATUS_SUCCESS
        _ = const.STATUS_FAILURE
        _ = const.STATUS_HELP
        _ = const.PYTHON
        _ = const.PYTHON_VERSION_REGEX
        _ = const.CONDA
        _ = const.PYENV
        _ = const.VENV_DIR
        _ = const.DEV_SUFFIX
        _ = const.MESSAGE_PREFIX
        _ = const.ENV_TYPE_VENV
        _ = const.ENV_TYPE_PYENV
        _ = const.ENV_TYPE_CONDA
        _ = const.ENV_TYPES
        _ = const.FROM_FILES
        _ = const.FROM_PACKAGES
        _ = const.FROM_COMMANDS
        _ = const.FROM_BDIST_WHEEL
        _ = const.FROM_PIP_ARGS
