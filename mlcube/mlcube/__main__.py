"""This requires the MLCube 2.0 that's located somewhere in one of dev branches."""
import logging
import os
import shutil
import sys
import typing as t

import click

import coloredlogs

from mlcube.parser import CliParser
from mlcube.cli import (MLCubeCommand, MultiValueOption, Options, parse_cli_args, UsageExamples)
from mlcube.errors import (ExecutionError, IllegalParameterValueError, MLCubeError)
from mlcube.shell import Shell
from mlcube.system_settings import SystemSettings

from omegaconf import OmegaConf

logger = logging.getLogger(__name__)

_TERMINAL_WIDTH = shutil.get_terminal_size()[0]   # Since Python version 3.3
"""Width of a user terminal. MLCube overrides default (80) character width to make usage examples look better."""


def add_to_parser(self, parser: click.parser.OptionParser, ctx: click.core.Context):
    def parser_process(value: str, state: click.parser.ParsingState):
        values: t.List[str] = [value]
        prefixes: t.Tuple[str] = tuple(self._eat_all_parser.prefixes)
        while state.rargs:
            if state.rargs[0].startswith(prefixes):
                break
            values.append(state.rargs.pop(0))
        self._previous_parser_process(tuple(values), state)

    super(MultiValueOption, self).add_to_parser(parser, ctx)
    for opt_name in self.opts:
        our_parser: t.Optional[click.parser.Option] = parser._long_opt.get(
            opt_name
        ) or parser._short_opt.get(opt_name)
        if our_parser:
            self._eat_all_parser = our_parser
            self._previous_parser_process = our_parser.process
            our_parser.process = parser_process
            break


log_level_option = click.option(
    "--log-level",
    "--log_level",
    required=False,
    type=str,
    default="warning",
    help="Log level to set, default is to do nothing.",
)
mlcube_option = click.option(
    "--mlcube",
    required=False,
    type=str,
    default=os.getcwd(),
    help="Path to MLCube. This can be either a directory path that becomes MLCube's root directory, or path to MLCube"
    "definition file (.yaml). In the latter case the MLCube's root directory becomes parent directory of the yaml"
    "file. Default is current directory.",
)
platform_option = click.option(
    "--platform",
    required=False,
    type=str,
    default="docker",
    help="Platform to run MLCube, default is 'docker' (that also supports podman).",
)
task_option = click.option(
    "--task",
    required=False,
    type=str,
    default=None,
    help="MLCube task name(s) to run, default is `main`. This parameter can take a list value, in which case task names"
    "are separated with ','.",
)
workspace_option = click.option(
    "--workspace",
    required=False,
    type=str,
    default=None,
    help="Workspace location that is used to store input/output artifacts of MLCube tasks.",
)
network_option = click.option(
    "--network",
    required=False,
    type=str,
    default=None,
    help="Networking options defined during MLCube container execution.",
)
security_option = click.option(
    "--security",
    required=False,
    type=str,
    default=None,
    help="Security options defined during MLCube container execution.",
)
gpus_option = click.option(
    "--gpus",
    required=False,
    type=str,
    default=None,
    help="GPU usage options defined during MLCube container execution.",
)
memory_option = click.option(
    "--memory",
    required=False,
    type=str,
    default=None,
    help="Memory RAM options defined during MLCube container execution.",
)
cpu_option = click.option(
    "--cpu",
    required=False,
    type=str,
    default=None,
    help="CPU options defined during MLCube container execution.",
)

@click.group(name='mlcube', add_help_option=False)
@Options.loglevel
@Options.help
def cli(log_level: t.Optional[str]):
    """MLCube 📦 is a tool for packaging, distributing and running Machine Learning (ML) projects and models.

    \b
    - GitHub: https://github.com/mlcommons/mlcube
    - Documentation: https://mlcommons.github.io/mlcube/
    - Example MLCubes: https://github.com/mlcommons/mlcube_examples
    """

    if log_level:
        log_level = log_level.upper()
        logging.basicConfig(level=log_level)
        coloredlogs.install(level=log_level)
        logging.info("Setting Log Level from CLI argument to '%s'.", log_level)
    _ = SystemSettings().update_installed_runners()


