import os
import click
from mlcube import parse   # Do not remove (it registers schemas on import)
from mlcube.common import mlcube_metadata
from mlcube.common import objects
from mlcube.common.objects import platform_config

from mlcube_docker.docker_run import DockerRun


@click.group(name='mlcube_docker')
def cli():
    """
    MLCube Docker Runner runs cubes (packaged Machine Learning (ML) workloads) in the docker environment.
    """
    pass


@cli.command(name='configure', help='Configure docker environment for MLCube ML workload.')
@click.option('--mlcube', required=True, type=click.Path(exists=True), help='Path to MLCube directory.')
@click.option('--platform', required=True, type=click.Path(exists=True), help='Path to MLCube Platform definition file.')
def configure(mlcube: str, platform: str):
    mlcube: mlcube_metadata.MLCube = mlcube_metadata.MLCube(path=mlcube)
    mlcube.platform = objects.load_object_from_file(
            file_path=platform, obj_class=platform_config.PlatformConfig)
    print(mlcube)

    runner = DockerRun(mlcube)
    runner.configure()


@cli.command(name='run', help='Run MLCube ML workload in the docker environment.')
@click.option('--mlcube', required=True, type=click.Path(exists=True), help='Path to MLCube directory.')
@click.option('--platform', required=True, type=click.Path(exists=True), help='Path to MLCube Platform definition file.')
@click.option('--task', required=True, type=click.Path(exists=True), help='Path to MLCube Task definition file.')
def run(mlcube: str, platform: str, task: str):
    mlcube: mlcube_metadata.MLCube = mlcube_metadata.MLCube(path=mlcube)
    mlcube.platform = objects.load_object_from_file(
            file_path=platform, obj_class=platform_config.PlatformConfig)
    mlcube.invoke = mlcube_metadata.MLCubeInvoke(task)
    mlcube.task = mlcube_metadata.MLCubeTask(os.path.join(mlcube.tasks_path, f'{mlcube.invoke.task_name}.yaml'))
    print(mlcube)

    runner = DockerRun(mlcube)
    runner.run()


if __name__ == '__main__':
    cli()
