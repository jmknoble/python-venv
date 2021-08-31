"""Provide a command-line interface for `~python_venv`:py:mod:."""

import argparse
import re
import sys

try:
    import argcomplete
except ModuleNotFoundError:
    # Enable running without autocompletion
    pass

from . import argparsing, completion, const, env, exceptions, get_version, reqs

COMMAND_CREATE = "create"
COMMAND_REMOVE = "remove"
COMMAND_REPLACE = "replace"
COMMAND_COMPLETION = "completion"

COMMANDS = {
    COMMAND_CREATE: {
        "help": "Create a Python virtual environment",
        "aliases": ["new"],
        "req_scheme_required": True,
    },
    COMMAND_REMOVE: {
        "help": "Remove a Python virtual environment",
        "aliases": ["rm"],
        "req_scheme_required": False,
    },
    COMMAND_REPLACE: {
        "help": "Remove and re-create a Python virtual environment",
        "req_scheme_required": True,
    },
    COMMAND_COMPLETION: {
        "help": "Set up shell command-line autocompletion",
    },
}

VENV_COMMANDS = [
    COMMAND_CREATE,
    COMMAND_REMOVE,
    COMMAND_REPLACE,
]

VENV_CREATE_COMMANDS = [
    COMMAND_CREATE,
    COMMAND_REPLACE,
]

DESCRIPTION_MAIN = f"""
Create or remove a Python virtual environment for the Python project in the
current directory.  We expect a 'setup.py' to exist, along with requirements in
'{reqs.REQUIREMENTS_PLAIN}', '{reqs.REQUIREMENTS_FROZEN}', '{reqs.REQUIREMENTS_DEV}',
and '{reqs.REQUIREMENTS_TEST}'.

Venv virtual environments are created in '{env.VENV_DIR}'.

Conda virtual environments are created using the name of the Python project
(via '{const.PYTHON} setup.py --name'), with underscores ('_') replaced by hyphens ('-')
and with '{env.DEV_SUFFIX}' appended for development environments.
"""

DESCRIPTION_CREATE = """
Create a Python virtual environment for the Python project in the current
directory.
"""

DESCRIPTION_REMOVE = """
Remove a Python virtual environment for the Python project in the current
directory.
"""

DESCRIPTION_REPLACE = """
Remove a Python virtual environment for the Python project in the current
directory, if one exists, and then create or re-create it.
"""

DESCRIPTION_COMPLETION = """
Set up shell command-line autocompletion.  When called with no arguments,
print instructions for enabling autocompletion.
"""


def _add_subcommands(argparser, commands, dest="command"):
    subcommands = {}
    subparsers = argparser.add_subparsers(title="subcommands", dest=dest)
    for (command, properties) in commands.items():
        subcommands[command] = subparsers.add_parser(
            command,
            aliases=properties.get("aliases", []),
            description=properties.get("description"),
            help=properties["help"],
        )
        subcommands[command].set_defaults(func=properties.get("func", None))
    return subcommands


