"""Provide a command-line interface for `~python_venv`:py:mod:."""

import argparse
import os
import os.path
import shutil
import stat
import sys

try:
    import argcomplete
except ModuleNotFoundError:
    # Enable running without autocompletion
    pass

from . import argparsing, completion, exceptions, get_version, runcommand

STATUS_SUCCESS = 0
STATUS_FAILURE = 1

PYTHON = "python3"
CONDA = "conda"

PROGRESS_PREFIX = "==> "

VENV_DIR = ".venv"
DEV_SUFFIX = "-dev"

REQUIREMENTS_VENV = ["pip", "setuptools", "wheel"]

REQUIREMENTS_PLAIN = "requirements.txt"
REQUIREMENTS_DEV = os.path.join("dev", "requirements_dev.txt")
REQUIREMENTS_TEST = os.path.join("dev", "requirements_test.txt")
REQUIREMENTS_FROZEN = "requirements_frozen.txt"
REQUIREMENTS_BUILD = os.path.join("dev", "requirements_build.txt")
REQUIREMENTS_PACKAGE = "{basename}"
REQUIREMENTS_SOURCE = ["{python}", "setup.py", "install"]

COMMAND_CREATE = "create"
COMMAND_REMOVE = "remove"
COMMAND_COMPLETION = "completion"

COMMANDS = {
    COMMAND_CREATE: {
        "help": "Create a Python virtual environment",
        "aliases": ["new"],
        "reqs_required": True,
    },
    COMMAND_REMOVE: {
        "help": "Remove a Python virtual environment",
        "aliases": ["rm"],
        "reqs_required": False,
    },
    COMMAND_COMPLETION: {
        "help": "Set up shell command-line autocompletion",
    },
}

REQS_PLAIN = "plain"
REQS_DEV = "dev"
REQS_FROZEN = "frozen"
REQS_PACKAGE = "package"
REQS_SOURCE = "source"

REQS = [
    REQS_PLAIN,
    REQS_DEV,
    REQS_FROZEN,
    REQS_PACKAGE,
    REQS_SOURCE,
]

ENV_TYPE_VENV = "venv"
ENV_TYPE_CONDA = "conda"

ENV_TYPES = [
    ENV_TYPE_VENV,
    ENV_TYPE_CONDA,
]

ENV_DESCRIPTIONS = {
    ENV_TYPE_VENV: "Python venv at {env_name}",
    ENV_TYPE_CONDA: "conda environment {env_name}",
}

FROM_FILES = "files"
FROM_PACKAGES = "packages"
FROM_COMMANDS = "commands"

REQUIREMENTS = {
    REQS_PLAIN: {
        FROM_FILES: [REQUIREMENTS_PLAIN],
    },
    REQS_DEV: {
        FROM_FILES: [
            REQUIREMENTS_PLAIN,
            REQUIREMENTS_BUILD,
            REQUIREMENTS_DEV,
            REQUIREMENTS_TEST,
        ],
    },
    REQS_FROZEN: {
        FROM_FILES: [REQUIREMENTS_FROZEN],
    },
    REQS_PACKAGE: {
        FROM_PACKAGES: [REQUIREMENTS_PACKAGE],
    },
    REQS_SOURCE: {
        FROM_COMMANDS: [REQUIREMENTS_SOURCE],
    },
}

DEFAULT_ENV_TYPE = ENV_TYPE_VENV

DESCRIPTION_MAIN = f"""
Create or remove a Python virtual environment for the Python project in the
current directory.  We expect a 'setup.py' to exist, along with requirements in
'{REQUIREMENTS_PLAIN}', '{REQUIREMENTS_FROZEN}', '{REQUIREMENTS_DEV}',
and '{REQUIREMENTS_TEST}'.

Venv virtual environments are created in '{VENV_DIR}'.

Conda virtual environments are created using the name of the Python project
(via '{PYTHON} setup.py --name'), with underscores ('_') replaced by hyphens ('-')
and with '{DEV_SUFFIX}' appended for development environments.
"""

DESCRIPTION_CREATE = """
Create a Python virtual environment for the Python project in the current
directory.
"""

