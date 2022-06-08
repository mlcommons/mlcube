"""
This requires the MLCube 2.0 that's located somewhere in one of dev branches.
"""
import os
import sys
import click
import logging
import coloredlogs
import typing as t
from omegaconf import (OmegaConf, DictConfig)
from mlcube.config import MLCubeConfig
from mlcube.errors import (IllegalParameterValueError, MLCubeError, ExecutionError)
from mlcube.parser import (CliParser, MLCubeDirectory)
from mlcube.platform import Platform
from mlcube.runner import Runner
from mlcube.shell import Shell
from mlcube.system_settings import SystemSettings
from mlcube.validate import Validate

logger = logging.getLogger(__name__)


class MultiValueOption(click.Option):
    def __init__(self, *args, **kwargs) -> None:
        super(MultiValueOption, self).__init__(*args, **kwargs)
        self._previous_parser_process: t.Optional[t.Callable] = None
        self._eat_all_parser: t.Optional[click.parser.Option] = None

    def add_to_parser(self, parser: click.parser.OptionParser, ctx: click.core.Context):

        def parser_process(value: t.Text, state: click.parser.ParsingState):
            values: t.List[t.Text] = [value]
            prefixes: t.Tuple[t.Text] = tuple(self._eat_all_parser.prefixes)
            while state.rargs:
                if state.rargs[0].startswith(prefixes):
                    break
                values.append(state.rargs.pop(0))
            self._previous_parser_process(tuple(values), state)

        super(MultiValueOption, self).add_to_parser(parser, ctx)
        for opt_name in self.opts:
            our_parser: t.Optional[click.parser.Option] = parser._long_opt.get(opt_name) or\
                                                          parser._short_opt.get(opt_name)
            if our_parser:
                self._eat_all_parser = our_parser
                self._previous_parser_process = our_parser.process
                our_parser.process = parser_process
                break


def _parse_cli_args(ctx: t.Optional[click.core.Context], mlcube: t.Text, platform: t.Optional[t.Text],
                    workspace: t.Optional[t.Text],
                    resolve: bool) -> t.Tuple[t.Optional[t.Type[Runner]], DictConfig]:
    """
    Args:
        ctx: Click context. We need this to get access to extra CLI arguments.
        mlcube: Path to MLCube root directory or mlcube.yaml file.
        platform: Platform to use to run this MLCube (docker, singularity, gcp, k8s etc).
        workspace: Workspace path to use. If not specified, default workspace inside MLCube directory is used.
        resolve: if True, compute values in MLCube configuration.
    """
    mlcube_inst: MLCubeDirectory = CliParser.parse_mlcube_arg(mlcube)
    Validate.validate_type(mlcube_inst, MLCubeDirectory)
    if ctx is not None:
        mlcube_cli_args, task_cli_args = CliParser.parse_extra_arg(*ctx.args)
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


log_level_option = click.option(
    '--log-level', '--log_level', required=False, type=str, default='warning',
    help="Log level to set, default is to do nothing."
)
mlcube_option = click.option(
    '--mlcube', required=False, type=str, default=os.getcwd(),
    help="Path to MLCube. This can be either a directory path that becomes MLCube's root directory, or path to MLCube"
         "definition file (.yaml). In the latter case the MLCube's root directory becomes parent directory of the yaml"
         "file. Default is current directory."
)
platform_option = click.option(
    '--platform', required=False, type=str, default='docker',
    help="Platform to run MLCube, default is 'docker' (that also supports podman)."
)
task_option = click.option(
    '--task', required=False, type=str, default=None,
    help="MLCube task name(s) to run, default is `main`. This parameter can take a list value, in which case task names"
         "are separated with ','."
)
workspace_option = click.option(
    '--workspace', required=False, type=str, default=None,
    help="Workspace location that is used to store input/output artifacts of MLCube tasks."
)


@click.group(name='mlcube', help="MLCube 📦 is a packaging tool for ML models")
@log_level_option
def cli(log_level: t.Text):
    if log_level:
        log_level = log_level.upper()
        logging.basicConfig(level=log_level)
        coloredlogs.install(level=log_level)
        logging.info("Setting Log Level from CLI argument to '%s'.", log_level)
    _ = SystemSettings().update_installed_runners()