def _add_venv_arguments(argparser, req_scheme_required=False, **_kwargs):
    argparsing.add_dry_run_argument(argparser)

    argparser.add_argument(
        "-b",
        "--basename",
        action="store",
        default=None,
        help=(
            f"Base name to use when inferring environment name or package name "
            f"(default: the result of '{const.PYTHON} setup.py --name', with "
            f"underscores replaced by hyphens)"
        ),
    )

    req_scheme_group = argparser.add_argument_group(title="requirements options")
    req_scheme_mutex_group = req_scheme_group.add_mutually_exclusive_group(
        required=req_scheme_required
    )
    req_scheme_mutex_group.add_argument(
        "-r",
        "--requirements",
        action="store",
        dest="req_scheme",
        choices=reqs.ALL_REQ_SCHEMES,
        default=None,
        help=(
            "Requirements to use for virtual environment "
            "(equivalent to the other requirements options below)"
        ),
    )
    req_scheme_mutex_group.add_argument(
        "-p",
        f"--{reqs.REQ_SCHEME_PLAIN}",
        action="store_const",
        dest="req_scheme",
        const=reqs.REQ_SCHEME_PLAIN,
        help=f"Virtual environment uses '{reqs.REQUIREMENTS_PLAIN}'",
    )
    req_scheme_mutex_group.add_argument(
        "-d",
        f"--{reqs.REQ_SCHEME_DEV}",
        action="store_const",
        dest="req_scheme",
        const=reqs.REQ_SCHEME_DEV,
        help=(
            f"Virtual environment is for development; uses "
            f"'{reqs.REQUIREMENTS_PLAIN}', '{reqs.REQUIREMENTS_DEV}', and "
            f"'{reqs.REQUIREMENTS_TEST}'"
        ),
    )
    req_scheme_mutex_group.add_argument(
        "-z",
        f"--{reqs.REQ_SCHEME_FROZEN}",
        action="store_const",
        dest="req_scheme",
        const=reqs.REQ_SCHEME_FROZEN,
        help=f"Virtual environment uses '{reqs.REQUIREMENTS_FROZEN}'",
    )
    req_scheme_mutex_group.add_argument(
        "-P",
        f"--{reqs.REQ_SCHEME_PACKAGE}",
        action="store_const",
        dest="req_scheme",
        const=reqs.REQ_SCHEME_PACKAGE,
        help="Virtual environment uses 'pip install BASENAME'",
    )
    req_scheme_mutex_group.add_argument(
        "-s",
        f"--{reqs.REQ_SCHEME_SOURCE}",
        action="store_const",
        dest="req_scheme",
        const=reqs.REQ_SCHEME_SOURCE,
        help=("Virtual environment uses '{command}'").format(
            command=" ".join(reqs.REQUIREMENTS_SOURCE).format(python=const.PYTHON)
        ),
    )

    venv_group = argparser.add_argument_group(title="environment options")
    venv_mutex_group = venv_group.add_mutually_exclusive_group(required=True)
    venv_mutex_group.add_argument(
        "-t",
        "--type",
        action="store",
        dest="env_type",
        choices=const.ENV_TYPES,
        help="The type of environment to create",
    )
    venv_mutex_group.add_argument(
        "-v",
        f"--{const.ENV_TYPE_VENV}",
        action="store_const",
        dest="env_type",
        const=const.ENV_TYPE_VENV,
        help=f"Same as '--type {const.ENV_TYPE_VENV}'",
    )
    venv_mutex_group.add_argument(
        "-c",
        f"--{const.ENV_TYPE_CONDA}",
        action="store_const",
        dest="env_type",
        const=const.ENV_TYPE_CONDA,
        help=f"Same as '--type {const.ENV_TYPE_CONDA}'",
    )

    venv_group.add_argument(
        "-e",
        "--env-name",
        action="store",
        default=None,
        help=(
            "Name of (or path to) virtual environment "
            "(default: '.venv' for venv environments, or "
            "inferred from BASENAME for conda environments)"
        ),
    )

    return argparser


def _add_force_arguments(argparser, **_kwargs):
    argparser.add_argument(
        "--force",
        action="store_true",
        help="Do not prompt for confirmation",
    )
    return argparser


def _add_python_version_arguments(argparser, **_kwargs):
    argparser.add_argument(
        "--python-version",
        metavar="X.Y",
        action="store",
        default=None,
        help="Python version to use when creating conda environment",
    )
    return argparser


def _add_completion_arguments(argparser, **_kwargs):
    argparser.add_argument(
        "--bash",
        action="store_true",
        help="Print autocompletion code for Bash-compatible shells",
    )
    argparser.add_argument(
        "--absolute",
        action="store_true",
        help=(
            "Normally, autocompletion works for commands that are on the PATH "
            "and have no specific location (that is, the shell finds them). "
            "With this option, set up autocompletion for a command that "
            "already has an absolute ('/path/to/...') or relative ('./...') "
            "location."
        ),
    )
    return argparser


def _add_version_arguments(prog, argparser, **_kwargs):
    argparser.add_argument(
        "-V",
        "--version",
        action="version",
        version=get_version(prog),
    )
    return argparser


def _check_create_args(args):
    if args.python_version is not None:
        if args.env_type != const.ENV_TYPE_CONDA:
            raise RuntimeError(
                "'--python-version' only makes sense with '--type conda'"
            )
        if re.match(const.PYTHON_VERSION_REGEX, args.python_version) is None:
            raise RuntimeError(
                f"--python-version: {args.python_version}: must start with a "
                "major, major.minor, or major.minor.micro version "
                "(example: --python-version 3.9)"
            )


def _get_virtual_env(args):
    kwargs = {
        "dry_run": args.dry_run,
        "force": args.force,
        "python": const.PYTHON,
        "basename": args.basename,
        "env_name": args.env_name,
    }
    try:
        if args.python_version is not None:
            kwargs["python_version"] = args.python_version
    except AttributeError:  # args.python_version may not exist
        pass

    if args.env_type == const.ENV_TYPE_VENV:
        virtual_env = env.VenvEnvironment(args.req_scheme, **kwargs)
    elif args.env_type == const.ENV_TYPE_CONDA:
        virtual_env = env.CondaEnvironment(args.req_scheme, **kwargs)

    return virtual_env


