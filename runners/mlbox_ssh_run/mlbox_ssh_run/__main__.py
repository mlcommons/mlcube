import os
import typer
from mlbox_ssh_run.ssh_run import SSHRun
from mlcommons_box import parse   # Do not remove (it registers schemas on import)
from mlcommons_box.common import mlbox_metadata
from mlbox_ssh_run import ssh_metadata


app = typer.Typer()


@app.command()
def configure(mlbox: str = typer.Option(...), platform: str = typer.Option(...)):
    mlbox: mlbox_metadata.MLBox = mlbox_metadata.MLBox(path=mlbox)
    mlbox.platform = ssh_metadata.Platform(platform, mlbox.qualified_name)
    print(mlbox)

    runner = SSHRun(mlbox)
    runner.configure()


@app.command()
def run(mlbox: str = typer.Option(...), platform: str = typer.Option(...), task: str = typer.Option(...)):
    mlbox: mlbox_metadata.MLBox = mlbox_metadata.MLBox(path=mlbox)
    mlbox.platform = ssh_metadata.Platform(platform, mlbox.qualified_name)
    mlbox.invoke = mlbox_metadata.MLBoxInvoke(task)
    mlbox.task = mlbox_metadata.MLBoxTask(os.path.join(mlbox.tasks_path, f'{mlbox.invoke.task_name}.yaml'))

    runner = SSHRun(mlbox)
    runner.run(task_file=task)


if __name__ == '__main__':
    app()
