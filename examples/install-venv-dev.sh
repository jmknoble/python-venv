#!/bin/sh

set -e
set -u

# This uses [python-venv](https://github.com/jmknoble/python-venv)
# to create a Python virtual environmeent using 'pyenv'.
#
# Call this script with '-n' or '--dry-run' for a dry run,
# or with '-e' or '--env-name' to change the environment name.

set -x

./python-venv replace \
    -t pyenv \
    -r devplus \
    ${1:+"$@"}
