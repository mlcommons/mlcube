"""This requires the MLCube 2.0 that's located somewhere in one of dev branches."""
import logging
import os
import sys
import typing as t

import click

import coloredlogs

from mlcube.config import MLCubeConfig
from mlcube.errors import (ExecutionError, IllegalParameterValueError, MLCubeError)
from mlcube.parser import (CliParser, MLCubeDirectory)
from mlcube.platform import Platform
from mlcube.runner import Runner
from mlcube.shell import Shell
from mlcube.system_settings import SystemSettings
from mlcube.validate import Validate

from omegaconf import (DictConfig, OmegaConf)

logger = logging.getLogger(__name__)


class MultiValueOption(click.Option):
    def __init__(self, *args, **kwargs) -> None:
        super(MultiValueOption, self).__init__(*args, **kwargs)
        self._previous_parser_process: t.Optional[t.Callable] = None
        self._eat_all_parser: t.Optional[click.parser.Option] = None

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
            our_parser: t.Optional[click.parser.Option] = \
                parser._long_opt.get(opt_name) or parser._short_opt.get(opt_name)
            if our_parser:
                self._eat_all_parser = our_parser
                self._previous_parser_process = our_parser.process
                our_parser.process = parser_process
                break


def _parse_cli_args(ctx: t.Optional[t.Union[click.core.Context, t.List[str]]],
                    mlcube: t.Optional[str], platform: t.Optional[str],
                    workspace: t.Optional[str],
                    resolve: bool) -> t.Tuple[t.Optional[t.Type[Runner]], DictConfig]:
    """Parse command line arguments.

    Args:
        ctx: Click context or list of extra arguments from a command line. We need this to get access to extra
             CLI arguments.
        mlcube: Path to MLCube root directory or mlcube.yaml file.
        platform: Platform to use to run this MLCube (docker, singularity, gcp, k8s etc).
        workspace: Workspace path to use. If not specified, default workspace inside MLCube directory is used.
        resolve: if True, compute values in MLCube configuration.
    """
    if mlcube is None:
        mlcube = os.getcwd()
    mlcube_inst: MLCubeDirectory = CliParser.parse_mlcube_arg(mlcube)
    Validate.validate_type(mlcube_inst, MLCubeDirectory)
    if ctx is not None:
        _ctx = ctx
        if isinstance(_ctx, click.core.Context):
            _ctx = _ctx.args
        mlcube_cli_args, task_cli_args = CliParser.parse_extra_arg(*_ctx)
    else:
        mlcube_cli_args, task_cli_args = None, None
    if platform is not None:
        system_settings = SystemSettings()
        runner_config: t.Optional[DictConfig] = system_settings.get_platform(platform)
        runner_cls: t.Optional[t.Type[Runner]] = Platform.get_runner(
            system_settings.runners.get(runner_config.runner, None)
        )
    else:
        runner_cls, runner_config = None, None
    mlcube_config = MLCubeConfig.create_mlcube_config(
        os.path.join(mlcube_inst.path, mlcube_inst.file), mlcube_cli_args, task_cli_args, runner_config, workspace,
        resolve=resolve, runner_cls=runner_cls
    )
    return runner_cls, mlcube_config


help_option = click.help_option(
    '--help', '-h', help='Show help message and exit.'
)
log_level_option = click.option(
    '--log-level', '--log_level', required=False, type=click.Choice(['critical', 'error', 'warning', 'info', 'debug']),
    default='warning',
    help="Logging level is a lower-case string value for Python's logging library (see "
         "[Logging Levels](https://docs.python.org/3/library/logging.html#logging-levels) for more details). Only "
         "messages with this logging level or higher are logged."
)
mlcube_option = click.option(
    '--mlcube', required=False, type=str, default=None, metavar='PATH',
    help="Path to an MLCube project. It can be a directory path, or a path to an MLCube configuration file "
         "(`mlcube.yaml`). When it is a directory path, MLCube runtime assumes this directory is the MLCube root "
         "directory containing `mlcube.yaml` file. When it is a file path, this file is assumed to be the MLCube "
         "configuration file (`mlcube.yaml`), and a parent directory of this file is considered to be the MLCube root "
         "directory. Default value is current directory."
)
platform_option = click.option(
    '--platform', required=False, type=str, default='docker', metavar='NAME',
    help="Platform name to run MLCube on (a platform is a configured instance of an MLCube runner). Multiple platforms "
         "are supported, including `docker` (Docker and Podman), `singularity` (Singularity). Other runners are "
         "in experimental stage: `gcp` (Google Cloud Platform), `k8s` (Kubernetes), `kubeflow` (KubeFlow), ssh (SSH "
         "runner). Default is `docker`. Platforms are defined and configured in MLCube system settings file."
)
task_option = click.option(
    '--task', required=False, type=str, default=None,
    help="MLCube task name(s) to run, default is `main`. This parameter can take a list of values, in which case task "
         "names are separated with comma (,)."
)
workspace_option = click.option(
    '--workspace', required=False, type=str, default=None, metavar='PATH',
    help="Location of a workspace to store input and output artifacts of MLCube tasks. If not specified (None), "
         "`${MLCUBE_ROOT}/workspace/` is used."
)


