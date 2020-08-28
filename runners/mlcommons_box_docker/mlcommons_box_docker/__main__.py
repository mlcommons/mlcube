import os
import click
from mlcommons_box import parse   # Do not remove (it registers schemas on import)
from mlcommons_box.common import mlbox_metadata
from mlcommons_box.common import objects
from mlcommons_box.common.objects import platform_config

from mlcommons_box_docker.docker_run import DockerRun


@click.group(name='mlcommons_box_docker')
def cli():
    """
    MLCommons-Box Docker Runner runs boxes (packaged Machine Learning (ML) workloads) in the docker environment.
    """
    pass


@cli.command(name='configure', help='Configure docker environment for MLCommons-Box ML workload.')
@click.option('--mlbox', required=True, type=click.Path(exists=True), help='Path to MLBox directory.')
@click.option('--platform', required=True, type=click.Path(exists=True), help='Path to MLBox Platform definition file.')
def configure(mlbox: str, platform: str):
    mlbox: mlbox_metadata.MLBox = mlbox_metadata.MLBox(path=mlbox)
    mlbox.platform = objects.load_object_from_file(
            file_path=platform, obj_class=platform_config.PlatformConfig)
    print(mlbox)

    runner = DockerRun(mlbox)
    runner.configure()


@cli.command(name='run', help='Run MLCommons-Box ML workload in the docker environment.')
@click.option('--mlbox', required=True, type=click.Path(exists=True), help='Path to MLBox directory.')
@click.option('--platform', required=True, type=click.Path(exists=True), help='Path to MLBox Platform definition file.')
@click.option('--task', required=True, type=click.Path(exists=True), help='Path to MLBox Task definition file.')
def run(mlbox: str, platform: str, task: str):
    mlbox: mlbox_metadata.MLBox = mlbox_metadata.MLBox(path=mlbox)
    mlbox.platform = objects.load_object_from_file(
            file_path=platform, obj_class=platform_config.PlatformConfig)
    mlbox.invoke = mlbox_metadata.MLBoxInvoke(task)
    mlbox.task = mlbox_metadata.MLBoxTask(os.path.join(mlbox.tasks_path, f'{mlbox.invoke.task_name}.yaml'))
    print(mlbox)

    runner = DockerRun(mlbox)
    runner.run()


if __name__ == '__main__':
    cli()