@cli.command(name='show_config', help='Show MLCube configuration.',
             context_settings=dict(ignore_unknown_options=True, allow_extra_args=True))
@mlcube_option
@platform_option
@workspace_option
@click.option('--resolve', is_flag=True, help="Resolve MLCube parameters.")
@click.pass_context
def show_config(ctx: click.core.Context, mlcube: t.Text, platform: t.Text, workspace: t.Text, resolve: bool) -> None:
    """
    Args:
        ctx: Click context. We need this to get access to extra CLI arguments.
        mlcube: Path to MLCube root directory or mlcube.yaml file.
        platform: Platform to use to run this MLCube (docker, singularity, gcp, k8s etc).
        workspace: Workspace path to use. If not specified, default workspace inside MLCube directory is used.
        resolve: if True, compute values in MLCube configuration.
    """
    _, mlcube_config = _parse_cli_args(ctx, mlcube, platform, workspace, resolve)
    print(OmegaConf.to_yaml(mlcube_config))


@cli.command(name='configure', help='Configure MLCube.',
             context_settings=dict(ignore_unknown_options=True, allow_extra_args=True))
@mlcube_option
@platform_option
@click.pass_context
def configure(ctx: click.core.Context, mlcube: t.Text, platform: t.Text) -> None:
    """
    Args:
        ctx: Click context. We need this to get access to extra CLI arguments.
        mlcube: Path to MLCube root directory or mlcube.yaml file.
        platform: Platform to use to configure this MLCube for (docker, singularity, gcp, k8s etc).
    """
    logger.info("Configuring MLCube (`%s`) for `%s` platform.", os.path.abspath(mlcube), platform)
    try:
        runner_cls, mlcube_config = _parse_cli_args(ctx, mlcube, platform, workspace=None, resolve=True)
        runner = runner_cls(mlcube_config, task=None)
        runner.configure()
    except MLCubeError as err:
        exit_code = err.context.get('code', 1) if isinstance(err, ExecutionError) else 1
        logger.exception(f"Failed to configure MLCube with error code {exit_code}.")
        if isinstance(err, ExecutionError):
            print(err.describe())
        sys.exit(exit_code)
    logger.info("MLCube (%s) has been successfully configured for `%s` platform.", os.path.abspath(mlcube), platform)


@cli.command(name='run', help='Run MLCube ML task.',
             context_settings=dict(ignore_unknown_options=True, allow_extra_args=True))
@mlcube_option
@platform_option
@task_option
@workspace_option
@click.pass_context
def run(ctx: click.core.Context, mlcube: t.Text, platform: t.Text, task: t.Text, workspace: t.Text) -> None:
    """
    Args:
        ctx: Click context. We need this to get access to extra CLI arguments.
        mlcube: Path to MLCube root directory or mlcube.yaml file.
        platform: Platform to use to run this MLCube (docker, singularity, gcp, k8s etc).
        task: Comma separated list of tasks to run.
        workspace: Workspace path to use. If not specified, default workspace inside MLCube directory is used.
    """
    runner_cls, mlcube_config = _parse_cli_args(ctx, mlcube, platform, workspace, resolve=True)
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


@cli.command(name='describe', help='Describe MLCube.')
@mlcube_option
def describe(mlcube: t.Text) -> None:
    _, mlcube_config = _parse_cli_args(None, mlcube, None, None, resolve=True)
    print(f"MLCube")
    print(f"  path = {mlcube_config.runtime.root}")
    print(f"  name = {mlcube_config.name}:{mlcube_config.get('version', 'latest')}")
    print()
    print(f"  workspace = {mlcube_config.runtime.workspace}")
    print(f"  system settings = {SystemSettings.system_settings_file()}")
    print()
    print(f"  Tasks:")
    for task_name, task_def in mlcube_config.tasks.items():
        description = f"name = {task_name}"
        if len(task_def.parameters.inputs) > 0:
            description = f"{description}, inputs = {list(task_def.parameters.inputs.keys())}"
        if len(task_def.parameters.outputs) > 0:
            description = f"{description}, outputs = {list(task_def.parameters.outputs.keys())}"
        print(f"    {description}")
    print()
    print(f"Run this MLCube:")
    print("  Configure MLCube:")
    print(f"    mlcube configure --mlcube={mlcube_config.runtime.root} --platform=docker")
    print("  Run MLCube tasks:")
    for task_name in mlcube_config.tasks.keys():
        print(f"    mlcube run --mlcube={mlcube_config.runtime.root} --task={task_name} --platform=docker")
    print()