@click.group(name='mlcube', add_help_option=False)
@log_level_option
@help_option
def cli(log_level: t.Optional[str]):
    """MLCube 📦 is a tool for packaging, distributing and running Machine Learning (ML) projects and models.

    \b
    GitHub: https://github.com/mlcommons/mlcube
    Documentation: https://mlcommons.github.io/mlcube/
    """

    if log_level:
        log_level = log_level.upper()
        logging.basicConfig(level=log_level)
        coloredlogs.install(level=log_level)
        logging.info("Setting Log Level from CLI argument to '%s'.", log_level)
    _ = SystemSettings().update_installed_runners()


@cli.command(
    name='show_config', context_settings={'ignore_unknown_options': True, 'allow_extra_args': True},
    add_help_option=False
)
@mlcube_option
@platform_option
@workspace_option
@click.option(
    '--resolve', is_flag=True,
    help="Resolve MLCube parameters. The `mlcube` uses [OmegaConf](https://omegaconf.readthedocs.io/) "
         "library to manage its configuration, including configuration files, system settings files and "
         "configuration parameters provided by users on command lines. OmegaConf supports variable interpolation ("
         "when one variables depend on other variables, e.g., `{'docker.image': 'mlcommons/{name}:${version}'}`). When "
         "this flag is set to true, the `mlcube` computes actual values of all variables."
)
@help_option
@click.argument('config_param', nargs=-1, type=click.UNPROCESSED)
def show_config(
        mlcube: t.Optional[str], platform: str, workspace: str, resolve: bool, config_param: t.Tuple[str]
) -> None:
    """Show effective MLCube configuration.

    Effective MLCube configuration is the one used by one of MLCube runners to run this MLCube. This configuration is
    built by merging (1) default runner configuration retrieved from system settings, (2) MLCube project configuration
    and (3) configuration parameters passed by a user on a command line (CONFIG_PARAM).

    CONFIG_PARAM Configuration parameter as a key-value pair. Must start with `-P`. The dot (.) is used to refer to
    nested parameters, for instance, `-Pdocker.build_strategy=always`. These parameters have the highest priority and
    override any other parameters in system settings and MLCube configuration.

    \f
    Args:
        mlcube: Path to MLCube root directory or mlcube.yaml file.
        platform: Platform to use to run this MLCube (docker, singularity, gcp, k8s etc).
        workspace: Workspace path to use. If not specified, default workspace inside MLCube directory is used.
        resolve: if True, compute values in MLCube configuration.
        config_param: Additional configuration parameters.
    """
    if mlcube is None:
        mlcube = os.getcwd()
    _, mlcube_config = _parse_cli_args([*config_param], mlcube, platform, workspace, resolve)
    print(OmegaConf.to_yaml(mlcube_config))


