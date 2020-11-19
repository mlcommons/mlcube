import logging
import click

from mlcube import parse  # Do not remove (it registers schemas on import)
from mlcube.common import mlcube_metadata, objects
from mlcube.common.objects import platform_config
from mlcube_k8s.k8s_run import KubernetesRun


@click.group(name='mlcube_k8s')
def cli():
    """
    MLCube k8s Runner runs cubes (packaged Machine Learning workloads) in a Kubernetes cluster.
    """
    pass


@cli.command(name="run")
@click.option('--mlcube',
              required=True,
              type=click.Path(exists=True),
              help='Path to MLCube directory.')
@click.option('--platform',
              required=True,
              type=click.Path(exists=True),
              help='Path to MLCube Platform definition file.')
@click.option('--task',
              required=True,
              type=click.Path(exists=True),
              help='Path to MLCube Task definition file.')
@click.option('--loglevel',
              required=False,
              type=click.STRING,
              default="DEBUG",
              help='Log level for the CLI app.')
def run(mlcube: str, platform: str, task: str, loglevel: str):
    """
    Runs a MLCube in a Kubernetes cluster.
    """
    # set loglevel for CLI
    logging.basicConfig(format='%(asctime)s - %(message)s',
                        datefmt='%d-%b-%y-%H:%M:%S',
                        level=loglevel)
    logger = logging.getLogger(__name__)

    logger.info("Configuring MLCube platform, task for Kubernetes...")
    mlcube: mlcube_metadata.MLCube = mlcube_metadata.MLCube(path=mlcube)
    mlcube.platform = objects.load_object_from_file(
        file_path=platform, obj_class=platform_config.PlatformConfig)
    mlcube.invoke = mlcube_metadata.MLCubeInvoke(task)
    logger.info("MLCube: %s", mlcube)

    runner = KubernetesRun(mlcube, loglevel)
    runner.run()
