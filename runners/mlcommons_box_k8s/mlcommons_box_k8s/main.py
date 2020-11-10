import logging
import click

from mlcommons_box import parse  # Do not remove (it registers schemas on import)
from mlcommons_box.common import mlbox_metadata, objects
from mlcommons_box.common.objects import platform_config
from mlcommons_box_k8s.k8s_run import KubernetesRun


@click.group(name='mlcommons_box_k8s')
def cli():
    """
    MLCommons-Box k8s Runner runs boxes (packaged Machine Learning workloads) in a Kubernetes cluster.
    """
    pass


@cli.command(name="run")
@click.option('--mlbox',
              required=True,
              type=click.Path(exists=True),
              help='Path to MLBox directory.')
@click.option('--platform',
              required=True,
              type=click.Path(exists=True),
              help='Path to MLBox Platform definition file.')
@click.option('--task',
              required=True,
              type=click.Path(exists=True),
              help='Path to MLBox Task definition file.')
@click.option('--loglevel',
              required=False,
              type=click.STRING,
              default="DEBUG",
              help='Log level for the CLI app.')
def run(mlbox: str, platform: str, task: str, loglevel: str):
    """
    Runs a MLBox in a Kubernetes cluster.
    """
    # set loglevel for CLI
    logging.basicConfig(format='%(asctime)s - %(message)s',
                        datefmt='%d-%b-%y-%H:%M:%S',
                        level=loglevel)
    logger = logging.getLogger(__name__)

    logger.info("Configuring MLBox platform, task for Kubernetes...")
    mlbox: mlbox_metadata.MLBox = mlbox_metadata.MLBox(path=mlbox)
    mlbox.platform = objects.load_object_from_file(
        file_path=platform, obj_class=platform_config.PlatformConfig)
    mlbox.invoke = mlbox_metadata.MLBoxInvoke(task)
    logger.info("MLBox: %s", mlbox)

    runner = KubernetesRun(mlbox, loglevel)
    runner.run()
