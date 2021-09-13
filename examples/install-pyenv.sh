#!/bin/sh

set -e
set -u

# This uses [python-venv](https://github.com/jmknoble/python-venv)
# to create a Python virtual environmeent using 'pyenv'.
#
# Call this script with '-n' or '--dry-run' for a dry run

ENV_NAME="${ENV_NAME:-}"

set -x

./python-venv replace \
    -t pyenv \
    -r wheel \
    ${ENV_NAME:+-e "${ENV_NAME}"} \
    ${1:+"$@"}