@cli.command(name='configure', context_settings={'ignore_unknown_options': True, 'allow_extra_args': True})
@mlcube_option
@platform_option
@click.argument('config_param', nargs=-1, type=click.UNPROCESSED)
def configure(mlcube: t.Optional[str], platform: str, config_param: t.Tuple[str]) -> None:
    """Configure MLCube.

    Some MLCube projects need to be configured first. For instance, docker-based MLCubes distributed via GitHub with
    source code most likely will provide a `Dockerfile` to build a docker image. In this case, the process of building
    a docker image before MLCube runner can run it, is called a configuration phase. In general, users do not need to
    run this command manually - MLCube runners should be able to figure out when they need to run it, and will run it
    as part of `mlcube run` command.

    CONFIG_PARAM Configuration parameter as a key-value pair. Must start with `-P`. The dot (.) is used to refer to
    nested parameters, for instance, `-Pdocker.build_strategy=always`. These parameters have the highest priority and
    override any other parameters in system settings and MLCube configuration.

    \f
    Args:
        mlcube: Path to MLCube root directory or mlcube.yaml file.
        platform: Platform to use to configure this MLCube for (docker, singularity, gcp, k8s etc).
        config_param: Additional configuration parameters.
    """
    if mlcube is None:
        mlcube = os.getcwd()
    logger.info("Configuring MLCube (`%s`) for `%s` platform.", os.path.abspath(mlcube), platform)
    try:
        runner_cls, mlcube_config = _parse_cli_args([*config_param], mlcube, platform, workspace=None, resolve=True)
        runner = runner_cls(mlcube_config, task=None)
        runner.configure()
    except MLCubeError as err:
        exit_code = err.context.get('code', 1) if isinstance(err, ExecutionError) else 1
        logger.exception(f"Failed to configure MLCube with error code {exit_code}.")
        if isinstance(err, ExecutionError):
            print(err.describe())
        sys.exit(exit_code)
    logger.info("MLCube (%s) has been successfully configured for `%s` platform.", os.path.abspath(mlcube), platform)


@cli.command(name='run', context_settings={'ignore_unknown_options': True, 'allow_extra_args': True})
@mlcube_option
@platform_option
@task_option
@workspace_option
@click.argument('config_param', nargs=-1, type=click.UNPROCESSED)
def run(mlcube: t.Optional[str], platform: str, task: str, workspace: str, config_param: t.Tuple[str]) -> None:
    """Run MLCube task(s).

    CONFIG_PARAM Configuration parameter as a key-value pair. Must start with `-P`. The dot (.) is used to refer to
    nested parameters, for instance, `-Pdocker.build_strategy=always`. These parameters have the highest priority and
    override any other parameters in system settings and MLCube configuration.

    \f
    Args:
        mlcube: Path to MLCube root directory or mlcube.yaml file.
        platform: Platform to use to run this MLCube (docker, singularity, gcp, k8s etc).
        task: Comma separated list of tasks to run.
        workspace: Workspace path to use. If not specified, default workspace inside MLCube directory is used.
        config_param: Additional configuration parameters.
    """
    if mlcube is None:
        mlcube = os.getcwd()
    runner_cls, mlcube_config = _parse_cli_args([*config_param], mlcube, platform, workspace, resolve=True)
    mlcube_tasks: t.List[str] = list((mlcube_config.get('tasks', None) or {}).keys())  # Tasks in this MLCube.
    tasks: t.List[str] = CliParser.parse_list_arg(task, default=None)                  # Requested tasks.

    if len(tasks) == 0:
        logger.warning("Missing required task name (--task=COMMA_SEPARATED_LIST_OF_TASK_NAMES).")
        if len(mlcube_tasks) != 1:
            logger.error("Task name could not be automatically resolved (supported tasks = %s).", str(mlcube_tasks))
            exit(1)
        logger.info("Task name has been automatically resolved to %s (supported tasks = %s).",
                    mlcube_tasks[0], str(mlcube_tasks))
        tasks = mlcube_tasks

    unknown_tasks: t.List[str] = [name for name in tasks if name not in mlcube_tasks]
    if len(unknown_tasks) > 0:
        logger.error("Unknown tasks have been requested: supported tasks = %s, requested tasks = %s, "
                     "unknown tasks = %s.", str(mlcube_tasks), str(tasks), str(unknown_tasks))
        exit(1)

    try:
        # TODO: Sergey - Can we have one instance for all tasks?
        for task in tasks:
            logger.info("Task = %s", task)
            runner = runner_cls(mlcube_config, task=task)
            runner.run()
    except MLCubeError as err:
        exit_code = err.context.get('code', 1) if isinstance(err, ExecutionError) else 1
        logger.exception(f"Failed to run MLCube with error code {exit_code}.")
        if isinstance(err, ExecutionError):
            print(err.describe())
        sys.exit(exit_code)


