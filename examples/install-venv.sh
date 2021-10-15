#!/bin/sh

set -e
set -u

# This uses [python-venv](https://github.com/jmknoble/python-venv)
# to create a Python virtual environmeent using 'python3 -m venv'.
#
# Call this script with '-n' or '--dry-run' for a dry run,
# or with '-e' or '--env-name' to change the environment name.

set -x

./python-venv replace \
    -t named-venv \
    -r wheel \
    ${1:+"$@"}
