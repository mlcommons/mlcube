import os
import click
from mlcommons_box import parse   # Do not remove (it registers schemas on import)
from mlcommons_box_gcp import gcp_metadata
from mlcommons_box_gcp.gcp_run import GCPRun
from mlcommons_box.common import mlbox_metadata


@click.group(name='mlcommons_box_gcp')
def cli():
    """
    MLCommons-Box GCP Runner runs boxes (packaged Machine Learning (ML) workloads) on the Google Compute Platform.
    """
    pass


@cli.command(name='configure', help='Configure remote environment for MLCommons-Box ML workload.')
@click.option('--mlbox', required=True, type=click.Path(exists=True), help='Path to MLBox directory.')
@click.option('--platform', required=True, type=click.Path(exists=True), help='Path to MLBox Platform definition file.')
def configure(mlbox: str, platform: str):
    mlbox: mlbox_metadata.MLBox = mlbox_metadata.MLBox(path=mlbox)
    mlbox.platform = gcp_metadata.Platform(path=platform)
    print(mlbox)

    runner = GCPRun(mlbox)
    runner.configure()


@cli.command(name='run', help='Run MLCommons-Box ML workload in the remote environment.')
@click.option('--mlbox', required=True, type=click.Path(exists=True), help='Path to MLBox directory.')
@click.option('--platform', required=True, type=click.Path(exists=True), help='Path to MLBox Platform definition file.')
@click.option('--task', required=True, type=click.Path(exists=True), help='Path to MLBox Task definition file.')
def run(mlbox: str, platform: str, task: str):
    mlbox: mlbox_metadata.MLBox = mlbox_metadata.MLBox(path=mlbox)
    mlbox.platform = gcp_metadata.Platform(path=platform)
    mlbox.invoke = mlbox_metadata.MLBoxInvoke(task)
    mlbox.task = mlbox_metadata.MLBoxTask(os.path.join(mlbox.tasks_path, f'{mlbox.invoke.task_name}.yaml'))
    print(mlbox)

    runner = GCPRun(mlbox)
    runner.run(task_file=task)


if __name__ == '__main__':
    cli()