@cli.command(name='describe')
@mlcube_option
def describe(mlcube: t.Optional[str]) -> None:
    """Describe this MLCube.
    \f
    Args:
        mlcube: Path to MLCube root directory or mlcube.yaml file.
    """
    if mlcube is None:
        mlcube = os.getcwd()
    _, mlcube_config = _parse_cli_args(None, mlcube, None, None, resolve=True)
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
            description = f"{description}, inputs = {list(task_def.parameters.inputs.keys())}"
        if len(task_def.parameters.outputs) > 0:
            description = f"{description}, outputs = {list(task_def.parameters.outputs.keys())}"
        print(f"    {description}")
    print()
    print("Run this MLCube:")
    print("  Configure MLCube:")
    print(f"    mlcube configure --mlcube={mlcube_config.runtime.root} --platform=docker")
    print("  Run MLCube tasks:")
    for task_name in mlcube_config.tasks.keys():
        print(f"    mlcube run --mlcube={mlcube_config.runtime.root} --task={task_name} --platform=docker")
    print()


@cli.command(
    name='config', context_settings={'ignore_unknown_options': True, 'allow_extra_args': True},
    help="Manage MLCube system settings (these settings define global configuration common for all MLCube runners and "
         "platforms). When this command runs without arguments, a path to system settings file is printed out. This "
         "is useful to automate certain operations with system settings. Alternatively, it may be easier to manipulate "
         "system settings file directly (it is a yaml file)."
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
    """Work with MLCube system settings (similar to `git config`)."""
    print(f"System settings file path = {SystemSettings.system_settings_file()}")
    settings = SystemSettings()

    def _check_tuple(_tuple: t.Tuple, _name: str, _expected_size: int, _expected_value: str) -> None:
        if len(_tuple) != _expected_size:
            raise IllegalParameterValueError(f'--{_name}', ' '.join(_tuple), f"\"{_expected_value}\"")

    try:
        if list_all:
            print(OmegaConf.to_yaml(settings.settings))
        elif get:
            print(OmegaConf.to_yaml(OmegaConf.select(settings.settings, get)))
        elif create_platform:
            _check_tuple(create_platform, 'create_platform', 2, 'RUNNER_NAME PLATFORM_NAME')
            settings.create_platform(create_platform)
        elif remove_platform:
            settings.remove_platform(remove_platform)
        elif rename_platform:
            _check_tuple(rename_platform, 'rename_platform', 2, 'OLD_NAME NEW_NAME')
            settings.copy_platform(rename_platform, delete_source=True)
        elif copy_platform:
            _check_tuple(copy_platform, 'copy_platform', 2, 'EXISTING_PLATFORM NEW_PLATFORM')
            settings.copy_platform(rename_platform, delete_source=False)
        elif rename_runner:
            _check_tuple(rename_runner, 'rename_runner', 2, 'OLD_NAME NEW_NAME')
            update_platforms: bool = '--update-platforms' in ctx.args or '--update_platforms' in ctx.args
            settings.rename_runner(rename_runner, update_platforms=update_platforms)
        elif remove_runner:
            remove_platforms: bool = '--remove-platforms' in ctx.args or '--remove_platforms' in ctx.args
            settings.remove_runner(remove_runner, remove_platforms=remove_platforms)
    except MLCubeError as e:
        logger.error("Command failed, command = '%s' error = '%s'", ' '.join(sys.argv), str(e))


@cli.command(name='create', add_help_option=False)
@help_option
def create() -> None:
    """Create a new Python project from the MLCube cookiecutter template.

    The `mlcube` uses this cookiecutter [library](https://cookiecutter.readthedocs.io/) with this
    [template](https://github.com/mlcommons/mlcube_cookiecutter). Cookiecutter library is not installed automatically:
    install it with `pip install cookiecutter`.
    """
    mlcube_cookiecutter_url = 'https://github.com/mlcommons/mlcube_cookiecutter'
    try:
        from cookiecutter.main import cookiecutter
        proj_dir: str = cookiecutter(mlcube_cookiecutter_url)
        if proj_dir and os.path.isfile(os.path.join(proj_dir, 'mlcube.yaml')):
            Shell.run(['mlcube', 'describe', '--mlcube', proj_dir], on_error='die')
    except ImportError:
        print("Cookiecutter library not found.")
        print("\tInstall it: pip install cookiecutter")
        print(f"\tMore details: {mlcube_cookiecutter_url}")


if __name__ == "__main__":
    cli()
