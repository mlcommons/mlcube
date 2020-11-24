import os
from typing import Optional
from mlcube.commands import CommandUtils
from mlcube.common import mlcube_metadata


class InspectCommand(object):
    def __init__(self, mlcube: Optional[str]) -> None:
        self.mlcube: str = CommandUtils.get_mlcube_path(mlcube)

    def execute(self) -> None:
        mlcube: mlcube_metadata.MLCube = mlcube_metadata.MLCube(path=self.mlcube)
        print(f"MLCube local path: {mlcube.root}")
        print(f"Name: {mlcube.name}")
        print(f"Version: {mlcube.version}")

        print("Tasks:")
        run_files = mlcube.get_files('run', recursive=True)
        for run_file in run_files:
            invoke = mlcube_metadata.MLCubeInvoke(run_file)
            task = mlcube_metadata.MLCubeTask(os.path.join(mlcube.root, 'tasks', f'{invoke.task_name}.yaml'))
            print(f"  Task = {invoke.task_name}")
            print("    Inputs:")
            for input_name, input_type in task.inputs.items():
                print(f"      {input_name}: {input_type} = {invoke.input_binding[input_name]}")
            print("    Outputs:")
            for output_name, output_type in task.outputs.items():
                print(f"      {output_name}: {output_type} = {invoke.output_binding[output_name]}")
        print("Platforms:")
        platforms = mlcube.get_files('platforms', recursive=True)
        for platform in platforms:
            print(f"  {os.path.relpath(platform, mlcube.root)}")
