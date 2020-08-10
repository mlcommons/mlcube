import typer
from halo import Halo
from time import sleep

app = typer.Typer()


@app.callback()
def callback():
    """
    MLBox 📦 is a packaging tool for ML models
    """


@app.command()
def build():
    """
    Build a MLBox
    """
    spinner = Halo(text="Building MLBox", spinner="dots")
    spinner.start()
    sleep(5)
    spinner.stop()


@app.command()
def run():
    """
    Run a MLBox
    """
    spinner = Halo(text="Running MLBox", spinner="dots")
    spinner.start()
    sleep(5)
    spinner.stop()
