import os
import typer
from mlcommons_box import parse   # Do not remove (it registers schemas on import)
from mlcommons_box.common import mlbox_metadata
from mlbox_docker_run import metadata
from mlbox_docker_run.docker_run import DockerRun


app = typer.Typer()


@app.command()
def configure(mlbox: str = typer.Option(...), platform: str = typer.Option(...)):
    mlbox: mlbox_metadata.MLBox = mlbox_metadata.MLBox(path=mlbox)
    mlbox.platform = metadata.DockerPlatform(path=platform)
    print(mlbox)

    runner = DockerRun(mlbox)
    runner.configure()


@app.command()
def run(mlbox: str = typer.Option(...), platform: str = typer.Option(...), task: str = typer.Option(...)):
    mlbox: mlbox_metadata.MLBox = mlbox_metadata.MLBox(path=mlbox)
    mlbox.platform = metadata.DockerPlatform(path=platform)
    mlbox.invoke = mlbox_metadata.MLBoxInvoke(task)
    mlbox.task = mlbox_metadata.MLBoxTask(os.path.join(mlbox.tasks_path, f'{mlbox.invoke.task_name}.yaml'))
    print(mlbox)

    runner = DockerRun(mlbox)
    runner.run()


if __name__ == '__main__':
    app()
