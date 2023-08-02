"""Helper utilities to work with runner configurations (==platforms).

- `Platform`: Class to manage reference Python-based MLCube runners.
"""
import importlib
import logging
import pkgutil
import typing as t
from types import ModuleType

from omegaconf import DictConfig

from mlcube.runner import Runner

logger = logging.getLogger(__name__)

__all__ = ["Platform"]


class Platform(object):
    """Class to manage reference Python-based MLCube runners."""

    @staticmethod
    def get_package_info(package: ModuleType) -> t.Dict:
        """Return information about the Python package"""
        info = {"name": package.__name__, "location": package.__file__}
        try:
            from importlib.metadata import version

            info["version"] = version(info["name"])
        except:
            pass
        return info

    @staticmethod
    def get_installed_runners() -> t.Dict[str, t.Dict]:
        """Find all installed Python-based MLCube runners.

        Returns:
            Dictionary mapping runner names to their Python package details. The schema for dictionary values is the
                following:
                ```yaml
                config:
                    pkg: PYTHON_PACKAGE_NAME
                runner_cls: PYTHON_RUNNER_CLASS
                ```

        Installed runners are found by inspecting Python packages. MLCube system settings file is not used.
        """
        installed_runners = {}
        for _, pkg_name, _ in pkgutil.iter_modules():
            if not pkg_name.startswith("mlcube_"):
                continue
            module_info: t.Optional[t.Dict] = None
            try:
                module = importlib.import_module(pkg_name)
                module_info = Platform.get_package_info(module)
                runner_cls: t.Type[Runner] = module.get_runner_class()
                if not issubclass(runner_cls, Runner):
                    raise TypeError(
                        f"Invalid runner type (expected: {Runner}, actual: {runner_cls})."
                    )
                runner_name = runner_cls.CONFIG.DEFAULT.runner
                installed_runners[runner_name] = {
                    "config": {"pkg": pkg_name},
                    "runner_cls": runner_cls,
                }
                logger.info(
                    "Platform.get_installed_runners found installed MLCube runner (platform=%s, pkg=%s, info=%s)",
                    runner_name,
                    pkg_name,
                    module_info,
                )
            except (ImportError, AttributeError, TypeError) as e:
                logger.warning(
                    "Platform.get_installed_runners package (pkg_name=%s, info=%s) is not a valid MLCube runner. "
                    'Error="%s".',
                    pkg_name,
                    module_info,
                    str(e),
                )
        return installed_runners

    @staticmethod
    def get_runner(runner_config: t.Optional[DictConfig]) -> t.Type[Runner]:
        """Return runner class.

        Args:
            runner_config: Dictionary containing `pkg` field with the runner's Python package name.
        Returns:
            Runner class.
        """
        if not runner_config:
            raise RuntimeError("Can't create runner. Runner config is null or empty.")
        if "pkg" not in runner_config:
            raise RuntimeError(
                f"Do not know how to instantiate a runner. Runner config={str(runner_config)}"
            )
        module = importlib.import_module(runner_config.pkg)
        get_runner_class: t.Optional[t.Callable] = getattr(
            module, "get_runner_class", None
        )
        if get_runner_class is None:
            raise RuntimeError(
                f"Imported module ({runner_config.pkg}) does not provide runner class function (get_runner_class)."
            )
        return get_runner_class()
