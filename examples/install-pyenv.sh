#!/bin/sh

set -e
set -u

# Call this script with '-n' or '--dry-run' for a dry run

set -x

./python-venv replace -t pyenv -r wheel ${1:+"$@"}
