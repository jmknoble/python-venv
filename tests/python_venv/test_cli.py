"""Provide unit tests for `~python_venv.cli`:py:mod:."""

import argparse
import itertools
import os
import os.path
import unittest
from unittest.mock import patch

import parameterized  # https://pypi.org/project/parameterized/

from python_venv import cli, const, env, osenv
from tests.python_venv import contextmgr as ctx

########################################

_ENV_CLASSES = {
    "venv": env.VenvEnvironment,
    "named-venv": env.NamedVenvEnvironment,
    "pyenv": env.PyenvEnvironment,
    "conda": env.CondaEnvironment,
}

########################################


def _generate_combinations(
    commands=None, env_types=None, requirements=None, action=None
):
    opt_types = ("short", "long", "abbrev_short", "abbrev_long")
    all_commands = ("create", "new", "remove", "rm", "replace", "rpl")
    all_env_types = ("venv", "pyenv", "conda")
    all_requirements = (
        "plain",
        "dev",
        "devplus",
        "frozen",
        "package",
        "pip",
        "source",
        "wheel",
    )
    basenames = (None, "dummy-basename")
    venvs_dirs = (None, "dummy-venvs-dir")
    cwds = (None, ".")
    env_names = (None, "dummy-env")
    forces = (False, True)
    python_versions = (None, "1.2.3")
    dry_runs = (False, True)
    pip_argses = ([], ["dummy-pypi-package"], ["--", "-r", "dummy-requirements.txt"])
    pip_args_names = ("argsnone", "argspkg", "argsdashes")
    actions = {
        "create": "create",
        "new": "create",
        "remove": "remove",
        "rm": "remove",
        "replace": "replace",
        "rpl": "replace",
    }
    opts = {
        "short": {
            "env_type": "-t",
            "requirements": "-r",
            "basename": "-b",
            "venvs_dir": "-V",
            "cd": "-C",
            "env_name": "-e",
            "dry_run": "-n",
            "force": "-f",
            "python_version": "--python-version",
        },
        "long": {
            "env_type": "--type",
            "requirements": "--requirements",
            "basename": "--basename",
            "venvs_dir": "--venvs-dir",
            "cd": "--cd",
            "env_name": "--env-name",
            "dry_run": "--dry-run",
            "force": "--force",
            "python_version": "--python-version",
        },
    }
    abbrevs = {
        "abbrev_short": {
            "venv": "-v",
            "named-venv": "-N",
            "pyenv": "-y",
            "conda": "-c",
            "plain": "-p",
            "dev": "-d",
            "devplus": "-D",
            "frozen": "-z",
            "package": "--package",
            "pip": "-P",
            "source": "-s",
            "wheel": "-w",
        },
        "abbrev_long": {
            "venv": "--venv",
            "named-venv": "--named-venv",
            "pyenv": "--pyenv",
            "conda": "--conda",
            "plain": "--plain",
            "dev": "--dev",
            "devplus": "--devplus",
            "frozen": "--frozen",
            "package": "--package",
            "pip": "--pip",
            "source": "--source",
            "wheel": "--wheel",
        },
    }
    commands = all_commands if commands is None else commands
    env_types = all_env_types if env_types is None else env_types
    requirements = all_requirements if requirements is None else requirements

    for name, things, all_things in [
        ("commands", commands, all_commands),
        ("env_types", env_types, all_env_types),
        ("requirements", requirements, all_requirements),
    ]:
        if not (set(things) & set(all_things)):  # set intersection, should be non-empty
            raise ValueError(f"one or more {name} is invalid: {things}")

    variations = itertools.product(
        commands,
        env_types,
        requirements,
        basenames,
        venvs_dirs,
        cwds,
        env_names,
        forces,
        python_versions,
        dry_runs,
        zip(pip_args_names, pip_argses),
        opt_types,
    )

    for (
        command,
        env_type,
        req,
        basename,
        venvs_dir,
        cwd,
        env_name,
        force,
        python_version,
        dry_run,
        pip_args,
        opt_type,
    ) in variations:
        name_parts = [command, env_type.replace("-", "_"), req]

        fallback_opt_type = opt_type.replace("abbrev_", "")
        these_opts = opts.get(opt_type, opts.get(fallback_opt_type)).copy()
        these_abbrevs = abbrevs.get(opt_type)

        args = []

        if not action:
            action = actions[command]

        if opt_type in opts:
            args.extend([these_opts["env_type"], env_type])
            args.extend([these_opts["requirements"], req])
        elif opt_type in abbrevs:
            args.extend([these_abbrevs[env_type], these_abbrevs[req]])
        else:
            raise KeyError(f"invalid opt_type: {opt_type}")

        if basename:
            name_parts.append("basename")
            args.extend([these_opts["basename"], basename])

        if venvs_dir and env_type in {const.ENV_TYPE_NAMED_VENV}:
            name_parts.append("venvsdir")
            args.extend([these_opts["venvs_dir"], venvs_dir])

        if cwd:
            name_parts.append("cd")
            args.extend([these_opts["cd"], cwd])

        if env_name:
            name_parts.append("env_name")
            args.extend([these_opts["env_name"], env_name])

        if force:
            name_parts.append("force")
            args.append(these_opts["force"])

        if (
            python_version
            and env_type in const.ENV_TYPES_VERSIONED
            and action in {"create", "replace"}
        ):
            name_parts.append("pyver")
            args.extend([these_opts["python_version"], python_version])
        else:
            python_version = None

        if dry_run:
            name_parts.append("dry_run")
            args.append(these_opts["dry_run"])

        (pip_args_name, pip_args) = pip_args
        if req in {"pip"}:
            name_parts.append(pip_args_name)
            args.extend(pip_args)
            if pip_args and pip_args[0] == "--":
                pip_args = pip_args[1:]
        elif pip_args:
            continue  # anything but empty pip_args doesn't make sense without --pip

        add_kwargs = {
            "pip_args": pip_args,
            "basename": basename,
            "env_name": env_name,
            "dry_run": dry_run,
            "force": force,
        }
        if python_version:
            add_kwargs["python_version"] = python_version
        if env_type in {const.ENV_TYPE_NAMED_VENV}:
            add_kwargs["env_prefix"] = os.path.expanduser(
                venvs_dir
                if venvs_dir
                else os.environ.get(const.ENV_VAR_VENVS_DIR, const.DEFAULT_VENVS_DIR)
            )

        name_parts.append(opt_type)
        name = "_".join(name_parts)

        yield (
            name,
            command,
            action,
            args,
            req,
            env_type,
            add_kwargs,
        )


