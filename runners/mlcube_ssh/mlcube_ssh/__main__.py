import os
import click
from mlcube import parse   # Do not remove (it registers schemas on import)
from mlcube.common import mlcube_metadata
from mlcube_ssh import ssh_metadata
from mlcube_ssh.ssh_run import SSHRun


def configure_(mlcube: str, platform: str):
    mlcube: mlcube_metadata.MLCube = mlcube_metadata.MLCube(path=mlcube)
    mlcube.platform = ssh_metadata.Platform(path=platform)
    print(mlcube)

    runner = SSHRun(mlcube)
    runner.configure()


def run_(mlcube: str, platform: str, task: str):
    mlcube: mlcube_metadata.MLCube = mlcube_metadata.MLCube(path=mlcube)
    mlcube.platform = ssh_metadata.Platform(path=platform)
    mlcube.invoke = mlcube_metadata.MLCubeInvoke(task)
    mlcube.task = mlcube_metadata.MLCubeTask(os.path.join(mlcube.tasks_path, f'{mlcube.invoke.task_name}.yaml'))
    print(mlcube)

    runner = SSHRun(mlcube)
    runner.run(task_file=task)


@click.group(name='mlcube_ssh')
def cli():
    """
    MLCube SSH Runner runs cubes (packaged Machine Learning (ML) workloads) in the remote environment.
    """
    pass


@cli.command(name='configure', help='Configure remote environment for MLCube ML workload.')
@click.option('--mlcube', required=True, type=click.Path(exists=True), help='Path to MLCube directory.')
@click.option('--platform', required=True, type=click.Path(exists=True), help='Path to MLCube Platform definition file.')
def configure(mlcube: str, platform: str):
    configure_(mlcube, platform)


@cli.command(name='run', help='Run MLCube ML workload in the remote environment.')
@click.option('--mlcube', required=True, type=click.Path(exists=True), help='Path to MLCube directory.')
@click.option('--platform', required=True, type=click.Path(exists=True), help='Path to MLCube Platform definition file.')
@click.option('--task', required=True, type=click.Path(exists=True), help='Path to MLCube Task definition file.')
def run(mlcube: str, platform: str, task: str):
    run_(mlcube, platform, task)


if __name__ == '__main__':
    cli()
