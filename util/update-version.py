#!/usr/bin/env python3

from __future__ import print_function

import configparser
import os.path
import sys

import utilutil.argparsing as argparsing
import utilutil.runcommand as runcommand

BUMPVERSION_CONFIG_FILES = [
    ".bumpversion.cfg",
    "setup.cfg",
]
BUMPVERSION_BASE_COMMAND = [
    "python3",
    "-m",
    "bumpversion",
    "--no-commit",
    "--no-tag",
]

DEFAULT_VERSION_FILENAME = "VERSION"
DEFAULT_STABLE_VERSION_FILENAME = "STABLE_VERSION"

DESCRIPTION = (
    "Compare project version with stable version, and "
    "modify project version to be a dev or pre-release "
    "version if they do not match."
)

RELEASE_TYPES = [
    "dev",
    "a",
    "alpha",
    "b",
    "beta",
    "c",
    "pre",
    "preview",
    "rc",
]

RELEASE_TYPES_REQUIRING_SEPARATOR = {"dev"}


def _get_version_from_file(version_file):
    """Return the version as read from `version_file`"""
    version = version_file.read().lstrip().splitlines()
    if not version:
        raise RuntimeError(
            "{path}: version file appears to be blank".format(path=version_file.path)
        )
    return version[0].rstrip()


def _bumpversion_in_use():
    """Tell whether a `bump2version`:py:mod: is in use."""
    for config_filename in BUMPVERSION_CONFIG_FILES:
        if os.path.exists(config_filename):
            config_file = configparser.ConfigParser()
            config_file.read(config_filename)
            if "bumpversion" in config_file:
                return True
    return False


def _write_version(version_filename, new_version, dry_run):
    if _bumpversion_in_use():
        bumpversion_command = BUMPVERSION_BASE_COMMAND + [
            "--new-version",
            new_version,
            "patch",
        ]
        runcommand.run_command(
            bumpversion_command,
            check=True,
            show_trace=True,
            dry_run=dry_run,
        )
    elif not dry_run:
        with open(version_filename, "w", encoding="utf-8") as version_file:
            version_file.write(new_version + "\n")


def _add_arguments(argparser):
    """Add command-line arguments to an argument parser"""
    argparsing.add_dry_run_argument(argparser)
    argparser.add_argument(
        "-b",
        "--build-number",
        dest="build_number",
        action="store",
        default=None,
        required=True,
        help="Numeric suffix for dev or pre-release",
    )
    argparser.add_argument(
        "-t",
        "--release-type",
        dest="release_type",
        action="store",
        choices=RELEASE_TYPES,
        default=None,
        required=True,
        help="Type of release",
    )
    argparser.add_argument(
        "-f",
        "--version-file",
        dest="version_file",
        action="store",
        default=DEFAULT_VERSION_FILENAME,
        help="File containing version (default: '{default}' in current dir)".format(
            default=DEFAULT_VERSION_FILENAME
        ),
    )
    argparser.add_argument(
        "-F",
        "--stable-version-file",
        dest="stable_version_file",
        action="store",
        default=DEFAULT_STABLE_VERSION_FILENAME,
        help=(
            "File containing stable version " "(default: '{default}' in current dir)"
        ).format(default=DEFAULT_STABLE_VERSION_FILENAME),
    )
    return argparser


def main(*argv):
    """Do the thing"""
    (prog, argv) = argparsing.grok_argv(argv)
    argparser = argparsing.setup_argparse(prog=prog, description=DESCRIPTION)
    _add_arguments(argparser)
    args = argparser.parse_args(argv)

    with open(args.version_file, "r", encoding="utf-8") as version_file:
        current_version = _get_version_from_file(version_file)

    with open(args.stable_version_file, "r", encoding="utf-8") as stable_version_file:
        stable_version = _get_version_from_file(stable_version_file)

    if current_version == stable_version:
        runcommand.print_trace(
            [
                "Current version matches stable version, leaving unchanged:",
                current_version,
            ],
            trace_prefix="",
            dry_run=args.dry_run,
        )
    else:
        sep = "." if args.release_type in RELEASE_TYPES_REQUIRING_SEPARATOR else ""
        new_version = "".join(
            [current_version, sep, args.release_type, args.build_number]
        )
        runcommand.print_trace(
            ["Updating current version from", current_version, "to", new_version],
            trace_prefix="",
            dry_run=args.dry_run,
        )
        _write_version(args.version_file, new_version, dry_run=args.dry_run)

    return 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv))
