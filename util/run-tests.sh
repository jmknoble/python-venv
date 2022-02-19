#!/bin/sh

set -e
set -u

# https://docs.python.org/3/library/unittest.html#test-discovery

set -x
python3 -m unittest discover -s tests -t . -v
