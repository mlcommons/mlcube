import os
import click
from mlcube import parse   # Do not remove (it registers schemas on import)
from mlcube_gcp import gcp_metadata
from mlcube_gcp.gcp_run import GCPRun
from mlcube.common import mlcube_metadata


@click.group(name='mlcube_gcp')
def cli():
    """
    MLCube GCP Runner runs cubes (packaged Machine Learning (ML) workloads) on the Google Compute Platform.
    """
    pass


@cli.command(name='configure', help='Configure remote environment for MLCube ML workload.')
@click.option('--mlcube', required=True, type=click.Path(exists=True), help='Path to MLCube directory.')
@click.option('--platform', required=True, type=click.Path(exists=True), help='Path to MLCube Platform definition file.')
def configure(mlcube: str, platform: str):
    mlcube: mlcube_metadata.MLCube = mlcube_metadata.MLCube(path=mlcube)
    mlcube.platform = gcp_metadata.Platform(path=platform)
    print(mlcube)

    runner = GCPRun(mlcube)
    runner.configure()


@cli.command(name='run', help='Run MLCube ML workload in the remote environment.')
@click.option('--mlcube', required=True, type=click.Path(exists=True), help='Path to MLCube directory.')
@click.option('--platform', required=True, type=click.Path(exists=True), help='Path to MLCube Platform definition file.')
@click.option('--task', required=True, type=click.Path(exists=True), help='Path to MLCube Task definition file.')
def run(mlcube: str, platform: str, task: str):
    mlcube: mlcube_metadata.MLCube = mlcube_metadata.MLCube(path=mlcube)
    mlcube.platform = gcp_metadata.Platform(path=platform)
    mlcube.invoke = mlcube_metadata.MLCubeInvoke(task)
    mlcube.task = mlcube_metadata.MLCubeTask(os.path.join(mlcube.tasks_path, f'{mlcube.invoke.task_name}.yaml'))
    print(mlcube)

    runner = GCPRun(mlcube)
    runner.run(task_file=task)


if __name__ == '__main__':
    cli()