DESCRIPTION_REMOVE = """
Remove a Python virtual environment for the Python project in the current
directory.
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


def _add_venv_arguments(argparser, reqs_required=False):
    argparsing.add_dry_run_argument(argparser)

    argparser.add_argument(
        "-b",
        "--basename",
        action="store",
        default=None,
        help=(
            f"Base name to use when inferring environment name or package name "
            f"(default: the result of '{PYTHON} setup.py --name', with underscores "
            f"replaced by hyphens)"
        ),
    )

    reqs_group = argparser.add_argument_group(title="requirements options")
    reqs_mutex_group = reqs_group.add_mutually_exclusive_group(required=reqs_required)
    reqs_mutex_group.add_argument(
        "-r",
        "--requirements",
        action="store",
        dest="reqs",
        choices=REQS,
        default=None,
        help=(
            "Requirements to use for virtual environment "
            "(equivalent to the other requirements options below)"
        ),
    )
    reqs_mutex_group.add_argument(
        "-p",
        f"--{REQS_PLAIN}",
        action="store_const",
        dest="reqs",
        const=REQS_PLAIN,
        help=f"Virtual environment uses '{REQUIREMENTS_PLAIN}'",
    )
    reqs_mutex_group.add_argument(
        "-d",
        f"--{REQS_DEV}",
        action="store_const",
        dest="reqs",
        const=REQS_DEV,
        help=(
            f"Virtual environment is for development; uses "
            f"'{REQUIREMENTS_PLAIN}', '{REQUIREMENTS_DEV}', and "
            f"'{REQUIREMENTS_TEST}'"
        ),
    )
    reqs_mutex_group.add_argument(
        "-z",
        f"--{REQS_FROZEN}",
        action="store_const",
        dest="reqs",
        const=REQS_FROZEN,
        help=f"Virtual environment uses '{REQUIREMENTS_FROZEN}'",
    )
    reqs_mutex_group.add_argument(
        "-P",
        f"--{REQS_PACKAGE}",
        action="store_const",
        dest="reqs",
        const=REQS_PACKAGE,
        help="Virtual environment uses 'pip install BASENAME'",
    )
    reqs_mutex_group.add_argument(
        "-s",
        f"--{REQS_SOURCE}",
        action="store_const",
        dest="reqs",
        const=REQS_SOURCE,
        help=("Virtual environment uses '{command}'").format(
            command=" ".join(REQUIREMENTS_SOURCE).format(python=PYTHON)
        ),
    )

    venv_group = argparser.add_argument_group(title="environment options")
    venv_mutex_group = venv_group.add_mutually_exclusive_group()
    venv_mutex_group.add_argument(
        "-t",
        "--type",
        action="store",
        dest="env_type",
        choices=ENV_TYPES,
        default=DEFAULT_ENV_TYPE,
        help=f"The type of environment to create (default: {DEFAULT_ENV_TYPE})",
    )
    venv_mutex_group.add_argument(
        "-v",
        f"--{ENV_TYPE_VENV}",
        action="store_const",
        dest="env_type",
        const=ENV_TYPE_VENV,
        help=f"Same as '--type {ENV_TYPE_VENV}'",
    )
    venv_mutex_group.add_argument(
        "-c",
        f"--{ENV_TYPE_CONDA}",
        action="store_const",
        dest="env_type",
        const=ENV_TYPE_CONDA,
        help=f"Same as '--type {ENV_TYPE_CONDA}'",
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
        help="Remove any pre-existing virtual environment",
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


def _add_version_arguments(prog, argparser):
    argparser.add_argument(
        "-V",
        "--version",
        action="version",
        version="{prog} {version}".format(prog=prog, version=get_version()),
    )
    return argparser


def _progress(args, message, suffix="..."):
    message_parts = [message]
    if suffix and not message.endswith("."):
        message_parts.append(suffix)
    runcommand.print_trace(
        message_parts, trace_prefix=PROGRESS_PREFIX, dry_run=args.dry_run
    )


def _get_package_name(_args):
    package_name = runcommand.run_command(
        [PYTHON, "setup.py", "--name"],
        dry_run=False,
        return_output=True,
        show_trace=False,
    )
    if package_name.endswith("\n"):
        package_name = package_name[:-1]
    return package_name


def _get_basename(args):
    if args.basename is None:
        args.basename = _get_package_name(args).replace("_", "-")
    return args.basename


def _get_env_name(args):
    if args.env_name is None:
        if args.env_type == ENV_TYPE_CONDA:
            args.env_name = _get_basename(args)
            if args.reqs == REQS_DEV:
                args.env_name += DEV_SUFFIX
        else:
            args.env_name = VENV_DIR
    return args.env_name


def _get_commands(requirements, **kwargs):
    commands = []
    for command in requirements.get(FROM_COMMANDS, []):
        commands.append([x.format(**kwargs) for x in command])
    return commands


def _pip_requirements(requirements, basename):
    pip_arguments = []
    for a_file in requirements.get(FROM_FILES, []):
        pip_arguments.append("-r")
        pip_arguments.append(a_file)
    for package_spec in requirements.get(FROM_PACKAGES, []):
        pip_arguments.append(package_spec.format(basename=basename))
    return pip_arguments


def _create_venv(args, env_description, requirements):
    _progress(args, f"Creating {env_description}")

    env_dir = _get_env_name(args)
    full_env_dir = os.path.abspath(env_dir)

    if os.path.isdir(env_dir):
        preexisting_message = f"Found preexisting {env_dir}"
        if args.force:
            _progress(args, preexisting_message)
            _remove_venv(args, env_description)
        else:
            raise RuntimeError(
                preexisting_message + ", please remove it first, or use '--force'"
            )
    elif os.path.exists(env_dir):
        raise RuntimeError(
            f"{full_env_dir} exists, but is not a directory; "
            "you must deal with it by hand."
        )

    runcommand.run_command(
        [PYTHON, "-m", "venv", env_dir], show_trace=True, dry_run=args.dry_run
    )
    verb = "Would have created" if args.dry_run else "Created"
    _progress(args, f"{verb} {full_env_dir}", suffix=None)

    env_bin_dir = os.path.join(env_dir, "bin")
    env_python = os.path.join(env_bin_dir, PYTHON)
    env_activate = os.path.join(env_bin_dir, "activate")

    _progress(args, f"Installing {args.reqs} requirements")

    pip_install_command = [env_python, "-m", "pip", "install"]
    runcommand.run_command(
        pip_install_command + ["--upgrade"] + REQUIREMENTS_VENV,
        show_trace=True,
        dry_run=args.dry_run,
    )
    if {FROM_COMMANDS} & set(requirements):  # set intersection
        for command in _get_commands(requirements, python=env_python):
            runcommand.run_command(command, show_trace=True, dry_run=args.dry_run)
    if {FROM_FILES, FROM_PACKAGES} & set(requirements):  # set intersection
        runcommand.run_command(
            pip_install_command + _pip_requirements(requirements, _get_basename(args)),
            show_trace=True,
            dry_run=args.dry_run,
        )

    _progress(args, "Done.")
    if not args.dry_run:
        _progress(args, f"To use your virtual environment: 'source {env_activate}'.")


def _remove_venv(args, env_description):
    _progress(args, f"Removing {env_description}")

    env_dir = _get_env_name(args)
    full_env_dir = os.path.abspath(env_dir)

    if not os.path.exists(env_dir):
        _progress(args, f"Good news!  There is no {env_description}.")
        return

    if not os.path.isdir(env_dir):
        raise RuntimeError(
            f"{full_env_dir} exists, but is not a directory; "
            "you must remove it by hand."
        )

    def _retry_readonly(func, path, _excinfo):
        """Make file writable and attempt to remove again."""
        os.chmod(path, stat.S_IWRITE)
        func(path)

    verb = "Would remove" if args.dry_run else "Removing"
    _progress(args, f"{verb} {full_env_dir} and all its contents")

    if not args.dry_run:
        shutil.rmtree(env_dir, onerror=_retry_readonly)

    _progress(args, "Done.")


def _get_conda_env_dir(args):
    if args.dry_run:
        return "CONDA_ENV_DIR"

    env_name = _get_env_name(args)

    env_listing = runcommand.run_command(
        [CONDA, "env", "list"],
        return_output=True,
        show_trace=False,
        dry_run=args.dry_run,
    ).splitlines()

    for line in [x.strip() for x in env_listing]:
        if line.startswith("# ") or not line:
            continue
        parts = line.split(maxsplit=1)
        if parts[0] == env_name:
            env_dir = parts[1]
            if env_dir.startswith("* "):
                env_dir = env_dir.split(maxsplit=1)[1]
            return env_dir

    raise exceptions.EnvNotFoundError(f"unable to find conda environment {env_name}")


def _create_conda_env(args, env_description, requirements):
    _progress(args, f"Creating {env_description}")

    env_name = _get_env_name(args)
    try:
        env_dir = _get_conda_env_dir(args)
    except exceptions.EnvNotFoundError:
        env_dir = None

    if env_dir is not None:
        preexisting_message = f"Found preexisting {env_name}"
        if args.force:
            _progress(args, preexisting_message)
            _remove_conda_env(args, env_description)
        else:
            raise RuntimeError(
                preexisting_message + ", please remove it first, or use '--force'"
            )

    conda_command = [CONDA, "create"]
    if args.force:
        conda_command.append("--yes")
    runcommand.run_command(
        conda_command + ["-n", env_name, "python=3"],
        show_trace=True,
        dry_run=args.dry_run,
    )

    env_dir = _get_conda_env_dir(args)
    env_bin_dir = os.path.join(env_dir, "bin")
    env_python = os.path.join(env_bin_dir, PYTHON)

    _progress(args, f"Installing {args.reqs} requirements")

    pip_install_command = [env_python, "-m", "pip", "install"]
    if {FROM_COMMANDS} & set(requirements):  # set intersection
        for command in _get_commands(requirements, python=env_python):
            runcommand.run_command(command, show_trace=True, dry_run=args.dry_run)
    if {FROM_FILES, FROM_PACKAGES} & set(requirements):  # set intersection
        runcommand.run_command(
            pip_install_command + _pip_requirements(requirements, _get_basename(args)),
            show_trace=True,
            dry_run=args.dry_run,
        )

    _progress(args, "Done.")
    if not args.dry_run:
        _progress(
            args, f"To use your virtual environment: 'source activate {env_name}'."
        )


def _remove_conda_env(args, env_description):
    _progress(args, f"Removing {env_description}")
    env_name = _get_env_name(args)
    conda_command = [CONDA, "env", "remove"]
    if args.force:
        conda_command.append("--yes")
    runcommand.run_command(
        conda_command + ["-n", env_name], show_trace=True, dry_run=args.dry_run
    )
    _progress(args, "Done.")


def _check_requirements(requirements):
    missing = []
    for requirements_file in requirements.get(FROM_FILES, []):
        if not os.path.exists(requirements_file):
            missing.append(requirements_file)
    if missing:
        noun = "file" if len(missing) == 1 else "files"
        text = ", ".join(missing)
        raise RuntimeError(f"Missing requirements {noun}: {text}")


def _command_action_create(_prog, args, **_kwargs):
    requirements = REQUIREMENTS[args.reqs]
    _check_requirements(requirements)
    env_name = _get_env_name(args)
    env_description = ENV_DESCRIPTIONS[args.env_type].format(env_name=env_name)
    if args.env_type == ENV_TYPE_VENV:
        _create_venv(args, env_description, requirements)
    elif args.env_type == ENV_TYPE_CONDA:
        _create_conda_env(args, env_description, requirements)

    return STATUS_SUCCESS


def _command_action_remove(_prog, args, **_kwargs):
    # set equivalence
    if {args.env_type, args.env_name, args.reqs} == {ENV_TYPE_CONDA, None}:
        raise RuntimeError(
            "Please supply either the '-e/--env-name' or '-r/--requirements' "
            "option so we know the name of the environment to remove."
        )
    env_name = _get_env_name(args)
    env_description = ENV_DESCRIPTIONS[args.env_type].format(env_name=env_name)
    if args.env_type == ENV_TYPE_VENV:
        _remove_venv(args, env_description)
    elif args.env_type == ENV_TYPE_CONDA:
        _remove_conda_env(args, env_description)

    return STATUS_SUCCESS


def _command_action_completion(prog, args, **_kwargs):
    if args.bash:
        print(completion.get_commands(prog, absolute=args.absolute))
    else:
        completion_args = [COMMAND_COMPLETION, "--bash"]
        print(completion.get_instructions(prog, completion_args))

    return STATUS_SUCCESS


def _populate_command_actions(commands, prog):
    func = "func"
    description = "description"
    add_arguments_funcs = "add_arguments_funcs"

    commands[COMMAND_CREATE][func] = _command_action_create
    commands[COMMAND_REMOVE][func] = _command_action_remove
    commands[COMMAND_COMPLETION][func] = _command_action_completion

    commands[COMMAND_CREATE][description] = DESCRIPTION_CREATE.format(prog=prog)
    commands[COMMAND_REMOVE][description] = DESCRIPTION_REMOVE.format(prog=prog)
    commands[COMMAND_COMPLETION][description] = DESCRIPTION_COMPLETION.format(prog=prog)

    commands[COMMAND_CREATE][add_arguments_funcs] = [
        _add_venv_arguments,
        _add_force_arguments,
    ]
    commands[COMMAND_REMOVE][add_arguments_funcs] = [_add_venv_arguments]
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
        kwargs = {}
        for key in ["reqs_required"]:
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

    try:
        if args.func is not None:
            return args.func(prog, args)
    except RuntimeError as e:
        print(f"{prog}: error: {e}", file=sys.stderr)
        return STATUS_FAILURE

    raise RuntimeError(f"Unhandled subcommand: {args.command}")


if __name__ == "__main__":
    sys.exit(main(*sys.argv))