########################################
# Tests


class TestCli_000_Base(unittest.TestCase):
    def setUp(self):
        self.kwargs = {
            "python": "python3",
            "os_environ": osenv.get_clean_environ(),
        }

    def tearDown(self):
        pass

    @parameterized.parameterized.expand(
        [
            ("help_short", "-h"),
            ("help_long", "--help"),
            ("version_short", "-V"),
            ("version_long", "--version"),
        ]
    )
    def test_PV_CLI_000_info(self, name, option):
        with self.assertRaises(SystemExit) as raised:
            with ctx.capture(cli.main, "python-venv", option):
                pass
        status = raised.exception.args[0]
        expected_status = 0
        self.assertEqual(status, expected_status)

    @parameterized.parameterized.expand(
        [
            ("main", []),
            ("create", ["create"]),
            ("new", ["new"]),
            ("remove", ["remove"]),
            ("rm", ["rm"]),
            ("replace", ["replace"]),
            ("rpl", ["rpl"]),
            ("invalid", ["yuck"]),
        ]
    )
    def test_PV_CLI_001_usage(self, name, args):
        with self.assertRaises(SystemExit) as raised:
            with ctx.capture(cli.main, "python-venv", *args):
                pass
        status = raised.exception.args[0]
        expected_status = 2
        self.assertEqual(status, expected_status)

    @parameterized.parameterized.expand(
        [
            ("create_short", "create", "-h"),
            ("create_long", "create", "--help"),
            ("new_short", "new", "-h"),
            ("new_long", "new", "--help"),
            ("remove_short", "remove", "-h"),
            ("remove_long", "remove", "--help"),
            ("rm_short", "rm", "-h"),
            ("rm_long", "rm", "--help"),
            ("replace_short", "replace", "-h"),
            ("replace_long", "replace", "--help"),
            ("rpl_short", "rpl", "-h"),
            ("rpl_long", "rpl", "--help"),
            ("completion_short", "completion", "-h"),
            ("completion_long", "completion", "--help"),
        ]
    )
    def test_PV_CLI_010_subcommand_help(self, name, subcommand, option):
        with self.assertRaises(SystemExit) as raised:
            with ctx.capture(cli.main, "python-venv", subcommand, option):
                pass
        status = raised.exception.args[0]
        expected_status = 0
        self.assertEqual(status, expected_status)

    @parameterized.parameterized.expand(
        [
            ("info", []),
            ("bash", ["--bash"]),
            ("bash_absolute", ["--bash", "--absolute"]),
        ]
    )
    def test_PV_CLI_020_completion(self, name, options):
        args = [cli.main, "python-venv", "completion"]
        args.extend(options)
        with ctx.capture(*args) as (status, _stdout, _stderr):
            self.assertEqual(status, 0)

    @parameterized.parameterized.expand(
        [
            ("venv_invalid_raises", "venv", "invalid_python_version", True),
            ("venv_valid_raises", "venv", "1.2.3", True),
            ("named_venv_invalid_raises", "named-venv", "invalid_python_version", True),
            ("named_venv_valid_raises", "named-venv", "1.2.3", True),
            ("pyenv_does_not_raise", "pyenv", "dummy-python-version", False),
            ("conda_invalid_raises", "conda", "invalid_python_version", True),
            ("conda_major_only", "conda", "1", False),
            ("conda_major_minor", "conda", "1.2", False),
            ("conda_major_minor_micro", "conda", "1.2.3", False),
            ("conda_major_minor_micro_extra", "conda", "1.2.3.4", False),
            ("conda_major_minor_micro_rc", "conda", "1.2.3rc4", False),
            ("conda_major_minor_micro_dot_rc", "conda", "1.2.3.rc4", False),
        ]
    )
    def test_PV_CLI_030_check_python_version(
        self, name, env_type, python_version, should_raise
    ):
        args = argparse.Namespace(env_type=env_type, python_version=python_version)
        if should_raise:
            with self.assertRaises(RuntimeError):
                cli._check_create_args(args)
        else:
            cli._check_create_args(args)

    @parameterized.parameterized.expand(
        [
            ("named_venv_does_not_raise", "named-venv", "dummy-venvs-dir", False),
            ("venv_raises", "venv", "dummy-venvs-dir", True),
            ("pyenv_raises", "pyenv", "dummy-venvs-dir", True),
            ("conda_raises", "conda", "dummy-venvs-dir", True),
        ]
    )
    def test_PV_CLI_040_check_venvs_dir(self, name, env_type, venvs_dir, should_raise):
        args = argparse.Namespace(env_type=env_type, venvs_dir=venvs_dir)
        if should_raise:
            with self.assertRaises(RuntimeError):
                cli._check_venv_dir_args(args)
        else:
            cli._check_venv_dir_args(args)

    ####################


