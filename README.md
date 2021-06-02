# python-venv

[![EditorConfig-enabled](https://img.shields.io/badge/EditorConfig-enabled-brightgreen?logo=EditorConfig&logoColor=white)](https://editorconfig.org/)
[![pre-commit-enabled](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
[![Python-3.7+](https://img.shields.io/badge/Python-3.6+-informational?logo=Python&logoColor=white)](https://www.python.org)
[![CodeStyle-black](https://img.shields.io/badge/CodeStyle-black-informational)](https://github.com/psf/black)


An opinionated but flexible Python virtual environment tool.

Enables straightforward creation, removal, or replacement of Python virtual
environments using either [venv][] or [conda][], using predictable
names/locations and flexible strategies.

Intended to be used by either developers or consumers of source-available
Python packages.


[begintoc]: #

## Contents

- [Requirements](#requirements)
- [Installation](#installation)
- [Invocation](#invocation)
- [Quick Start](#quick-start)
- [Types of Virtual Environments](#types-of-virtual-environments)
- [Installing Requirements](#installing-requirements)
    - [Opinionation and Development Environments](#opinionation-and-development-environments)
    - [Names and Some Flexibility](#names-and-some-flexibility)
- [References](#references)

[endtoc]: # (Generated by markdown-toc pre-commit hook)


## Requirements

- A [Python](https://www.python.org/) interpreter, version 3.7 or later
- The Python packages listed in **requirements.txt**


## Installation

The recommended method of installing **python-venv** is to install it into a
virtual environment.  Currently only installation from source is supported,
(unless you build your own packages using `python setup.py bist_wheel`).

**python-venv** can create the virtual environment and install itself for you.
For a [venv][] environment:

    python3 -m python_venv create -t venv -r source --dry-run

**python-venv** will say what it would do.  To actually do it, remove the
`--dry-run` argument:

    python3 -m python_venv create -t venv -r source

For a [conda][] environment:

    python -m python_venv create -t conda -r source --dry-run

and to actually do it:

    python -m python_venv create -t conda -r source


## Invocation

**python-venv** may be invoked in a few different ways:

- Before installation, using the executable script in the top of the source
  directory:

        ./python-venv

- After installation into a Python virtual environment and activation of that
  environment, using the executable script:

        python-venv

- Using the Python interpreter, either from the source directory or from an
  activated virtual enviroment where **python-venv** has been installed:

        python -m python_venv

For the remainder of this document, we will use `python-venv` to mean any of
those methods.


## Quick Start

Create a Python virtual environment using [venv][] at `.venv` for the Python
project in the current directory, using `requirements.txt` as the list of
requirements:

    python-venv create -t venv -r plain

Remove that virtual enviroment:

    python-venv remove -t venv

Create a [conda][] virtual environment nameed after the Python project in the
current directory using `requirements.txt`:

    python-venv create -t conda -r plain

Remove that [conda][] environment:

    python-venv remove -t conda -r plain

Display command-line help:

    python-venv --help


## Types of Virtual Environments

**python-venv** knows how to create virtual environments using:

- The [venv][] module built into Python 3.
- The [conda][] tool that accompanies a [Miniconda][] or [Anaconda][] Python
  distribution.

Use the `-t` or `--env-type` option to say what type of virtual environment to
create or remove.


## Installing Requirements

**python-env** understands several different opinionated ways of specifying
what to install into a virtual environment:

- **Plain** -- using a `requirements.txt` file.
- **Frozen** -- using frozen requirements (from `pip freeze`) in a
  `requirements_frozen.txt` file.
- **Package** -- using the name of the Python project in the current directory
  as a package to `pip install`.
- **Source** -- using the Python project in the current directory as a thing
  to install via `python setup.py install`.
- **Dev** -- using a combination of requirements files to install packages as
  a development environment for the Python project in the current directory.

These methods correspond roughly to the following:

| Kind of Requirements | Corresponding Install Command |
|----------------------|-------------------------------|
| plain | `pip install -r requirements.txt` |
| frozen | `pip install -r requirements_frozen.txt` |
| package | `pip install this-package-name` |
| source | `python3 setup.py install` |
| dev | `pip install -r requirements.txt -r dev/requirements_build.txt -r dev/requirements_dev.txt -r dev/requirements_test.txt` |


### Opinionation and Development Environments

**python-venv** creates `dev` environments from the following requirements
files that correspond to arguments of the `setup()` call in `setup.py`:

| Requirements | `setup()` argument | Purpose |
|--------------|--------------------|---------|
| requirements.txt | `install_requires` | Runtime requirements |
| dev/requirements_dev.txt | `setup_requires` | Requirements for developing |
| dev/requirements_test.txt | `tests_require` | Requirements for running tests |
| dev/requirements_build.txt | _None_ | Requirements for building packages |

This is the scheme followed by **python-venv**'s `setup.py`.  It's quite
likely it may not work well for everyone.


### Names and Some Flexibility

Part of **python-venv**'s purpose in life is to create or re-create Python
environments in a predictable way using a single command.

The default "base name" comes from the Python project in the current directory
(`python setup.py --name`), with underscores replaced by hyphens (that is,
`python-venv` for this Python project).

This base name is used for:

- The name of non-`dev` [conda][] environments as-is.
- The name of `dev` [conda][] environments with a `-dev` suffix
  (`python-venv-dev`).
- The name of the Python package to install for `package` environments.

You can choose your own base name using the `--basename` option; this will
keep **python-env** from trying to use `setup.py` to find the name:

    python-venv create -t conda -r dev --basename python-venv-0.1.0
    python-venv create -t venv -r package --basename mypackage

You can also choose your own environment name using the `--env-name` option if
you want a different environment name:

    python-venv create -t conda -r plain --env-name myenv

Or, if you are using `venv` environments, if you want your virtual environment
somewhere besides `.venv`:

    python-venv create -t venv -r plain --env-name ~/.venvs/myenv


## References

- [conda][]
- [venv][]


 [Anaconda]: https://www.anaconda.com/products/individual
 [conda]: https://docs.conda.io/en/latest/
 [Miniconda]: https://docs.conda.io/en/latest/miniconda.html
 [venv]: https://docs.python.org/3/library/venv.html
