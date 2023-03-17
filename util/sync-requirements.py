#!/usr/bin/env python3

from __future__ import print_function

import configparser
import difflib
import os.path
import sys

import utilutil.argparsing as argparsing

STATUS_NO_CHANGE = 0
STATUS_ERROR = 1
STATUS_CHANGED = 100

FILE_TYPE = "file_type"
FILE_SECTION = "section"
FILE_KEY = "key"
FILE_ENABLED = "enabled"

REQUIREMENTS_FILES = {
    "setup.cfg": {
        FILE_TYPE: "configparser",
        FILE_SECTION: "options",
        FILE_KEY: "install_requires",
        FILE_ENABLED: True,
    },
    "requirements.txt": {
        FILE_TYPE: "text",
        FILE_SECTION: None,
        FILE_KEY: None,
        FILE_ENABLED: True,
    },
    # TODO:  Add TOML support
    "pyproject.toml": {
        FILE_TYPE: "toml",
        FILE_SECTION: "project",
        FILE_KEY: "dependencies",
        FILE_ENABLED: False,
    },
}

KNOWN_REQUIREMENTS_FILES = [
    # pylint: disable=consider-using-dict-items
    x
    for x in REQUIREMENTS_FILES
    if REQUIREMENTS_FILES[x][FILE_ENABLED]
]

DESCRIPTION = (
    "Synchronize Python requirements (dependencies) between "
    "files having different formats."
)


def _get_config_parser():
    return configparser.ConfigParser(
        allow_no_value=True, strict=True, empty_lines_in_values=True, interpolation=None
    )


def _read_ini_file(filename, section, key):
    config = _get_config_parser()
    config.read(filename)
    if section in config.sections() and key in config[section].keys():
        requirements = config[section][key].strip().split("\n")
    else:
        requirements = None
    return requirements


def _write_ini_file(filename, section, key, requirements_list):
    config = _get_config_parser()
    if os.path.exists(filename):
        config.read(filename)
    if section not in config.sections():
        config[section] = {}
    if requirements_list:
        requirements_list = [""] + requirements_list + [""]
    requirements = "\n".join(requirements_list)
    config[section][key] = requirements
    with open(filename, "w", encoding="utf-8") as outfile:
        config.write(outfile)


def _read_text_file(filename):
    requirements = []
    with open(filename, "r", encoding="utf-8") as infile:
        for line in infile:
            requirements.append(line.strip())
    return requirements


def _write_text_file(filename, requirements_list):
    if requirements_list:
        requirements_list = requirements_list + [""]
    with open(filename, "w", encoding="utf-8") as outfile:
        outfile.write("\n".join(requirements_list))


def _read_requirements(filename, file_type, section, key, **_kwargs):
    requirements = None
    if file_type == "configparser":
        requirements = _read_ini_file(filename, section, key)
    elif file_type == "text":
        requirements = _read_text_file(filename)
    else:
        raise RuntimeError(f"Unhandled file type for {filename}: {file_type}")
    return requirements


def _write_requirements(filename, requirements, file_type, section, key, **_kwargs):
    if file_type == "configparser":
        _write_ini_file(filename, section, key, requirements)
    elif file_type == "text":
        _write_text_file(filename, requirements)
    else:
        raise RuntimeError(f"Unhandled file type for {filename}: {file_type}")


def _message(message, dry_run_message, dry_run):
    if dry_run:
        print("[DRY-RUN]", dry_run_message)
    else:
        print(message)


# pylint: disable=unused-argument
def _verbose_message(message, dry_run_message, dry_run, verbose, quiet):
    if verbose:
        _message(message, dry_run_message, dry_run)


# pylint: disable=unused-argument
def _normal_message(message, dry_run_message, dry_run, verbose, quiet):
    if not quiet:
        _message(message, dry_run_message, dry_run)


def _error_message(message):
    print("error:", message, file=sys.stderr, flush=True)


def _sync_requirements(
    source_file, source_info, target_file, target_info, diff, dry_run, verbose, quiet
):
    message = f"Reading requirements from {source_file} ..."
    _verbose_message(message, message, dry_run, verbose, quiet)
    source_requirements = _read_requirements(source_file, **source_info)
    message = f"Reading requirements from {target_file} ..."
    target_requirements = _read_requirements(target_file, **target_info)
    if source_requirements == target_requirements:
        message = "Source and target requirements are the same."
        _normal_message(message, message, dry_run, verbose, quiet)
        status = STATUS_NO_CHANGE
    else:
        template = f"{{verb}} requirements to {target_file} ..."
        _normal_message(
            template.format(verb="Syncing"),
            template.format(verb="Would sync"),
            dry_run,
            verbose,
            quiet,
        )
        if not dry_run:
            _write_requirements(target_file, source_requirements, **target_info)
        if diff:
            differences = difflib.unified_diff(
                target_requirements,
                source_requirements,
                fromfile=target_file,
                tofile=source_file,
                lineterm="",
            )
            print("\n".join(differences))
        status = STATUS_CHANGED
    return status


def _add_arguments(argparser):
    """Add command-line arguments to an argument parser"""
    argparsing.add_dry_run_argument(argparser)
    argparser.add_argument(
        "-d",
        "--diff",
        action="store_true",
        help="Show what requirements differ between SOURCE and TARGET, without syncing",
    )
    chattiness_args = argparser.add_mutually_exclusive_group()
    chattiness_args.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help=(
            "Only print error messagess; "
            "use exit status to indicate whether requirements differ"
        ),
    )
    chattiness_args.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Say everything that is happening",
    )
    argparser.add_argument(
        "source",
        metavar="SOURCE",
        choices=KNOWN_REQUIREMENTS_FILES,
        help=(
            "File containing source of truth for requirements " "(one of {choices})"
        ).format(choices=KNOWN_REQUIREMENTS_FILES),
    )
    argparser.add_argument(
        "target",
        metavar="TARGET",
        choices=KNOWN_REQUIREMENTS_FILES,
        help="File to sync requirements to (one of {choices})".format(
            choices=KNOWN_REQUIREMENTS_FILES
        ),
    )
    return argparser


def main(*argv):
    """Do the thing"""
    (prog, argv) = argparsing.grok_argv(argv)
    argparser = argparsing.setup_argparse(prog=prog, description=DESCRIPTION)
    _add_arguments(argparser)
    args = argparser.parse_args(argv)

    source_info = REQUIREMENTS_FILES[args.source]
    target_info = REQUIREMENTS_FILES[args.target]

    status = _sync_requirements(
        args.source,
        source_info,
        args.target,
        target_info,
        diff=args.diff,
        dry_run=args.dry_run,
        verbose=args.verbose,
        quiet=args.quiet,
    )

    return status


if __name__ == "__main__":
    sys.exit(main(*sys.argv))
