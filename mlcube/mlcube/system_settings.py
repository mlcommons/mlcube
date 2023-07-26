"""Classes to work with MLCube system settings file.

# Introduction
MLCube system settings file provides user-level configuration for MLCube runners. This configuration is used by
these runners to run all MLCubes on a user local machine.

The default location of this file is `${HOME}/mlcube.yaml`, but can be overridden with `MLCUBE_SYSTEM_SETTINGS`
environment variable. This file is automatically created on the first run, and is (possibly) automatically updated
each time users interact with MLCube runtime (i.e., execute `mlcube` on a command line).

This file can be edited manually. MLCube CLI implements `config` command to interact with this file. For more details,
execute the following command: `mlcube config --help`.

# Terminology
- `system settings file`: YAML file that provides various configurations for MLCube runners on a particular machine.
- `runner`: MLCuber runner (docker, singularity etc.). Each runner has its own default configuration.
- `runners`: System settings configuration section that provides information about installed MLCube runners. Reference
  Python-based MLCube runners (implemented in this project) are detected automatically. It's a list if `runner`
  descriptions.
- `platform`: An instance of configured `runner`. Each runner has a default configuration, and when MLCube runtime
  detects new runner, it updates the `runners` section, and adds a new entry to the `platforms` section (see below).
  When users run MLCubes on a command line, they can provide `--platform` argument. This argument refers to this
  `platform` term. Summary: each `runner` (identifies by a name) always has a default `platform` with the same name.
- `platforms: System settings configuration section that provides various pre-configured runners. As it was mentioned
  above, a pre-configured `runner` instance is called `platform`. Why do we want to have multiple platforms?
    - Users can have multiple MLCube runners: docker runner, singularity runner etc.
    - Users may want to have multiple pre-configured instances of the same runner. This may be required due to multiple
      reasons. For instance, users can have multiple SSH configurations that they use to run MLCubes on different remote
      machines. Or maybe users have different docker runners, one configured to use all available RAM, and the other
      configured to use only a limited RAM, e.g., 64 GB (for benchmarking purposes)

# Classes implemented in this module:
- `SystemSettings`: Class that implements various operations associated with the MLCube system settings file.
"""
import logging
import os
import typing as t
from pathlib import Path

from mlcube.errors import MLCubeError
from mlcube.platform import Platform
from mlcube.runner import Runner

from omegaconf import (DictConfig, OmegaConf)

__all__ = ['SystemSettings']

logger = logging.getLogger(__name__)


class SystemSettings(object):
    """Class to work with MLCube system settings file."""

    @staticmethod
    def system_settings_file() -> str:
        """Return full path to MLCube system settings file."""
        return os.path.abspath(os.environ.get('MLCUBE_SYSTEM_SETTINGS', Path.home() / 'mlcube.yaml'))

    def __init__(self, path: t.Optional[str] = None) -> None:
        """Initialize system settings file class.

        Args:
            path: If not None, path to system file. If None, default path is used.
        """
        self.path: Path = Path(path if path is not None else SystemSettings.system_settings_file()).resolve()
        if not self.path.exists():
            logger.info(
                "SystemSettings.__init__ MLCube system settings file does not exist (%s).", self.path.as_posix()
            )
            self.path.touch()
        else:
            logger.info("SystemSettings.__init__ MLCube system settings file exists (%s)", self.path.as_posix())
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
        """Return `runners` configuration section."""
        return self.settings.runners

    @property
    def platforms(self) -> DictConfig:
        """Return `platforms` configuration section."""
        return self.settings.platforms

    @property
    def storage(self) -> DictConfig:
        """Return `storage` configuration section."""
        return self.settings.storage

    def save(self, resolve: bool = False) -> 'SystemSettings':
        """Serialize system settings.

        Args:
            resolve: If True, resolve all values in system settings file. MLCube uses `omegaconf` library, and MLCube
                relies on its capability to define values by referencing other parameters.
        """
        OmegaConf.save(self.settings, self.path, resolve=resolve)
        return self

    def update_installed_runners(self) -> 'SystemSettings':
        """Check if new MLCube runners have been installed and update systems settings file."""
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

    def get_platform(self, platform: t.Optional[str] = None) -> DictConfig:
        """Return platform configuration associated with the given name.

        Args:
            platform: Platform name.
        """
        if not platform:
            return OmegaConf.create({})
        return self.settings.platforms.get(platform, OmegaConf.create({}))

    def create_platform(self, args: t.Optional[t.Tuple[str, str]] = None) -> 'SystemSettings':
        """Create a new platform for the given runner.

        Args:
            args: Tuple of runner (runner name: str), platform (platform name: str).
        """
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

    def remove_platform(self, platform: t.Optional[str] = None) -> 'SystemSettings':
        """Remove corresponding `platform` and update system settings file.

        Args:
            platform: Platform name.
        """
        if platform and platform in self.settings.platforms:
            del self.settings.platforms[platform]
            self.save()
        return self

    def copy_platform(self, args: t.Optional[t.Tuple[str, str]] = None,
                      delete_source: bool = False) -> 'SystemSettings':
        """Clone existing platform.

        Args:
            args: Tuple of existing platform (name), new platform (name).
            delete_source: If True, remove source (existing) platform.
        """
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

    def rename_runner(self, args: t.Optional[t.Tuple[str, str]] = None,
                      update_platforms: bool = False) -> 'SystemSettings':
        """Rename existing runner.

        Args:
            args: Tuple of existing runner (name), new runner (name).
            update_platforms: If True, update existing platforms. If there are platforms associated with the
                existing runner, and update_platforms is False, exception is raised.
        """
        if args is None:
            return self
        old_name, new_name = args
        if old_name not in self.settings.runners:
            raise MLCubeError(f"Runner ({old_name}) does not exist.")
        if new_name in self.settings.runners:
            raise MLCubeError(f"Runner ({new_name}) already exists ({self.settings.runners[new_name]}).")

        for _platform_name, platform_def in self.settings.platforms:
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

    def remove_runner(self, runner: t.Optional[str] = None, remove_platforms: bool = False) -> 'SystemSettings':
        """Remove existing runner.

        Args:
            runner: Runner name.
            remove_platforms: If True, also remove associated platforms. If False, and such platforms exists, an
                exception is raised.
        """
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
