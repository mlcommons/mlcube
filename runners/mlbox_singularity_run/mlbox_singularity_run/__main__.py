import os
import typer
from mlbox_singularity_run.singularity_run import SingularityRun
from mlcommons_box import parse   # Do not remove (it registers schemas on import)
from mlcommons_box.common import mlbox_metadata
from mlbox_singularity_run import metadata


metadata.MLSchemaRegistrar.register()
app = typer.Typer()


@app.command()
def configure(mlbox: str = typer.Option(...), platform: str = typer.Option(...)):
    mlbox: mlbox_metadata.MLBox = mlbox_metadata.MLBox(path=mlbox)
    mlbox.platform = metadata.SingularityPlatform(path=platform)
    print(mlbox)

    runner = SingularityRun(mlbox)
    runner.configure()


@app.command()
def run(mlbox: str = typer.Option(...), platform: str = typer.Option(...), task: str = typer.Option(...)):
    mlbox: mlbox_metadata.MLBox = mlbox_metadata.MLBox(path=mlbox)
    mlbox.platform = metadata.SingularityPlatform(path=platform)
    mlbox.invoke = mlbox_metadata.MLBoxInvoke(task)
    mlbox.task = mlbox_metadata.MLBoxTask(os.path.join(mlbox.tasks_path, f'{mlbox.invoke.task_name}.yaml'))
    print(mlbox)

    runner = SingularityRun(mlbox)
    runner.run()


if __name__ == '__main__':
    app()
