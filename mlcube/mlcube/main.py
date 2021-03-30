import os
import click
import logging
import coloredlogs
from halo import Halo
from pathlib import Path
from typing import Optional
from mlcube.check import check_root_dir
from mlcube.common.mlcube_metadata import (MLCubeFS, CompactMLCube)


logger = logging.getLogger(__name__)


@click.group(name='mlcube', help="MLCube 📦 is a packaging tool for ML models")
@click.option('--log-level', default="INFO", help="Log level for the app.")
def cli(log_level: str):
    click.echo(f"Log level is set to - {log_level}")
    coloredlogs.install(level=log_level)


@cli.command(name='verify', help='Verify MLCube metadata.')
@click.option('--mlcube', required=False, type=str, help='MLCube path.')
@Halo(text="", spinner="dots")
def verify(mlcube: Optional[str]) -> None:
    logging.info("Starting mlcube metadata verification")
    mlcube_path = CompactMLCube(mlcube).unpack().mlcube_fs.root
    metadata, verify_err = check_root_dir(mlcube_path)
    if verify_err:
        logging.error(f"Error verifying mlcube metadata: {verify_err}")
        logging.error(f"mlcube verification - FAILED!")
        raise click.Abort()
    logging.info('OK - VERIFIED')


@cli.command(name='pull', help='Pull MLCube from some remote location.')
@click.option('--mlcube', required=True, type=str, help='Location of a remote MLCube.')
@click.option('--branch', required=False, type=str, help='Branch name if URL is a GitHub url.')
def pull(mlcube: str, branch: Optional[str]) -> None:
    if not mlcube.startswith('https://github.com'):
        raise RuntimeError(f"Unsupported URL")

    branch = f"--branch {branch}" if branch else ""
    os.system(f"git clone {branch} {mlcube}")


@cli.command(name='describe', help='Describe this MLCube.')
@click.option('--mlcube', required=False, type=str, help='MLCube location.')
def describe(mlcube: Optional[str]) -> None:
    CompactMLCube(mlcube).unpack().mlcube_fs.describe()


@cli.command(name='configure', help='Configure environment for MLCube ML workload.')
@click.option('--mlcube', required=False, type=str, help='Path to MLCube directory.')
@click.option('--platform', required=False, type=str, help='Path to MLCube Platform definition file.')
def configure(mlcube: Optional[str], platform: Optional[str]):
    mlcube_fs = CompactMLCube(mlcube).unpack().mlcube_fs
    platform_path = mlcube_fs.get_platform_path(platform)
    runner = mlcube_fs.get_platform_runner(platform_path)
    os.system(f"{runner} configure --mlcube={mlcube_fs.root} --platform={platform_path}")


@cli.command(name='run', help='Run MLCube ML workload.',
             context_settings=dict(ignore_unknown_options=True, allow_extra_args=True))
@click.option('--mlcube', required=False, type=str, help='Path to MLCube directory.')
@click.option('--platform', required=False, type=str, help='Path to MLCube Platform definition file.')
@click.option('--task', required=False, type=str, help='Path to MLCube Task definition file.')
@click.pass_context
def run(ctx, mlcube: Optional[str], platform: Optional[str], task: Optional[str]):
    mlcube_fs = CompactMLCube(mlcube).unpack().mlcube_fs
    platform_path = mlcube_fs.get_platform_path(platform)
    task_path = mlcube_fs.get_task_instance_path(task)
    runner = mlcube_fs.get_platform_runner(platform_path)
    os.system(f"{runner} run --mlcube={mlcube_fs.root} --platform={platform_path} --task={task_path} "
              f"{' '.join(ctx.args)}")


if __name__ == "__main__":
    cli()