def _command_action_create(_prog, args):
    _check_create_args(args)
    _get_virtual_env(args).create()
    return const.STATUS_SUCCESS


def _command_action_remove(_prog, args):
    # set equivalence
    if {args.env_type, args.env_name, args.req_scheme} == {const.ENV_TYPE_CONDA, None}:
        raise RuntimeError(
            "Please supply either the '-e/--env-name' or '-r/--requirements' "
            "option so we know the name of the environment to remove."
        )
    _get_virtual_env(args).remove()
    return const.STATUS_SUCCESS


def _command_action_replace(_prog, args):
    _check_create_args(args)
    _get_virtual_env(args).replace()
    return const.STATUS_SUCCESS


def _command_action_completion(prog, args):
    if args.bash:
        print(completion.get_commands(prog, absolute=args.absolute))
    else:
        completion_args = [COMMAND_COMPLETION, "--bash"]
        print(completion.get_instructions(prog, completion_args))

    return const.STATUS_SUCCESS


def _populate_command_actions(commands, prog):
    func = "func"
    description = "description"
    add_arguments_funcs = "add_arguments_funcs"

    commands[COMMAND_CREATE][func] = _command_action_create
    commands[COMMAND_REMOVE][func] = _command_action_remove
    commands[COMMAND_REPLACE][func] = _command_action_replace
    commands[COMMAND_COMPLETION][func] = _command_action_completion

    commands[COMMAND_CREATE][description] = DESCRIPTION_CREATE.format(prog=prog)
    commands[COMMAND_REMOVE][description] = DESCRIPTION_REMOVE.format(prog=prog)
    commands[COMMAND_REPLACE][description] = DESCRIPTION_REPLACE.format(prog=prog)
    commands[COMMAND_COMPLETION][description] = DESCRIPTION_COMPLETION.format(prog=prog)

    for command in VENV_COMMANDS:
        commands[command][add_arguments_funcs] = [
            _add_venv_arguments,
            _add_force_arguments,
        ]
    for command in VENV_CREATE_COMMANDS:
        commands[command][add_arguments_funcs].append(
            _add_python_version_arguments,
        )
    commands[COMMAND_COMPLETION][add_arguments_funcs] = [_add_completion_arguments]


def main(*argv):
    """Do the thing."""
    (prog, argv) = argparsing.grok_argv(argv)
    argparser = argparsing.setup_argparse(
        prog=prog,
        description=DESCRIPTION_MAIN,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    _add_version_arguments(prog, argparser)
    _populate_command_actions(COMMANDS, prog)
    subcommands = _add_subcommands(argparser, COMMANDS)
    for (subcommand, subcommand_parser) in subcommands.items():
        kwargs = {"subcommand": subcommand}
        for key in ["req_scheme_required"]:
            if key in COMMANDS[subcommand]:
                kwargs[key] = COMMANDS[subcommand][key]
        for add_arguments_func in COMMANDS[subcommand]["add_arguments_funcs"]:
            add_arguments_func(subcommand_parser, **kwargs)

    try:
        argcomplete.autocomplete(argparser)
    except NameError:
        # Enable running without autocompletion
        pass

    args = argparser.parse_args(argv)
    if args.command is None:
        argparser.print_usage()
        sys.exit(const.STATUS_HELP)  # Same behavior as argparse usage messages

    try:
        try:
            if args.func is not None:
                return args.func(prog, args)

        except exceptions.MissingRequirementsError as e:
            message = "{msg}: {args}".format(msg=e.args[0], args=", ".join(e.args[1]))
            raise RuntimeError(message)

        except exceptions.EnvExistsError as e:
            message = (
                e.args[0]
                + f"; please remove it first, or use '{COMMAND_REPLACE}' instead"
            )
            raise RuntimeError(message)

        except exceptions.EnvOccludedError as e:
            message = e.args[0] + "; you must deal with it by hand"
            raise RuntimeError(message)

    except RuntimeError as e:
        print(f"{prog}: error: {e}", file=sys.stderr)
        return const.STATUS_FAILURE

    raise RuntimeError(f"Unhandled subcommand: {args.command}")


if __name__ == "__main__":
    sys.exit(main(*sys.argv))