@cli.command(name='config', help='Perform various operations with system settings file.',
             context_settings=dict(ignore_unknown_options=True, allow_extra_args=True))
@click.option('--list', 'list_all', is_flag=True, help="List configuration in MLCube system settings file.")
@click.option('--get', required=False, type=str, default=None,
              help="Return value of the key (use OmegaConf notation, e.g. --get runners.docker).")
@click.option('--create_platform', '--create-platform', required=False, cls=MultiValueOption, type=tuple, default=None,
              help="Create a new platform instance for this runner")
@click.option('--remove_platform', '--remove-platform', required=False, type=str, default=None,
              help="Remove this platform from list of platforms in system settings file.")
@click.option('--rename_platform', '--rename-platform', required=False, cls=MultiValueOption, type=tuple, default=None,
              help="Rename existing platform. If default platform is to be renamed (like docker), it will be recreated "
                   "(with default values) next time mlcube runs")
@click.option('--copy_platform', '--copy-platform', required=False, cls=MultiValueOption, type=tuple, default=None,
              help="Copy existing platform.")
@click.option('--rename_runner', '--rename-runner', required=False, cls=MultiValueOption, type=tuple, default=None,
              help="Rename existing runner. If platforms exist that reference this runner, users must explicitly "
                   "provide `--update-platforms` flag to confirm they want to update platforms' description too.")
@click.option('--remove_runner', '--remove-runner', required=False, type=str, default=None,
              help="Remove existing runner from the list. If platforms exist that reference this runner, users must "
                   "explicitly provide `--remove-platforms` flag to confirm they want to remove platforms too.")
@click.pass_context
def config(ctx: click.core.Context,
           list_all: bool,                          # mlcube config --list
           get: t.Optional[t.Text],                 # mlcube config --get KEY
           create_platform: t.Optional[t.Tuple],    # mlcube config --create-platform RUNNER PLATFORM
           remove_platform: t.Optional[t.Text],     # mlcube config --remove-platform NAME
           rename_platform: t.Optional[t.Tuple],    # mlcube config --rename-platform OLD_NAME NEW_NAME
           copy_platform: t.Optional[t.Tuple],      # mlcube config --copy-platform EXISTING_PLATFORM NEW_PLATFORM
           rename_runner: t.Optional[t.Tuple],      # mlcube config --rename-runner OLD_NAME NEW_NAME
           remove_runner: t.Optional[t.Text]        # mlcube config --remove-runner NAME
           ) -> None:
    """ Work with MLCube system settings (similar to `git config`). """
    print(f"System settings file path = {SystemSettings.system_settings_file()}")
    settings = SystemSettings()

    def _check_tuple(_tuple: t.Tuple, _name: t.Text, _expected_size: int, _expected_value: t.Text) -> None:
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


@cli.command(name='create',
             help='Create a new MLCube using cookiecutter.')
def create() -> None:
    """ Create a new MLCube using cookiecutter template.
      - MLCube cookiecutter: https://github.com/mlcommons/mlcube_cookiecutter
      - Example: https://mlcommons.github.io/mlcube/tutorials/create-mlcube/
    """
    mlcube_cookiecutter_url = 'https://github.com/mlcommons/mlcube_cookiecutter'
    try:
        from cookiecutter.main import cookiecutter
        proj_dir: t.Text = cookiecutter(mlcube_cookiecutter_url)
        if proj_dir and os.path.isfile(os.path.join(proj_dir, 'mlcube.yaml')):
            Shell.run(['mlcube', 'describe', '--mlcube', proj_dir], on_error='die')
    except ImportError:
        print("Cookiecutter library not found.")
        print("\tInstall it: pip install cookiecutter")
        print(f"\tMore details: {mlcube_cookiecutter_url}")


if __name__ == "__main__":
    cli()