@cli.command(
    name='show_config', cls=MLCubeCommand, add_help_option=False, epilog=UsageExamples.show_config,
    context_settings={'ignore_unknown_options': True, 'allow_extra_args': True, 'max_content_width': _TERMINAL_WIDTH}
)
@Options.mlcube
@Options.platform
@Options.workspace
@Options.resolve
@Options.parameter
@Options.help
@click.pass_context
def show_config(ctx: click.core.Context, mlcube: t.Optional[str], platform: str, workspace: str,
                resolve: bool, p: t.Tuple[str]) -> None:
    """Show effective MLCube configuration.

    Effective MLCube configuration is the one used by one of MLCube runners to run this MLCube. This configuration is
    built by merging (1) default runner configuration retrieved from system settings, (2) MLCube project configuration
    and (3) configuration parameters passed by a user on a command line (CONFIG_PARAM).

    \f
    Args:
        ctx: Click context for unknown options
        mlcube: Path to MLCube root directory or mlcube.yaml file.
        platform: Platform to use to run this MLCube (docker, singularity, gcp, k8s etc).
        workspace: Workspace path to use. If not specified, default workspace inside MLCube directory is used.
        resolve: if True, compute values in MLCube configuration.
        p: Additional configuration parameters.
    """
    if mlcube is None:
        mlcube = os.getcwd()
    _, mlcube_config = parse_cli_args(
        unparsed_args=ctx.args + ['-P' + param for param in p],
        parsed_args={"mlcube": mlcube, "platform": platform, "workspace": workspace},
        resolve=resolve
    )
    print(OmegaConf.to_yaml(mlcube_config))


@cli.command(
    name='configure', cls=MLCubeCommand, add_help_option=False, epilog=UsageExamples.configure,
    context_settings={'ignore_unknown_options': True, 'allow_extra_args': True, 'max_content_width': _TERMINAL_WIDTH}
)
@Options.mlcube
@Options.platform
@Options.parameter
@Options.help
def configure(mlcube: t.Optional[str], platform: str, p: t.Tuple[str]) -> None:
    """Configure MLCube.

    Some MLCube projects need to be configured first. For instance, docker-based MLCubes distributed via GitHub with
    source code most likely will provide a `Dockerfile` to build a docker image. In this case, the process of building
    a docker image before MLCube runner can run it, is called a configuration phase. In general, users do not need to
    run this command manually - MLCube runners should be able to figure out when they need to run it, and will run it
    as part of `mlcube run` command.

    \f
    Args:
        mlcube: Path to MLCube root directory or mlcube.yaml file.
        platform: Platform to use to configure this MLCube for (docker, singularity, gcp, k8s etc).
        p: Additional MLCube configuration parameters (these parameters are those parameters that normally start with
            `-P` prefix). Here, due to original implementation, we need to `unparse` by adding `-P` prefix.
    """
    logger.debug("mlcube::configure, mlcube=%s, platform=%s, p=%s", mlcube, platform, str(p))
    if mlcube is None:
        mlcube = os.getcwd()
    logger.info("Configuring MLCube (`%s`) for `%s` platform.", os.path.abspath(mlcube), platform)
    try:
        runner_cls, mlcube_config = parse_cli_args(
            unparsed_args=['-P' + param for param in p],
            parsed_args={"mlcube": mlcube, "platform": platform},
            resolve=True
        )
        runner = runner_cls(mlcube_config, task=None)
        runner.configure()
    except MLCubeError as err:
        exit_code = err.context.get("code", 1) if isinstance(err, ExecutionError) else 1
        logger.exception(f"Failed to configure MLCube with error code {exit_code}.")
        if isinstance(err, ExecutionError):
            print(err.describe())
        sys.exit(exit_code)
    logger.info(
        "MLCube (%s) has been successfully configured for `%s` platform.",
        os.path.abspath(mlcube),
        platform,
    )


