"""Provide methods for manipulating `os.environ`:py:attr:."""

import contextlib
import os
import sys


def python_lib_version():
    """Get the Python version as it appears in the lib directory."""
    major = sys.version_info[0]
    minor = sys.version_info[1]
    return f"python{major}.{minor}"


def clean_syspath(syspath, suffix):
    """Remove things from syspath that have to do with virtual envs."""
    syspath_parts = syspath.split(os.pathsep)
    for env_var in [
        "VIRTUAL_ENV",
        "CONDA_PREFIX",
    ]:
        env_dir = os.environ.get(env_var)
        if not env_dir:
            continue
        env_dir = os.path.join(env_dir, suffix)
        indexes = []
        for (i, path) in enumerate(syspath_parts):
            if path == env_dir:
                indexes.append(i)
        for i in reversed(indexes):
            del syspath_parts[i]
    return os.pathsep.join(syspath_parts)


def get_clean_environ(environ=None):
    """Return an environment that has virtual environment detritus removed."""
    if environ is None:
        environ = os.environ
    environ = environ.copy()
    try:
        environ["PATH"] = clean_syspath(environ["PATH"], "bin")
        environ["PYTHONPATH"] = clean_syspath(
            environ["PYTHONPATH"],
            os.path.join("lib", python_lib_version(), "site-packages"),
        )
    except KeyError:
        pass
    for env_var in [
        "PYTHONHOME",
        "VIRTUAL_ENV",
        "CONDA_DEFAULT_ENV",
        "CONDA_PREFIX",
    ]:
        try:
            del environ[env_var]
        except KeyError:
            pass
    return environ


@contextlib.contextmanager
def clean_environ(environ=None):
    """Provide a cleaned environment using a context manager."""
    if environ is None:
        environ = os.environ

    try:
        environ = get_clean_environ(environ)
        yield environ
    finally:
        pass


@contextlib.contextmanager
def clean_os_environ(environ=None):
    """Provide a cleaned `os.environ`:py:attr: using a context manager."""
    if environ is None:
        environ = os.environ
    original_os_environ = environ

    try:
        os.environ = get_clean_environ(environ)
        yield os.environ
    finally:
        os.environ = original_os_environ
