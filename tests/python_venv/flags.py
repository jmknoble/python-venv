"""Provide some flags and related functions for tests."""

import os
import os.path
import subprocess

HERE = os.getcwd()

FLAG_TEST_WITHOUT_PYENV = "TEST_WITHOUT_PYENV.tmp"
FLAG_TEST_WITHOUT_CONDA = "TEST_WITHOUT_CONDA.tmp"
FLAG_TEST_WITH_LONG_RUNNING = "TEST_WITH_LONG_RUNNING.tmp"
FLAG_TEST_WITH_OUTPUT = "TEST_WITH_OUTPUT.tmp"

SKIP_CONDA_MESSAGE = "requires conda"
SKIP_PYENV_MESSAGE = "requires pyenv and pyenv-virtualenv"
SKIP_LONG_RUNNING_MESSAGE = (
    f"takes a long time (touch {FLAG_TEST_WITH_LONG_RUNNING} to run anyway)"
)


def have_pyenv():
    """The ``pyenv`` command is available."""
    try:
        subprocess.check_call(
            ["pyenv", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        subprocess.check_call(
            ["pyenv", "virtualenv", "--help"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False
    return True


def should_run_pyenv_tests():
    """We should run tests for pyenv environments."""
    return have_pyenv() and not os.path.exists(
        os.path.join(HERE, FLAG_TEST_WITHOUT_PYENV)
    )


def have_conda():
    """The ``conda`` command is available."""
    try:
        subprocess.call(
            ["conda", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
    except FileNotFoundError:
        return False
    return True


def should_run_conda_tests():
    """We should run tests for conda environments."""
    return have_conda() and not os.path.exists(
        os.path.join(HERE, FLAG_TEST_WITHOUT_CONDA)
    )


def should_run_long_tests():
    """We should run tests that take a while."""
    return os.path.exists(os.path.join(HERE, FLAG_TEST_WITH_LONG_RUNNING))


def should_suppress_output():
    """Running tests should not print to stdout or stderr."""
    return not os.path.exists(os.path.join(HERE, FLAG_TEST_WITH_OUTPUT))
