from typing import Optional
from mlcube.commands import CommandUtils


class ConfigureCommand(object):
    def __init__(self, mlcube: Optional[str], platform: Optional[str]) -> None:
        self.mlcube: str = CommandUtils.get_mlcube_path(mlcube)
        self.platform = CommandUtils.get_file(self.mlcube, 'platforms', platform)

    def execute(self) -> None:
        configure, _ = CommandUtils.load_mlcube_runner(self.platform)
        configure(self.mlcube, self.platform)
