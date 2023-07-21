"""Helper utilities to work with runner configurations (==platforms).

- `Platform`: Class to manage reference Python-based MLCube runners.
"""
import importlib
import logging
import pkgutil
import typing as t

from mlcube.runner import Runner

from omegaconf import DictConfig


logger = logging.getLogger(__name__)

__all__ = ['Platform']


class Platform(object):
    """Class to manage reference Python-based MLCube runners."""

    reference_runners = {
        'docker': {'pkg': 'mlcube_docker'},
        'singularity': {'pkg': 'mlcube_singularity'},
        'ssh': {'pkg': 'mlcube_ssh'},
        'gcp': {'pkg': 'mlcube_gcp'},
        'k8s': {'pkg': 'mlcube_k8s'},
        'kubeflow': {'pkg': 'mlcube_kubeflow'},
    }

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
        candidate_runners = {
            name: importlib.import_module(name) for _, name, _ in pkgutil.iter_modules() if name.startswith('mlcube_')
        }
        installed_runners = {}
        for pkg_name, module in candidate_runners.items():
            try:
                get_runner_class: t.Optional[t.Callable] = getattr(module, 'get_runner_class', None)
                if get_runner_class is None:
                    logger.warning(
                        "Platform.get_installed_runners candidate MLCube runner package (%s) does not provide runner "
                        "class function (get_runner_class).", pkg_name
                    )
                    continue
                runner_cls: t.Type[Runner] = get_runner_class()
                if not issubclass(runner_cls, Runner):
                    raise TypeError(f"Invalid type of a runner ({runner_cls}). Expecting subclass of {Runner}.")
                runner_name = runner_cls.CONFIG.DEFAULT.runner
                installed_runners[runner_name] = {'config': {'pkg': pkg_name}, 'runner_cls': runner_cls}
                logger.info(
                    "Platform.get_installed_runners found installed MLCube runner: platform=%s, pkg=%s",
                    runner_name, pkg_name
                )
            except (AttributeError, TypeError) as e:
                logger.warning(
                    "Platform.get_installed_runners package (%s) is not a valid MLCube runner. Error=\"%s\"",
                    pkg_name, str(e)
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
        if 'pkg' not in runner_config:
            raise RuntimeError(f"Do not know how to instantiate a runner. Runner config={str(runner_config)}")
        module = importlib.import_module(runner_config.pkg)
        get_runner_class: t.Optional[t.Callable] = getattr(module, 'get_runner_class', None)
        if get_runner_class is None:
            raise RuntimeError(
                f"Imported module ({runner_config.pkg}) does not provide runner class function (get_runner_class)."
            )
        return get_runner_class()
