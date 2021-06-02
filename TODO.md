# TODO

## Code

This code is inelegant; it used to be a single script included with other
source.

- Split virtual environment "smarts" into separate module(s), preferably using
  an abstract base class and derived concrete classes to implement.
- Possibly split requirements handling into its own module.
- Clean up the CLI argument parsing.
- Write unit tests.


## Build

- CI pipeline


## Package

- Upload to PyPI