class TestCli_100_Venv_Create(unittest.TestCase):
    def setUp(self):
        self.kwargs = {
            "python": "python3",
            "os_environ": osenv.get_clean_environ(),
        }

    def tearDown(self):
        pass

    @parameterized.parameterized.expand(
        _generate_combinations(
            commands=["create", "new"], env_types=["venv", "named-venv"]
        )
    )
    def test_PV_CLI_100_venv(
        self, name, command, action, options, req_scheme, env_type, add_kwargs
    ):
        this_class = _ENV_CLASSES[env_type]
        with patch.object(this_class, "__init__", return_value=None) as init:
            with patch.object(env.VenvEnvironment, action) as action_method:
                with ctx.capture_output():
                    cli.main("python-venv", command, *options)
        kwargs = self.kwargs.copy()
        kwargs.update(add_kwargs)
        init.assert_called_once_with(req_scheme, **kwargs)
        action_method.assert_called_once_with()


class TestCli_110_Venv_Remove(unittest.TestCase):
    def setUp(self):
        self.kwargs = {
            "python": "python3",
            "os_environ": osenv.get_clean_environ(),
        }

    def tearDown(self):
        pass

    @parameterized.parameterized.expand(
        _generate_combinations(
            commands=["remove", "rm"], env_types=["venv", "named-venv"]
        )
    )
    def test_PV_CLI_110_venv(
        self, name, command, action, options, req_scheme, env_type, add_kwargs
    ):
        this_class = _ENV_CLASSES[env_type]
        with patch.object(this_class, "__init__", return_value=None) as init:
            with patch.object(env.VenvEnvironment, action) as action_method:
                with ctx.capture_output():
                    cli.main("python-venv", command, *options)
        kwargs = self.kwargs.copy()
        kwargs.update(add_kwargs)
        init.assert_called_once_with(req_scheme, **kwargs)
        action_method.assert_called_once_with()


