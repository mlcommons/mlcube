import click
import logging
import coloredlogs
from halo import Halo
from pathlib import Path
from mlcube.check import check_root_dir


@click.group(name='mlcube')
@click.option('--log-level', default="INFO", help="Log level for the app.")
def cli(log_level: str):
    """
    MLCube 📦 is a packaging tool for ML models
    """
    logger = logging.getLogger(__name__)
    click.echo(f"Log level is set to - {log_level}")
    coloredlogs.install(level=log_level)


@cli.command()
@click.argument('path_to_mlcube')
@Halo(text="", spinner="dots")
def verify(path_to_mlcube: str):
    """
    Verify MLCube metadata
    """
    logging.info("Starting mlcube metadata verification")
    metadata, verify_err = check_root_dir(Path(path_to_mlcube).resolve().as_posix())

    if verify_err:
        logging.error(f"Error verifying mlcube metadata: {verify_err}")
        logging.error(f"mlcube verification - FAILED!")
        raise click.Abort()

    logging.info('OK - VERIFIED')


@cli.command(name='configure', help='Configure MLCube.')
@click.option('--mlcube', required=False, help='MLCube root directory.')
@click.option('--platform', required=False, help='MLCube Platform definition file.')
def configure_cli(mlcube: str, platform: str):
    from mlcube.commands.configure import ConfigureCommand
    ConfigureCommand(mlcube, platform).execute()


@cli.command(name='run', help='Run MLCube ML workload in the docker environment.')
@click.option('--mlcube', required=False, help='MLCube root directory.')
@click.option('--platform', required=False, help='MLCube Platform definition file.')
@click.option('--task', required=False, help='MLCube Task definition file.')
def run_cli(mlcube: str, platform: str, task: str):
    from mlcube.commands.run import RunCommand
    RunCommand(mlcube, platform, task).execute()


@cli.command(name='inspect', help='Report details of this MLCube.')
@click.option('--mlcube', required=False, help='MLCube root directory.')
def inspect_cli(mlcube: str):
    from mlcube.commands.inspect import InspectCommand
    InspectCommand(mlcube).execute()


@cli.command(name='validate', help='Validate directory-based MLCube.')
@click.option('--mlcube', required=False, help='MLCube root directory.')
def validate_cli(mlcube: str):
    from mlcube.commands.validate import ValidateCommand
    ValidateCommand(mlcube).execute()


@cli.command(name='fetch', help='Fetch MLCube from a remote location.',
             context_settings=dict(ignore_unknown_options=True, allow_extra_args=True,))
@click.option('--mlcube', required=False, help='MLCube path identifier.')
@click.pass_context
def fetch_cli(ctx: click.core.Context, mlcube: str):
    # ctx.args: List of unparsed options (--name=value).
    from mlcube.commands.fetch import FetchCommand
    FetchCommand(mlcube, ctx.args).execute()


if __name__ == "__main__":
    cli()
