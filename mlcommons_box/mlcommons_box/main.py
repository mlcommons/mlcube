import sys
from time import sleep
from pathlib import Path
import pprint
import logging

import click
from halo import Halo
import coloredlogs

from mlcommons_box.check import check_root_dir

@click.group(name='mlcommons_box')
@click.option('--log-level', default="DEBUG", help="Log level for the app.")
def cli(log_level: str):
    """
    Box 📦 is a packaging tool for ML models
    """
    logger = logging.getLogger(__name__)
    click.echo(f"Log level is set to - {log_level}")
    coloredlogs.install(level=log_level)

@cli.command()
@click.argument('path_to_box')
@Halo(text="", spinner="dots")
def verify(path_to_box: str):
    """
    Verify Box metadata
    """
    logging.info("Starting Box metadata verification")
    metadata, verify_err = check_root_dir(
    Path(path_to_box).resolve().as_posix())

    if verify_err:
        logging.error(f"Error verifying Box metadata: {verify_err}")
        logging.error(f"Box verification - FAILED!")
        raise click.Abort()

    logging.info('OK - VERIFIED')

if __name__ == "__main__":
    cli()
