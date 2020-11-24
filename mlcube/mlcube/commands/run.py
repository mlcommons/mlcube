from typing import Optional
from mlcube.commands import CommandUtils


class RunCommand(object):
    def __init__(self, mlcube: Optional[str], platform: Optional[str], task: str) -> None:
        self.mlcube: str = CommandUtils.get_mlcube_path(mlcube)
        self.platform = CommandUtils.get_file(self.mlcube, 'platforms', platform)
        self.task = CommandUtils.get_file(self.mlcube, 'run', task)

    def execute(self) -> None:
        _, run = CommandUtils.load_mlcube_runner(self.platform)
        run(self.mlcube, self.platform, self.task)
