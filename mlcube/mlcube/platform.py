import pkgutil
import logging
import importlib
import typing as t
from omegaconf import DictConfig
from mlcube.runner import Runner

logger = logging.getLogger(__name__)

__all__ = ['Platform']


class Platform(object):
    reference_runners = {
        'docker': dict(pkg='mlcube_docker'),
        'singularity': dict(pkg='mlcube_singularity'),
        'ssh': dict(pkg='mlcube_ssh'),
        'gcp': dict(pkg='mlcube_gcp'),
        'k8s': dict(pkg='mlcube_k8s'),
        'kubeflow': dict(pkg='mlcube_kubeflow'),
    }

    @staticmethod
    def get_installed_runners() -> t.Dict:
        candidate_runners = {
            name: importlib.import_module(name) for _, name, _ in pkgutil.iter_modules() if name.startswith('mlcube_')
        }
        installed_runners = {}
        for pkg_name, module in candidate_runners.items():
            try:
                get_runner_class: t.Callable = getattr(module, 'get_runner_class')
                runner_cls: t.Type[Runner] = get_runner_class()
                if not issubclass(runner_cls, Runner):
                    raise TypeError(f"Invalid type of a runner ({runner_cls}). Expecting subclass of {Runner}.")
                runner_name = runner_cls.CONFIG.DEFAULT.runner
                installed_runners[runner_name] = dict(config=dict(pkg=pkg_name), runner_cls=runner_cls)
                logger.info("Found installed MLCube runner: platform=%s, pkg=%s", runner_name, pkg_name)
            except (AttributeError, TypeError) as e:
                logger.warning("Package (%s) is not a valid MLCube runner. Error = \"%s\"", pkg_name, str(e))
        return installed_runners

    @staticmethod
    def get_runner(runner_config: t.Optional[DictConfig]) -> t.Type[Runner]:
        if not runner_config:
            raise RuntimeError("Can't create runner. Runner config is null or empty.")
        if 'pkg' not in runner_config:
            raise RuntimeError(f"Do not know how to instantiate a runner. Runner config={str(runner_config)}")
        module = importlib.import_module(runner_config.pkg)
        get_runner_class: t.Callable = getattr(module, 'get_runner_class')
        return get_runner_class()
