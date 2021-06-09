"""Provide context managers for use in unit tests."""

import contextlib
import os
import os.path
import sys
import tempfile
from io import StringIO


@contextlib.contextmanager
def capture(a_callable, *args, **kwargs):
    """Capture status, stdout, and stderr from a function or method call"""
    (orig_stdout, sys.stdout) = (sys.stdout, StringIO())
    (orig_stderr, sys.stderr) = (sys.stderr, StringIO())
    try:
        status = a_callable(*args, **kwargs)
        sys.stdout.seek(0)
        sys.stderr.seek(0)
        yield (status, sys.stdout.read(), sys.stderr.read())
    finally:
        sys.stdout.close()
        sys.stderr.close()
        sys.stdout = orig_stdout
        sys.stderr = orig_stderr


SETUP_TEMPLATE = """
import os.path
from setuptools import find_packages, setup

SETUP_DIR = os.path.dirname(os.path.realpath(__file__))


def get_requirements_from_file(dirname, basename, default=None):
    reqs_path = os.path.join(dirname, basename)
    if os.path.isfile(reqs_path):
        with open(reqs_path) as f:
            return [x for x in (y.strip() for y in f) if not x.startswith("#")]
    else:
        return [] if default is None else default


setup(
    name="{package_name}",
    packages=find_packages(
        include=["*"],
        exclude=[
            "build",
            "dist",
            "docs",
            "examples",
            "tests",
            "tests.*",
            "*.egg-info",
        ]
    ),
    install_requires=get_requirements_from_file(SETUP_DIR, "requirements.txt"),
)
"""


def _ensure_relative_path(path):
    if ".." in path:
        raise ValueError(
            f"path must be relative and may not refer to parent dir: '{path}'"
        )
    if not path.startswith(os.path.join(".", "")):
        path = os.path.join(".", path)
    return path


def _python_lib_version():
    major = sys.version_info[0]
    minor = sys.version_info[1]
    return f"python{major}.{minor}"


def _clean_syspath(syspath, suffix):
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


def _clean_environ_copy(environ):
    environ = environ.copy()
    try:
        environ["PATH"] = _clean_syspath(environ["PATH"], "bin")
        environ["PYTHONPATH"] = _clean_syspath(
            environ["PYTHONPATH"],
            os.path.join("lib", _python_lib_version(), "site-packages"),
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
def project(package_name, dirs=None, filespecs=None, cleanup=None, **kwargs):
    """
    Set up a mock Python project to create an environment from and change
    directory to it.

    :Args:
        package_name
            The name of the Python package the project contains.

        dirs
            (optional) a list of directories to create recursively.

        filespecs
            (optional) a dictionary in the form::

                {
                    relative_path:  text,
                    ...
                }

            where `relative_path` is a relative path to a file, and `text` is a
            string or string template to be written as the contents.  If
            `kwargs` is supplied, `text` will be written as
            ``text.format(**kwargs)``.

        cleanup
            (optional) a callable; if supplied, will be called on exiting the
            context manager before any other cleanup.

        kwargs
            (optional) additional keyword arguments used for formatting
            contents of files
    """
    try:
        if dirs is None:
            dirs = []
        if filespecs is None:
            filespecs = {}

        original_environ = os.environ
        os.environ = _clean_environ_copy(os.environ)

        original_cwd = os.getcwd()
        temp_dir = tempfile.TemporaryDirectory()
        os.chdir(temp_dir.name)

        with open("setup.py", "w") as f:
            f.write(SETUP_TEMPLATE.format(package_name=package_name))

        package_dir = _ensure_relative_path(package_name)
        os.mkdir(package_dir)

        with open(os.path.join(package_dir, "__init__.py"), "w"):
            pass  # empty file is ok

        for path in dirs:
            path = _ensure_relative_path(path)
            os.makedirs(os.path.dirname(path), exist_ok=True)

        for (path, contents) in filespecs.items():
            path = _ensure_relative_path(path)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as f:
                if kwargs:
                    contents = contents.format(**kwargs)
                f.write(contents)

        yield
    finally:
        if cleanup:
            cleanup()
        os.environ = original_environ
        os.chdir(original_cwd)
        temp_dir.cleanup()