class TestCli_120_Venv_Replace(unittest.TestCase):
    def setUp(self):
        self.kwargs = {
            "python": "python3",
            "os_environ": osenv.get_clean_environ(),
        }

    def tearDown(self):
        pass

    @parameterized.parameterized.expand(
        _generate_combinations(
            commands=["replace", "rpl"], env_types=["venv", "named-venv"]
        )
    )
    def test_PV_CLI_120_venv(
        self, name, command, action, options, req_scheme, env_type, add_kwargs
    ):
        this_class = _ENV_CLASSES[env_type]
        with patch.object(this_class, "__init__", return_value=None) as init:
            with patch.object(env.VenvEnvironment, action) as action_method:
                with ctx.capture_output():
                    cli.main("python-venv", command, *options)
        kwargs = self.kwargs.copy()
        kwargs.update(add_kwargs)
        init.assert_called_once_with(req_scheme, **kwargs)
        action_method.assert_called_once_with()


class TestCli_130_Venv_Remove_Extra(unittest.TestCase):
    def setUp(self):
        self.kwargs = {
            "python": "python3",
            "os_environ": osenv.get_clean_environ(),
        }

    def tearDown(self):
        pass

    def test_PV_CLI_130_venv_remove_minimal(self):
        with ctx.capture(
            cli.main, "python-venv", "remove", "-t", "venv", "--dry-run"
        ) as (status, _stdout, _stderr):
            self.assertEqual(status, 0)

    def test_PV_CLI_140_named_venv_remove_minimal(self):
        with ctx.capture_to_file(
            cli.main, "python-venv", "remove", "-t", "named-venv", "--dry-run"
        ) as (status, _stdout, stderr):
            self.assertEqual(status, 1)
            self.assertIn(
                (
                    "error: Please supply either the '-e/--env-name' "
                    "or '-r/--requirements' option"
                ),
                stderr,
            )

    ####################


class TestCli_200_Pyenv_Create(unittest.TestCase):
    def setUp(self):
        self.kwargs = {
            "python": "python3",
            "os_environ": osenv.get_clean_environ(),
        }

    def tearDown(self):
        pass

    @parameterized.parameterized.expand(
        _generate_combinations(commands=["create", "new"], env_types=["pyenv"])
    )
    def test_PV_CLI_200_pyenv(
        self, name, command, action, options, req_scheme, env_type, add_kwargs
    ):
        this_class = _ENV_CLASSES[env_type]
        with patch.object(this_class, "__init__", return_value=None) as init:
            with patch.object(this_class, action) as action_method:
                with ctx.capture_output():
                    cli.main("python-venv", command, *options)
        kwargs = self.kwargs.copy()
        kwargs.update(add_kwargs)
        init.assert_called_once_with(req_scheme, **kwargs)
        action_method.assert_called_once_with()


