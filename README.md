# python-venv

[![EditorConfig-enabled](https://img.shields.io/badge/EditorConfig-enabled-brightgreen?logo=EditorConfig&logoColor=white)](https://editorconfig.org/)
[![pre-commit-enabled](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
[![Python-3.7+](https://img.shields.io/badge/Python-3.7+-informational?logo=Python&logoColor=white)](https://www.python.org)
[![CodeStyle-black](https://img.shields.io/badge/CodeStyle-black-informational)](https://github.com/psf/black)


An opinionated but flexible Python virtual environment tool.

Enables straightforward creation, removal, or replacement of Python virtual
environments using [venv][], [pyenv-virtualenv][], or [conda][], using
predictable names/locations and flexible strategies.

Intended to be used by either developers or consumers of source-available
Python packages.


> [!WARNING]
>
> **python-venv** is deprecated and no longer maintained.
> Please use [uv](https://github.com/astral-sh/uv) instead.


[begintoc]: #

## Contents

- [Recent Changes](#recent-changes)
- [Requirements](#requirements)
- [Installation](#installation)
- [Invocation](#invocation)
- [Quick Start](#quick-start)
- [Types of Virtual Environments](#types-of-virtual-environments)
- [Installing Requirements](#installing-requirements)
    - [Opinionation and Devplus Requirements](#opinionation-and-devplus-requirements)
    - [Names and Some Flexibility](#names-and-some-flexibility)
    - [Basenames](#basenames)
    - [Environment Names](#environment-names)
    - [Changing the Current Directory](#changing-the-current-directory)
- [Python Interpreter](#python-interpreter)
    - [Specifying a Python Interpreter](#specifying-a-python-interpreter)
    - [Specifying a Python Version](#specifying-a-python-version)
- [Command-line Autocompletion](#command-line-autocompletion)
- [Backwards-Incompatible Changes](#backwards-incompatible-changes)
    - [Changes to Command-Line Flags](#changes-to-command-line-flags)
- [References](#references)

[endtoc]: # (Generated by markdown-toc pre-commit hook)


## Recent Changes

See [NEWS][].

For incompatible changes beginning in v0.7.0, see [Backwards-Incompatible
Changes](#backwards-incompatible-changes).


## Requirements

- A [Python][] interpreter, version 3.7 or later
- The Python packages listed in **requirements.txt**


## Installation

The recommended method of installing **python-venv** is to install it into a
virtual environment.  Currently installation from a wheelfile or from source
is supported.  Installing from a wheelfile is recommended.

**python-venv** can create the virtual environment and install itself for you.
For a [venv][] environment:

    python3 -m python_venv create -t venv -r wheel --dry-run

**python-venv** will say what it would do.  To actually do it, remove the
`--dry-run` argument:

    python3 -m python_venv create -t venv -r wheel

Similarly, for a [pyenv-virtualenv][] environment:

    python3 -m python_venv create -t pyenv -r wheel --dry-run
    python3 -m python_venv create -t pyenv -r wheel

Or, for a [conda][] environment:

    python3 -m python_venv create -t conda -r wheel --dry-run
    python3 -m python_venv create -t conda -r wheel


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

        python3 -m python_venv

Some of the above methods may differ for some command-line interpreters on
Windows.

For the remainder of this document, we will use `python-venv` to mean any of
the above methods.


## Quick Start

Create a Python virtual environment using [venv][] at `.venv` for the Python
source project in the current directory, using `requirements.txt` as the list
of requirements:

    python-venv create -t venv -r plain

Remove that virtual enviroment:

    python-venv remove -t venv

Create a [conda][] virtual environment named after the Python source project
in the current directory using `requirements.txt`:

    python-venv create -t conda -r plain

Remove that [conda][] environment:

    python-venv remove -t conda -r plain

Create a [pyenv-virtualenv][] environment for development, named after the
Python source project in the current directory, and using
`requirements_dev.txt`:

    python-venv create -t pyenv -r dev

Replace it with a new environment after updating `requirements_dev.txt`:

    python-venv replace -t pyenv -r dev

Display command-line help:

    python-venv --help


## Types of Virtual Environments

**python-venv** knows how to create virtual environments using:

- The [venv][] module built into Python 3.
- The [pyenv-virtualenv][] plugin for [pyenv][].
- The [conda][] tool that accompanies a [Miniconda][] or [Anaconda][] Python
  distribution.

Use the `-t` or `--env-type` option to say what type of virtual environment to
create or remove.

> :pushpin: ***NOTE:***
>
> **Python-venv** can create "anonymous" `venv` environments in a predictably
> named folder under the current directory, or `named-venv` environments in a
> dedicated directory and named after the Python source project in the current
> directory.  See [Names and Some Flexibility](#names-and-some-flexibility)
> for more about this.


## Installing Requirements

**python-venv** understands several different opinionated ways of specifying
what to install into a virtual environment ("requirement schemes"):

- **Plain** -- using a `requirements.txt` file.
- **Frozen** -- using frozen requirements (from `pip freeze`) in a
  `requirements_frozen.txt` file.
- **Package** -- using the name of the Python source project in the current
  directory as a package to `pip install`.
- **Pip** -- using the additional arguments on the command line as arguments
  to `pip install`.
- **Source** -- using the Python source project in the current directory as a
  thing to build via `python3 -m build --sdist` and then installing the
  resulting source distrbution using `pip`.
- **Wheel** -- using the Python source project in the current directory as a
  thing to build via `python3 -m build` and then installing the
  resulting wheelfile using `pip`.
- **Dev** -- using a `requirements_dev.txt` file.
- **Devplus** -- using a combination of requirements files to install packages
  as a development environment for the Python source project in the current
  directory.

These schemes correspond roughly to the following:

| Kind of Requirements | Corresponding Install Command |
|----------------------|-------------------------------|
| plain | `pip install -r requirements.txt` |
| frozen | `pip install -r requirements_frozen.txt` |
| package | `pip install this-package-name` |
| pip | `pip install ARG1 ARG2 ...` |
| source | `python3 -m build --sdist && pip install SDIST` |
| wheel | `python3 -m build && pip install WHEELFILE` |
| dev | `pip install -r requirements_dev.txt` |
| devplus | `pip install -r requirements.txt -r dev/requirements_build.txt -r dev/requirements_dev.txt -r dev/requirements_test.txt` |

> :pushpin: ***NOTE:***
> _Prior to v0.7.0, the `devplus` requirement scheme was known as `dev`, and
> there was no generic `dev` equivalent._

> :pushpin: ***NOTE:***
> _Prior to v0.7.0, the `-P` command-line argument meant `--package`.  Now it
> means `--pip`._

> :star: ***HINT:***
> _When using `--pip`, to keep **python-venv** from misinterpreting
> **pip** requirements as options, Use plain dashes (`--`) as the first
> additional argument on the command line.  For example:_
>
>     python-venv create -t venv -r pip -e .venv -- -r my-requirements.txt


### Opinionation and Devplus Requirements

**python-venv** creates `devplus` environments from the following requirements
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

**Python-venv**'s main purpose in life is to create or re-create Python
environments in a predictable way using a single command.  It uses one of two
approaches or *naming schemes:*

- *Anonymous* environments with a predictable name in the current directory.
- *Named* environments in a dedicated directory and named using a *basename*.

Which naming scheme **python-venv** uses depends on the environment type:

| Environment Type | Naming Scheme | Example |
|------------------|----------|---------|
| venv | anonymous | `./.venv` |
| named-venv | named | `~/.venvs/python-venv` |
| conda | named | `<CONDA_PREFIX>/envs/python-venv` |
| pyenv | named | `<PYENV_ROOT>/<VERSION>/envs/python-venv` |


### Basenames

In the named environment examples above, `python-venv` is the *basename*.  The
default basename comes from the Python source project in the current directory
(`python3 setup.py --name`), with underscores replaced by hyphens (for this
Python project, that works out to `python-venv`).

The basename is used for:

- The name of non-`dev` named environments as-is.
- The name of `dev` and `devplus` named environments, with a `-dev` suffix
  added (`python-venv-dev`).
- The name of the Python package to install for `package` environments.

You can choose your own basename using the `--basename` option; this will
keep **python-venv** from trying to use `setup.py` to find the name:

    python-venv create -t named-venv -r dev --basename python-venv-0.1.0
    python-venv create -t pyenv -r plain --basename requirements-test
    python-venv create -t venv -r package --basename mypackage


### Environment Names

You can also choose your own environment name using the `--env-name` option if
you want a different environment name:

    python-venv create -t conda -r plain --env-name myenv
    python-venv create -t pyenv -r dev --env-name myenv-development
    python-venv create -t named-venv -r devplus --venvs-dir ~/.venvs-dev --env-name myenv

Or, if you are using `venv` environments, if you want your virtual environment
somewhere besides `.venv`:

    python-venv create -t venv -r plain --env-name .python-env
    python-venv create -t venv -r plain --env-name /path/to/myenv


### Changing the Current Directory

If the place you're running `python-venv` from is not the spot where the
Python source project is that you want to act on, you can tell `python-venv`
to change directories before doing anything using the `-C`/`--cd` option:

    python-venv create -t venv -r plain --cd /some/other/dir


## Python Interpreter

Typical Python setups, with a "system" Python and possibly either an
[Anaconda][]/[Miniconda][] or a [pyenv][] install, will generally work well
with **python-venv**, whether you're creating stock [venv][] environments or
something more esoteric.  But there are times when you may need more control
over:

- What Python interpreter you use to create [venv][] environments.
- What the name of the Python interpreter is inside your virtual environment.
- What Python interpreter version to place into your [conda][] environment.

**python-venv** tries to help with that.


### Specifying a Python Interpreter

Use the `--python` option to tell **python-venv** to use a specific Python
interpreter.  The default is `python3`.

You may supply either a _base command name_, like `python3`, or a _full path_,
like `/usr/bin/python3`.

If you supply a **base command name**:

- The command is looked for on the PATH, and the first matching command is
  used for Python commands that create virtual environments (such as `python3
  -m venv ...`).
- The base command name is also used to refer to the Python interpreter
  _inside_ the virtual environment, for running Python commands after the
  virtual environment has been created (such as `/path/to/your/env/bin/python3
  -m pip install ...`).

If you supply a **full path**:

- The path is used as-is for Python commands that create virtual environments.
  For example, `/usr/local/bin/mypython -m venv ...`.
- The _base command name_ from the full path is used to refer to the Python
  interpreter inside the virtual environment.  For example,
  `/path/to/your/env/bin/mypython -m pip install ...`.

You may choose a different default value for `--python` by setting the
`PYTHON_VENV_USE_PYTHON` environment variable.  For example, with the Bash
shell:

    export PYTHON_VENV_USE_PYTHON=/usr/local/bin/mypython


### Specifying a Python Version

`conda create` allows (in fact, requires) you to specify a Python version when
creating a [conda][] environment.  The default is `python=3`, selecting the
latest Python 3 version available.  If you want more control over that, use
the `--python-version` option and specify a conda-compatible version.  For
example:

    python-venv create --conda --python-version 3.8 ...

`pyenv` also allows choosing a Python version to run.  When creating a `pyenv`
environment, you can use the `--python-version` option to choose one of the
versions listed by `pyenv versions`.  Examples:

    python-venv create --pyenv --python-version 3.9.7 ...
    python-venv create --pyenv --python-version system ...

This option only works with the `create` and `replace` subcommands (a Python
interpreter is not invoked when removing environments), and only for `conda`
and `pyenv` environments.  

> :star: ***HINT:***
> _Use the `--python` option if you need to select a specific Python version
> for `venv` environments._

You may choose a default value for for `--python-version` by setting the
`PYTHON_VENV_USE_PYTHON_VERSION` environment variable.  For example, with the
Bash shell:

    export PYTHON_VENV_USE_PYTHON_VERSION=3.9.7


## Command-line Autocompletion

**python-venv** provides command-line [autocompletion][] for the [Bash][]
command-line shell and compatible shells, using the
[argcomplete][argcomplete-pypi] Python package.

For instructions on how to enable completion:

    python-venv completion


## Backwards-Incompatible Changes

### Changes to Command-Line Flags

As of v0.7.0, there are a few significant changes to command-line flags:

| Old (pre-0.7.0) | New (post-0.7.0) | Description |
|-----------------|------------------|-------------|
| `-d`, `--dev`, `-r dev` | `-D`, `--devplus`, `-r devplus` | Opinionated dev requirements |
| *nothing* | `-d`, `--dev`, `-r dev` | Generic `requirements_dev.txt` |
| `-P`, `--package`, `-r package` | `--package`, `-r package` | Install a package named like the current Python project | 
| *nothing* | `-P`, `--pip`, `-r pip` | Install packages/wheels/pip requirements named on the command line |


## References

- [conda][]
- [pyenv][]
    - [pyenv-virtualenv][]
    - [Managing Multiple Python Versions With pyenv][pyenv-article]
- [venv][]
- argcomplete on [PyPI][argcomplete-pypi] and [GitHub][argcomplete-github]
- build on [PyPI][build]


 [Anaconda]: https://www.anaconda.com/products/individual
 [argcomplete-pypi]: https://pypi.org/project/argcomplete/
 [argcomplete-github]: https://github.com/kislyuk/argcomplete
 [autocompletion]: https://en.wikipedia.org/wiki/Autocomplete
 [Bash]: https://en.wikipedia.org/wiki/Bash_(Unix_shell)
 [build]: https://pypi.org/project/build/
 [conda]: https://docs.conda.io/en/latest/
 [Miniconda]: https://docs.conda.io/en/latest/miniconda.html
 [NEWS]: NEWS.md
 [Python]: https://www.python.org/
 [pyenv]: https://github.com/pyenv/pyenv
 [pyenv-article]: https://realpython.com/intro-to-pyenv/
 [pyenv-virtualenv]: https://github.com/pyenv/pyenv-virtualenv
 [setuptools]: https://pypi.org/project/setuptools/
 [wheel]: https://pypi.org/project/wheel/
 [venv]: https://docs.python.org/3/library/venv.html