@cli.command(
    name='run', cls=MLCubeCommand, add_help_option=False, epilog=UsageExamples.run,
    context_settings={'ignore_unknown_options': True, 'allow_extra_args': True, 'max_content_width': _TERMINAL_WIDTH}
)
@mlcube_option
@platform_option
@task_option
@workspace_option
@network_option
@security_option
@gpus_option
@memory_option
@cpu_option
@Options.help
@click.pass_context
def run(
    ctx: click.core.Context,
    mlcube: str,
    platform: str,
    task: str,
    workspace: str,
    network: str,
    security: str,
    gpus: str,
    memory: str,
    cpu: str,
) -> None:
    """Run MLCube task(s).

    \f
    Args:
        ctx: Click context for unknown options
        mlcube: Path to MLCube root directory or mlcube.yaml file.
        platform: Platform to use to run this MLCube (docker, singularity, gcp, k8s etc).
        task: Comma separated list of tasks to run.
        workspace: Workspace path to use. If not specified, default workspace inside MLCube directory is used.
        network: Networking options defined during MLCube container execution.
        security: Security options defined during MLCube container execution.
        gpus: GPU usage options defined during MLCube container execution.
        memory: Memory RAM options defined during MLCube container execution.
        cpu: CPU options defined during MLCube container execution.
    """
    runner_cls, mlcube_config = parse_cli_args(
        unparsed_args=ctx.args,
        parsed_args={
            "mlcube": mlcube, "platform": platform, "workspace": workspace,
            "network": network, "security": security, "gpus": gpus, "memory": memory, "cpu": cpu
        },
        resolve=True
    )
    mlcube_tasks: t.List[str] = list(
        (mlcube_config.get("tasks", None) or {}).keys()
    )  # Tasks in this MLCube.
    tasks: t.List[str] = CliParser.parse_list_arg(
        task, default=None
    )  # Requested tasks.

    if len(tasks) == 0:
        logger.warning(
            "Missing required task name (--task=COMMA_SEPARATED_LIST_OF_TASK_NAMES)."
        )
        if len(mlcube_tasks) != 1:
            logger.error(
                "Task name could not be automatically resolved (supported tasks = %s).",
                str(mlcube_tasks),
            )
            exit(1)
        logger.info(
            "Task name has been automatically resolved to %s (supported tasks = %s).",
            mlcube_tasks[0],
            str(mlcube_tasks),
        )
        tasks = mlcube_tasks

    unknown_tasks: t.List[str] = [name for name in tasks if name not in mlcube_tasks]
    if len(unknown_tasks) > 0:
        logger.error(
            "Unknown tasks have been requested: supported tasks = %s, requested tasks = %s, "
            "unknown tasks = %s.",
            str(mlcube_tasks),
            str(tasks),
            str(unknown_tasks),
        )
        exit(1)

    try:
        # TODO: Sergey - Can we have one instance for all tasks?
        for task in tasks:
            logger.info("Task = %s", task)
            runner = runner_cls(mlcube_config, task=task)
            runner.run()
    except MLCubeError as err:
        exit_code = err.context.get("code", 1) if isinstance(err, ExecutionError) else 1
        logger.exception(f"Failed to run MLCube with error code {exit_code}.")
        if isinstance(err, ExecutionError):
            print(err.describe())
        sys.exit(exit_code)


