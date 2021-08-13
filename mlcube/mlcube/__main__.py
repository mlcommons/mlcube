"""
This requires the MLCube 2.0 that's located somewhere in one of dev branches.
"""
import os
import click
import logging
import typing as t
from omegaconf import OmegaConf
from mlcube.parser import CliParser
from mlcube.config import MLCubeConfig


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
        platform = platform.lower()
        if platform in ('docker', 'podman'):
            try:
                from mlcube_docker.docker_run import DockerRun as Runner
            except ImportError:
                print(f"Docker/Podman runner (platform={platform}) could not be imported.")
                raise
        else:
            raise ValueError(f"Runner for platform '{platform}' is not supported yet.")
        return Runner


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


@click.group(name='mlcube')
def cli():
    pass


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
    mlcube_root, mlcube_file = CliParser.parse_mlcube_arg(mlcube)
    mlcube_cli_args, task_cli_args = CliParser.parse_extra_arg(*ctx.args)
    mlcube_config = MLCubeConfig.create_mlcube_config(
        os.path.join(mlcube_root, mlcube_file), mlcube_cli_args, task_cli_args, platform, workspace, resolve=resolve
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
    mlcube_root, mlcube_file = CliParser.parse_mlcube_arg(mlcube)
    mlcube_cli_args, task_cli_args = CliParser.parse_extra_arg(*ctx.args)
    mlcube_config = MLCubeConfig.create_mlcube_config(
        os.path.join(mlcube_root, mlcube_file), mlcube_cli_args, task_cli_args, platform, workspace, resolve=True
    )
    runner_cls: t.Callable = Platforms.get_runner(platform)
    tasks: t.List[str] = CliParser.parse_list_arg(task, default='main')
    for task in tasks:
        docker_runner = runner_cls(mlcube_config, task=task)
        docker_runner.run()


if __name__ == "__main__":
    cli()