class TestCli_210_Pyenv_Remove(unittest.TestCase):
    def setUp(self):
        self.kwargs = {
            "python": "python3",
            "os_environ": osenv.get_clean_environ(),
        }

    def tearDown(self):
        pass

    @parameterized.parameterized.expand(
        _generate_combinations(commands=["remove", "rm"], env_types=["pyenv"])
    )
    def test_PV_CLI_210_pyenv(
        self, name, command, action, options, req_scheme, env_type, add_kwargs
    ):
        this_class = _ENV_CLASSES[env_type]
        with patch.object(this_class, "__init__", return_value=None) as init:
            with patch.object(this_class, action) as action_method:
                with ctx.capture_output():
                    cli.main("python-venv", command, *options)
        kwargs = self.kwargs.copy()
        kwargs.update(add_kwargs)
        init.assert_called_once_with(req_scheme, **kwargs)
        action_method.assert_called_once_with()


class TestCli_220_Pyenv_Replace(unittest.TestCase):
    def setUp(self):
        self.kwargs = {
            "python": "python3",
            "os_environ": osenv.get_clean_environ(),
        }

    def tearDown(self):
        pass

    @parameterized.parameterized.expand(
        _generate_combinations(commands=["replace", "rpl"], env_types=["pyenv"])
    )
    def test_PV_CLI_220_pyenv(
        self, name, command, action, options, req_scheme, env_type, add_kwargs
    ):
        this_class = _ENV_CLASSES[env_type]
        with patch.object(this_class, "__init__", return_value=None) as init:
            with patch.object(this_class, action) as action_method:
                with ctx.capture_output():
                    cli.main("python-venv", command, *options)
        kwargs = self.kwargs.copy()
        kwargs.update(add_kwargs)
        init.assert_called_once_with(req_scheme, **kwargs)
        action_method.assert_called_once_with()


class TestCli_230_Pyenv_Remove_Extra(unittest.TestCase):
    def setUp(self):
        self.kwargs = {
            "python": "python3",
            "os_environ": osenv.get_clean_environ(),
        }

    def tearDown(self):
        pass

    def test_PV_CLI_230_pyenv_remove_minimal(self):
        with ctx.capture_to_file(
            cli.main, "python-venv", "remove", "-t", "pyenv", "--dry-run"
        ) as (status, _stdout, stderr):
            self.assertEqual(status, 1)
            self.assertIn(
                (
                    "error: Please supply either the '-e/--env-name' "
                    "or '-r/--requirements' option"
                ),
                stderr,
            )

    ####################


class TestCli_300_Conda_Create(unittest.TestCase):
    def setUp(self):
        self.kwargs = {
            "python": "python3",
            "os_environ": osenv.get_clean_environ(),
        }

    def tearDown(self):
        pass

    @parameterized.parameterized.expand(
        _generate_combinations(commands=["create", "new"], env_types=["conda"])
    )
    def test_PV_CLI_300_conda(
        self, name, command, action, options, req_scheme, env_type, add_kwargs
    ):
        this_class = _ENV_CLASSES[env_type]
        with patch.object(this_class, "__init__", return_value=None) as init:
            with patch.object(this_class, action) as action_method:
                with ctx.capture_output():
                    cli.main("python-venv", command, *options)
        kwargs = self.kwargs.copy()
        kwargs.update(add_kwargs)
        init.assert_called_once_with(req_scheme, **kwargs)
        action_method.assert_called_once_with()


