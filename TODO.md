# TODO

## Code

This code is inelegant; it used to be a single script included with other
source.

- Command-line completion with `argcompletion`.
- Split virtual environment "smarts" into separate module(s), preferably using
  an abstract base class and derived concrete classes to implement.
- Possibly split requirements handling into its own module.
- Clean up the CLI argument parsing.
- Add `replace` command (`create --force`, with prompting).
- Write unit tests.


## Build

- CI pipeline


## Package

- Upload to PyPI
