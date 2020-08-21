import sys
from time import sleep
from pathlib import Path
import pprint
import logging

import typer
import click
from halo import Halo
import coloredlogs

from mlcommons_box.check import check_root_dir

app = typer.Typer()

@app.callback()
def callback(self, log_level: str = typer.Option("DEBUG", help="Logging level for the app.")):
    """
    Box 📦 is a packaging tool for ML models
    """
    logger = logging.getLogger(__name__)
    typer.echo(f"Log level is set to - {log_level}")
    coloredlogs.install(level=log_level)

@app.command()
@Halo(text="", spinner="dots")
def verify(self, path_to_box: str):
    """
    Verify Box metadata
    """
    logging.info("Starting Box metadata verification")
    metadata, verify_err = check_root_dir(
    Path(path_to_box).resolve().as_posix())

    if verify_err:
        logging.error(f"Error verifying Box metadata: {verify_err}")
        logging.error(f"Box verification - FAILED!")
        raise typer.Exit()

    logging.info('OK - VERIFIED')

if __name__ == "__main__":
    app()
