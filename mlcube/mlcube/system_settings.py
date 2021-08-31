import os
import logging
import typing as t
from pathlib import Path
from omegaconf import (OmegaConf, DictConfig)
from mlcube.errors import MLCubeError
from mlcube.platform import Platform
from mlcube.runner import Runner

logger = logging.getLogger(__name__)


class SystemSettings(object):

    @staticmethod
    def system_settings_file() -> t.Text:
        return os.path.abspath(os.environ.get('MLCUBE_SYSTEM_SETTINGS', Path.home() / 'mlcube.yaml'))

    def __init__(self, path: t.Optional[t.Text] = None) -> None:
        self.path: Path = Path(path if path is not None else SystemSettings.system_settings_file()).resolve()
        if not self.path.exists():
            logger.info("MLCube system settings file does not exist (%s).", str(self.path))
            self.path.touch()
        else:
            logger.info("MLCube system settings file exists (%s)", str(self.path))
        self.settings: DictConfig = OmegaConf.load(self.path)
        if not isinstance(self.settings, DictConfig):
            raise ValueError(f"Invalid object read from {self.path} (type = {type(self.settings)}). "
                             f"Expecting DictConfig.")

        updated = False
        for key in ('runners', 'platforms', 'storage'):
            if key not in self.settings:
                updated = True
                self.settings[key] = {}
        if updated:
            self.save()

    @property
    def runners(self) -> DictConfig:
        return self.settings.runners

    @property
    def platforms(self) -> DictConfig:
        return self.settings.platforms

    @property
    def storage(self) -> DictConfig:
        return self.settings.storage

    def save(self, resolve: bool = False) -> 'SystemSettings':
        OmegaConf.save(self.settings, self.path, resolve=resolve)
        return self

    def update_installed_runners(self) -> 'SystemSettings':
        installed_runners: t.Dict = Platform.get_installed_runners()
        updated: bool = False
        for platform_name, platform_spec in installed_runners.items():
            if platform_name not in self.settings.runners:
                updated = True
                self.settings.runners[platform_name] = platform_spec['config']
            if platform_name not in self.settings.platforms:
                updated = True
                self.settings.platforms[platform_name] = platform_spec['runner_cls'].CONFIG.DEFAULT
        if updated:
            self.save()
        return self

    def get_platform(self, platform: t.Optional[t.Text] = None) -> DictConfig:
        if not platform:
            return OmegaConf.create({})
        return self.settings.platforms.get(platform, OmegaConf.create({}))

    def create_platform(self, args: t.Optional[t.Tuple[t.Text, t.Text]] = None) -> 'SystemSettings':
        if args is None:
            return self
        runner, platform = args
        if platform in self.settings.platforms:
            raise MLCubeError(f"Platform ({platform}) already exists ({self.settings.platforms[platform]}).")
        if runner not in self.settings.runners:
            raise MLCubeError(f"Unknown runner ({runner}). Installed runners = {str(self.settings.runners.keys())}")
        runner_cls: t.Type[Runner] = Platform.get_runner(self.runners.get(runner, None))
        self.settings.platforms[platform] = runner_cls.CONFIG.DEFAULT
        self.save()
        return self

    def remove_platform(self, platform: t.Optional[t.Text] = None) -> 'SystemSettings':
        if platform and platform in self.settings.platforms:
            del self.settings.platforms[platform]
            self.save()
        return self

    def copy_platform(self, args: t.Optional[t.Tuple[t.Text, t.Text]] = None,
                      delete_source: bool = False) -> 'SystemSettings':
        if args is None:
            return self
        old_name, new_name = args
        if old_name not in self.settings.platforms:
            raise MLCubeError(f"Platform ({old_name}) does not exist.")
        if new_name in self.settings.platforms:
            raise MLCubeError(f"Platform ({new_name}) already exists ({self.settings.platforms[new_name]}).")
        self.settings.platforms[new_name] = self.settings.platforms[old_name]
        if delete_source:
            del self.settings.platforms[old_name]
        self.save()
        return self

    def rename_runner(self, args: t.Optional[t.Tuple[t.Text, t.Text]] = None,
                      update_platforms: bool = False) -> 'SystemSettings':
        if args is None:
            return self
        old_name, new_name = args
        if old_name not in self.settings.runners:
            raise MLCubeError(f"Runner ({old_name}) does not exist.")
        if new_name in self.settings.runners:
            raise MLCubeError(f"Runner ({new_name}) already exists ({self.settings.runners[new_name]}).")

        for platform_name, platform_def in self.settings.platforms:
            if platform_def.runner == old_name:
                if not update_platforms:
                    raise MLCubeError(
                        f"Cannot rename runner ({old_name}). Some platforms reference this runner, and need to "
                        "be updated, but update_platforms is false (if you are running an mlcube from CLI, "
                        "provide `--update-platforms` switch)."
                    )
                platform_def.runner = new_name

        self.settings.runners[new_name] = self.settings.runners[old_name]
        del self.settings.runners[old_name]
        self.save()
        return self

    def remove_runner(self, runner: t.Optional[t.Text] = None, remove_platforms: bool = False) -> 'SystemSettings':
        if not runner or runner not in self.settings.runners:
            return self

        platforms = [p for p in self.settings.platforms if self.settings.platforms[p].runner == runner]
        if platforms and not remove_platforms:
            raise MLCubeError(
                f"Cannot remove runner ({runner}). Some platforms reference this runner, and need to "
                "be removed, but remove_platforms is false (if you are running an mlcube from CLI, "
                "provide `--remove-platforms` switch)."
            )
        for platform in platforms:
            del self.settings.platforms[platform]
        del self.settings.runners[runner]
        self.save()
        return self
