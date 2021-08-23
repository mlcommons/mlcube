"""
This requires the MLCube 2.0 that's located somewhere in one of dev branches.
"""
import importlib
import os
import click
import logging
import coloredlogs
import typing as t
from omegaconf import OmegaConf
from mlcube import validate_type
from mlcube.config import MLCubeConfig
from mlcube.parser import (CliParser, MLCubeDirectory)


logger = logging.getLogger(__name__)


class Platforms(object):
    @staticmethod
    def get_runner(platform: t.Text) -> t.Callable:
        """Return runner class or create function for given platform.
        Args:
            platform: Platform name (e.g. `docker`, `podman`, `ssh`, `gcp`, `k8s` etc.).
        Returns:
            Callable object (e.g. runner class) that can create runner instance.
        """
        from mlcube import default_runners
        platform = platform.lower()
        runner_csl: t.Optional[t.Text] = None
        for default_runner in default_runners:
            if default_runner['platform'] == platform:
                runner_csl = default_runner['cls']
                break
        if runner_csl is None:
            raise RuntimeError(f"Unknown platform: '{platform}'.")

        module_name, cls_name = runner_csl.rsplit('.', 1)
        try:
            runner_module = importlib.import_module(module_name)
            Runner = getattr(runner_module, cls_name)
            logger.info("[RUNNER] platform = %s, module = %s, cls = %s imported OK.", platform, module_name, cls_name)
        except (ImportError, AttributeError):
            logger.warning("Runner (%s) could not imported.", runner_csl)
            raise
        return Runner


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
    '--task', required=False, type=str, default='main',
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
    mlcube_inst: MLCubeDirectory = CliParser.parse_mlcube_arg(mlcube)
    validate_type(mlcube_inst, MLCubeDirectory)
    mlcube_cli_args, task_cli_args = CliParser.parse_extra_arg(*ctx.args)
    mlcube_config = MLCubeConfig.create_mlcube_config(
        os.path.join(mlcube_inst.path, mlcube_inst.file), mlcube_cli_args, task_cli_args, platform, workspace,
        resolve=resolve
    )
    print(OmegaConf.to_yaml(mlcube_config))


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
    mlcube_inst: MLCubeDirectory = CliParser.parse_mlcube_arg(mlcube)
    validate_type(mlcube_inst, MLCubeDirectory)
    mlcube_cli_args, task_cli_args = CliParser.parse_extra_arg(*ctx.args)
    mlcube_config = MLCubeConfig.create_mlcube_config(
        os.path.join(mlcube_inst.path, mlcube_inst.file), mlcube_cli_args, task_cli_args, platform, workspace,
        resolve=True
    )
    runner_cls: t.Callable = Platforms.get_runner(platform)
    tasks: t.List[str] = CliParser.parse_list_arg(task, default='main')
    for task in tasks:
        docker_runner = runner_cls(mlcube_config, task=task)
        docker_runner.run()


@cli.command(name='describe', help='Describe MLCube.')
@mlcube_option
def run(mlcube: t.Text) -> None:
    mlcube_inst: MLCubeDirectory = CliParser.parse_mlcube_arg(mlcube)
    validate_type(mlcube_inst, MLCubeDirectory)
    mlcube_config = MLCubeConfig.create_mlcube_config(
        os.path.join(mlcube_inst.path, mlcube_inst.file), mlcube_cli_args=None, task_cli_args=None, platform=None,
        resolve=True
    )
    print(f"MLCube")
    print(f"  path = {mlcube_config.runtime.root}")
    print(f"  name = {mlcube_config.name}:{mlcube_config.get('version', 'latest')}")
    print()
    print(f"  workspace = {mlcube_config.runtime.workspace}")
    if os.path.exists(mlcube_config.runtime.global_config.uri) and not mlcube_config.runtime.global_config.ignore:
        print(f"  system settings = {mlcube_config.runtime.global_config.uri}")
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


if __name__ == "__main__":
    cli()