@cli.command(
    name='describe', cls=MLCubeCommand, add_help_option=False, epilog=UsageExamples.describe,
    context_settings={'max_content_width': _TERMINAL_WIDTH}
)
@Options.mlcube
@Options.help
def describe(mlcube: t.Optional[str]) -> None:
    """Describe this MLCube.

    \f
    Args:
        mlcube: Path to MLCube root directory or mlcube.yaml file.
    """
    if mlcube is None:
        mlcube = os.getcwd()
    _, mlcube_config = parse_cli_args(
        unparsed_args=[],
        parsed_args={"mlcube": mlcube},
        resolve=True
    )
    print("MLCube")
    print(f"  path = {mlcube_config.runtime.root}")
    print(f"  name = {mlcube_config.name}:{mlcube_config.get('version', 'latest')}")
    print()
    print(f"  workspace = {mlcube_config.runtime.workspace}")
    print(f"  system settings = {SystemSettings.system_settings_file()}")
    print()
    print("  Tasks:")
    for task_name, task_def in mlcube_config.tasks.items():
        description = f"name = {task_name}"
        if len(task_def.parameters.inputs) > 0:
            description = (
                f"{description}, inputs = {list(task_def.parameters.inputs.keys())}"
            )
        if len(task_def.parameters.outputs) > 0:
            description = (
                f"{description}, outputs = {list(task_def.parameters.outputs.keys())}"
            )
        print(f"    {description}")
    print()
    print("Run this MLCube:")
    print("  Configure MLCube:")
    print(
        f"    mlcube configure --mlcube={mlcube_config.runtime.root} --platform=docker"
    )
    print("  Run MLCube tasks:")
    for task_name in mlcube_config.tasks.keys():
        print(
            f"    mlcube run --mlcube={mlcube_config.runtime.root} --task={task_name} --platform=docker"
        )
    print()


