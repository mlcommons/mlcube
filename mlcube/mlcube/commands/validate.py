import os
from typing import Optional
from mlcube.commands import CommandUtils
from mlcube.common import mlcube_metadata


class ValidateCommand(object):
    def __init__(self, mlcube: Optional[str]) -> None:
        self.mlcube: str = CommandUtils.get_mlcube_path(mlcube)

    def execute(self) -> None:
        # See if we can load the mlcube definition file.
        mlcube: mlcube_metadata.MLCube = mlcube_metadata.MLCube(path=self.mlcube)
        # Get all run configurations recursively.
        run_files = mlcube.get_files('run', recursive=True)
        if len(run_files) == 0:
            raise ValueError(f"No run configurations found for {mlcube.root}")
        # Load run configuration and associated task.
        for run_file in run_files:
            invoke = mlcube_metadata.MLCubeInvoke(run_file)
            _ = mlcube_metadata.MLCubeTask(os.path.join(mlcube.root, 'tasks', f'{invoke.task_name}.yaml'))
        # Load all platform configs recursively.
        platforms = mlcube.get_files('platforms', recursive=True)
        if len(platforms) == 0:
            raise ValueError(f"No platform configurations found for {mlcube.root}")

        print(f"MLCube ({mlcube.root}) has been validated")
