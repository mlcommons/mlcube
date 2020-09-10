import os
import click
from mlcommons_box import parse   # Do not remove (it registers schemas on import)
from mlcommons_box.common import mlbox_metadata
from mlcommons_box_singularity_run import metadata
from mlcommons_box_singularity_run.singularity_run import SingularityRun


metadata.MLSchemaRegistrar.register()


@click.group(name='mlbox_docker_run')
def cli():
    pass


@cli.command(name='configure', help='Configure docker-based MLBox on a local host.')
@click.option('--mlbox', required=True, type=click.Path(exists=True), help='Path to MLBox directory.')
@click.option('--platform', required=True, type=click.Path(exists=True), help='Path to MLBox Platform definition file.')
def configure(mlbox: str, platform: str):
    mlbox: mlbox_metadata.MLBox = mlbox_metadata.MLBox(path=mlbox)
    mlbox.platform = metadata.SingularityPlatform(path=platform, mlbox=mlbox)
    print(mlbox)

    runner = SingularityRun(mlbox)
    runner.configure()


@cli.command(name='run', help='Run docker-based MLBox on a local host.')
@click.option('--mlbox', required=True, type=click.Path(exists=True), help='Path to MLBox directory.')
@click.option('--platform', required=True, type=click.Path(exists=True), help='Path to MLBox Platform definition file.')
@click.option('--task', required=True, type=click.Path(exists=True), help='Path to MLBox Task definition file.')
def run(mlbox: str, platform: str, task: str):
    mlbox: mlbox_metadata.MLBox = mlbox_metadata.MLBox(path=mlbox)
    mlbox.platform = metadata.SingularityPlatform(path=platform, mlbox=mlbox)
    mlbox.invoke = mlbox_metadata.MLBoxInvoke(task)
    mlbox.task = mlbox_metadata.MLBoxTask(os.path.join(mlbox.tasks_path, f'{mlbox.invoke.task_name}.yaml'))
    print(mlbox)

    runner = SingularityRun(mlbox)
    runner.run()


if __name__ == '__main__':
    cli()