@cli.command(
    name='config', cls=MLCubeCommand, add_help_option=False, epilog=UsageExamples.config,
    context_settings={'ignore_unknown_options': True, 'allow_extra_args': True, 'max_content_width': _TERMINAL_WIDTH}
)
@click.option(
    '--list', 'list_all', is_flag=True,
    help="Print out the content of system settings file."
)
@click.option(
    '--get', required=False, type=str, default=None,
    help="Return value of the key (use OmegaConf notation, e.g. `mlcube config --get runners.docker`)."
)
@click.option(
    '--create_platform', '--create-platform', required=False, cls=MultiValueOption, type=tuple, default=None,
    help="Create a new platform instance for this runner. Default runner parameters are used to initialize this new "
         "platform."
)
@click.option(
    '--remove_platform', '--remove-platform', required=False, type=str, default=None,
    help="Remove this platform. If this is one of the default platforms (e.g., `docker`), it will be recreated (with "
         "default values) next time `mlcube` runs."
)
@click.option(
    '--rename_platform', '--rename-platform', required=False, cls=MultiValueOption, type=tuple, default=None,
    help="Rename existing platform. If default platform is to be renamed (e.g., `docker`), it will be recreated "
         "(with default values) next time `mlcube` runs."
)
@click.option(
    '--copy_platform', '--copy-platform', required=False, cls=MultiValueOption, type=tuple, default=None,
    help="Copy existing platform. This can be useful for creating new platforms off existing platforms, for instance,"
         "creating a new SSH runner configuration that runs MLCubes on a new remote server."
)
@click.option(
    '--rename_runner', '--rename-runner', required=False, cls=MultiValueOption, type=tuple, default=None,
    help="Rename existing MLCube runner. If platforms exist that reference this runner, users must explicitly provide "
         "`--update-platforms` flag to confirm they want to update platforms' description too."
)
@click.option(
    '--remove_runner', '--remove-runner', required=False, type=str, default=None,
    help="Remove existing runner. If platforms exist that reference this runner, users must explicitly provide "
         "`--remove-platforms` flag to confirm they want to remove platforms too."
)
@Options.help
@click.pass_context
def config(ctx: click.core.Context,
           list_all: bool,                          # mlcube config --list
           get: t.Optional[str],                    # mlcube config --get KEY
           create_platform: t.Optional[t.Tuple],    # mlcube config --create-platform RUNNER PLATFORM
           remove_platform: t.Optional[str],        # mlcube config --remove-platform NAME
           rename_platform: t.Optional[t.Tuple],    # mlcube config --rename-platform OLD_NAME NEW_NAME
           copy_platform: t.Optional[t.Tuple],      # mlcube config --copy-platform EXISTING_PLATFORM NEW_PLATFORM
           rename_runner: t.Optional[t.Tuple],      # mlcube config --rename-runner OLD_NAME NEW_NAME
           remove_runner: t.Optional[str]           # mlcube config --remove-runner NAME
           ) -> None:
    """Work with MLCube [system settings](https://mlcommons.github.io/mlcube/getting-started/system-settings/) similar
    to `git config`.

    Manage MLCube system settings (these settings define global configuration common for all MLCube runners and
    platforms). When this command runs without arguments, a path to system settings file is printed out. This is useful
    to automate certain operations with system settings. Alternatively, it may be easier to manipulate system settings
    file directly (it is a yaml file).
    """
    print(f"System settings file path = {SystemSettings.system_settings_file()}")
    settings = SystemSettings()

    def _check_tuple(
        _tuple: t.Tuple, _name: str, _expected_size: int, _expected_value: str
    ) -> None:
        if len(_tuple) != _expected_size:
            raise IllegalParameterValueError(
                f"--{_name}", " ".join(_tuple), f'"{_expected_value}"'
            )

    try:
        if list_all:
            print(OmegaConf.to_yaml(settings.settings))
        elif get:
            print(OmegaConf.to_yaml(OmegaConf.select(settings.settings, get)))
        elif create_platform:
            _check_tuple(
                create_platform, "create_platform", 2, "RUNNER_NAME PLATFORM_NAME"
            )
            settings.create_platform(create_platform)
        elif remove_platform:
            settings.remove_platform(remove_platform)
        elif rename_platform:
            _check_tuple(rename_platform, "rename_platform", 2, "OLD_NAME NEW_NAME")
            settings.copy_platform(rename_platform, delete_source=True)
        elif copy_platform:
            _check_tuple(
                copy_platform, "copy_platform", 2, "EXISTING_PLATFORM NEW_PLATFORM"
            )
            settings.copy_platform(rename_platform, delete_source=False)
        elif rename_runner:
            _check_tuple(rename_runner, "rename_runner", 2, "OLD_NAME NEW_NAME")
            update_platforms: bool = "--update-platforms" in ctx.args or "--update_platforms" in ctx.args
            settings.rename_runner(rename_runner, update_platforms=update_platforms)
        elif remove_runner:
            remove_platforms: bool = "--remove-platforms" in ctx.args or "--remove_platforms" in ctx.args
            settings.remove_runner(remove_runner, remove_platforms=remove_platforms)
    except MLCubeError as e:
        logger.error(
            "Command failed, command = '%s' error = '%s'", " ".join(sys.argv), str(e)
        )


@cli.command(
    name='create', add_help_option=False, cls=MLCubeCommand, epilog=UsageExamples.create,
    context_settings={'max_content_width': _TERMINAL_WIDTH}
)
@Options.help
def create() -> None:
    """Create a new Python project from the MLCube cookiecutter template.

    MLCube uses the [cookiecutter](https://cookiecutter.readthedocs.io/) library with the
    [mlcube_cookiecutter](https://github.com/mlcommons/mlcube_cookiecutter) template. The library is not installed
    automatically: install it with `pip install cookiecutter`.
    """
    mlcube_cookiecutter_url = "https://github.com/mlcommons/mlcube_cookiecutter"
    try:
        from cookiecutter.main import cookiecutter

        proj_dir: str = cookiecutter(mlcube_cookiecutter_url)
        if proj_dir and os.path.isfile(os.path.join(proj_dir, "mlcube.yaml")):
            Shell.run(["mlcube", "describe", "--mlcube", proj_dir], on_error="die")
    except ImportError:
        print("Cookiecutter library not found.")
        print("\tInstall it: pip install cookiecutter")
        print(f"\tMore details: {mlcube_cookiecutter_url}")


if __name__ == "__main__":
    cli()
