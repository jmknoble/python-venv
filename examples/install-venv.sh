#!/bin/sh

set -e
set -u

# This uses [python-venv](https://github.com/jmknoble/python-venv)
# to create a Python virtual environmeent using 'python3 -m venv'.
#
# Call this script with '-n' or '--dry-run' for a dry run

ENV_NAME="${ENV_NAME:-python-venv}"
VENV_DIR="${VENV_DIR:-${HOME}/.venvs}"
USE_PYTHON="${USE_PYTHON:-/usr/bin/python3}"

case "${USE_PYTHON}" in
    none|default)
        USE_PYTHON=""
        ;;
esac

set -x

mkdir -p "${VENV_DIR}"

./python-venv replace \
    -t venv \
    -r wheel \
    -e "${VENV_DIR}/${ENV_NAME}" \
    ${USE_PYTHON:+--python "${USE_PYTHON}"} \
    ${1:+"$@"}