class TestCli_310_Conda_Remove(unittest.TestCase):
    def setUp(self):
        self.kwargs = {
            "python": "python3",
            "os_environ": osenv.get_clean_environ(),
        }

    def tearDown(self):
        pass

    @parameterized.parameterized.expand(
        _generate_combinations(commands=["remove", "rm"], env_types=["conda"])
    )
    def test_PV_CLI_310_conda(
        self, name, command, action, options, req_scheme, env_type, add_kwargs
    ):
        this_class = _ENV_CLASSES[env_type]
        with patch.object(this_class, "__init__", return_value=None) as init:
            with patch.object(this_class, action) as action_method:
                with ctx.capture_output():
                    cli.main("python-venv", command, *options)
        kwargs = self.kwargs.copy()
        kwargs.update(add_kwargs)
        init.assert_called_once_with(req_scheme, **kwargs)
        action_method.assert_called_once_with()


class TestCli_320_Conda_Replace(unittest.TestCase):
    def setUp(self):
        self.kwargs = {
            "python": "python3",
            "os_environ": osenv.get_clean_environ(),
        }

    def tearDown(self):
        pass

    @parameterized.parameterized.expand(
        _generate_combinations(commands=["replace", "rpl"], env_types=["conda"])
    )
    def test_PV_CLI_320_conda(
        self, name, command, action, options, req_scheme, env_type, add_kwargs
    ):
        this_class = _ENV_CLASSES[env_type]
        with patch.object(this_class, "__init__", return_value=None) as init:
            with patch.object(this_class, action) as action_method:
                with ctx.capture_output():
                    cli.main("python-venv", command, *options)
        kwargs = self.kwargs.copy()
        kwargs.update(add_kwargs)
        init.assert_called_once_with(req_scheme, **kwargs)
        action_method.assert_called_once_with()


class TestCli_330_Conda_Remove_Extra(unittest.TestCase):
    def setUp(self):
        self.kwargs = {
            "python": "python3",
            "os_environ": osenv.get_clean_environ(),
        }

    def tearDown(self):
        pass

    def test_PV_CLI_330_conda_remove_minimal(self):
        with ctx.capture(
            cli.main, "python-venv", "remove", "-t", "conda", "--dry-run"
        ) as (status, _stdout, stderr):
            self.assertEqual(status, 1)
            self.assertIn(
                (
                    "error: Please supply either the '-e/--env-name' "
                    "or '-r/--requirements' option"
                ),
                stderr,
            )

    ####################


class TestCli_400_Extra(unittest.TestCase):
    def setUp(self):
        self.kwargs = {
            "python": "python3",
            "os_environ": osenv.get_clean_environ(),
        }

    def tearDown(self):
        pass

    @parameterized.parameterized.expand(
        [
            ("venv_plain", "venv", "plain", {}),
            ("venv_dev", "venv", "dev", {}),
            ("venv_devplus", "venv", "devplus", {}),
            ("venv_frozen", "venv", "frozen", {}),
            ("conda_plain", "conda", "plain", {}),
            ("conda_dev", "conda", "dev", {}),
            ("conda_devplus", "conda", "devplus", {}),
            ("conda_frozen", "conda", "frozen", {}),
        ]
    )
    def test_PV_CLI_400_create_missing_req(self, name, env_type, req_scheme, filespecs):
        req_files = {
            "plain": ["requirements.txt"],
            "dev": ["requirements_dev.txt"],
            "devplus": [
                "requirements.txt",
                os.path.join("dev", "requirements_build.txt"),
                os.path.join("dev", "requirements_dev.txt"),
                os.path.join("dev", "requirements_test.txt"),
            ],
            "frozen": ["requirements_frozen.txt"],
        }
        reqs = req_files[req_scheme]
        noun = "file" if len(reqs) == 1 else "files"
        reqs = ", ".join(reqs)
        with ctx.project("dummy_package", filespecs=filespecs):
            with ctx.capture_to_file(
                cli.main,
                "python-venv",
                "create",
                "--dry-run",
                "-t",
                env_type,
                "-r",
                req_scheme,
            ) as (status, _stdout, stderr):
                self.assertEqual(status, 1)
                self.assertIn(f"error: Missing requirements {noun}: {reqs}\n", stderr)
