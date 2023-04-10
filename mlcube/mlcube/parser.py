"""Collection of classes to parse instantiate MLCube configuration from various sources.

- `MLCubeInstance`: Base class for various MLCube flavours (directory, archive ...).
- `MLCubeDirectory`: Class to work with directory-based MLCubes.
- `CliParser`: Helper utilities to parse command linea arguments.
"""
import abc
import os
import typing as t

from omegaconf import DictConfig, OmegaConf


class MLCubeInstance(abc.ABC):
    """Base class for different instantiations of MLCube (local, remote, directory, archive, container ...)."""

    @abc.abstractmethod
    def uri(self) -> str:
        """Return uniform resource identifier of this MLCube."""
        raise NotImplementedError


MLCubeInstanceType = t.TypeVar("MLCubeInstanceType", bound=MLCubeInstance)


class MLCubeDirectory(MLCubeInstance):
    """An MLCube instantiation as a local directory."""

    def __init__(self, path: t.Optional[str] = None) -> None:
        """Instantiate MLCube from mlcube.yaml file.

        Args:
            path: MLCube directory or path to mlcube.yaml. If None, current directory is used.
        """
        if path is None:
            path = os.getcwd()
        path = os.path.abspath(path)
        if os.path.isfile(path):
            self.path, self.file = os.path.split(path)
        else:
            self.path, self.file = os.path.abspath(path), "mlcube.yaml"

    def uri(self) -> str:
        return os.path.join(self.path, self.file)


class CliParser(object):
    """Helper utilities to parse command linea arguments."""

    @staticmethod
    def parse_mlcube_arg(mlcube: t.Optional[str]) -> MLCubeInstanceType:
        """Parse value of the `--mlcube` command line argument.

        Args:
            mlcube: Path to a MLCube directory or `mlcube.yaml` file. If it's a directory, standard name
                `mlcube.yaml` is assumed for MLCube definition file.
        Returns:
            One of child classes of MLCubeInstance that represents this MLCube.
        """
        return MLCubeDirectory(mlcube)

    @staticmethod
    def parse_list_arg(
        arg: t.Optional[str], default: t.Optional[str] = None
    ) -> t.List[str]:
        """Parse a string into list of strings using `,` as a separator.

        Args:
            arg: String if elements separated with `,`.
            default: Default value for `arg` if `arg` is None or empty.
        Returns:
            List of items.
        """
        arg = arg or default
        if not arg:
            return []
        return arg.split(",")

    @staticmethod
    def parse_extra_arg(
            unparsed_args: t.List[str], parsed_args: t.Dict[str, t.Optional[str]]
    ) -> t.Tuple[DictConfig, t.Dict]:
        """Parse extra arguments on a command line.

        These arguments correspond to:
            - MLCube runtime arguments. These start with `-P` prefix and are translated to a nested dictionaries
                structure using `.` as a separator. For instance, `-Pdocker.image=mlcommons/mnist:0.0.1` translates to
                python dictionary {'docker': {'image': 'mlcommons/mnist:0.0.1'}}.
            - Task arguments are all other arguments that do not star with `-P` or `--`. These arguments are
                input/output arguments of tasks.

        Args:
            unparsed_args: List of arguments that have not been parsed yet. These are parameters that are described
                above (MLCube runtime arguments and task arguments).
            parsed_args: CLI arguments that have already been parsed. These are all other CLI arguments that start with
                `--` prefix, and are normally parsed by libraries such as `click` or `argparse`. This dictionary will
                 also include such arguments as `--platform`, `--mlcube` and others. Keys in this dictionary are
                 argument names without `--` prefix. The following is the list of arguments this function can parse:
                    - `platform`: Platform to use to run this MLCube (docker, singularity, gcp, k8s etc).
                    - `network_option`: Networking options defined during MLCube container execution.
                    - `security_option`: Security options defined during MLCube container execution.
                    - `gpus_option`: GPU usage options defined during MLCube container execution.
                    - `memory_option`: Memory RAM options defined during MLCube container execution.
                    - `cpu_option`: CPU options defined during MLCube container execution.

        Returns:
            Tuple of two dictionaries: (mlcube_arguments, task_arguments).
        """
        # Parse unparsed arguments
        mlcube_args = OmegaConf.from_dotlist(
            [arg[2:] for arg in unparsed_args if arg.startswith("-P")]
        )

        task_args = [arg.split("=") for arg in unparsed_args if not arg.startswith("-P")]
        task_args = {arg[0]: arg[1] for arg in task_args}

        # Parse unparsed arguments
        platform: t.Optional[str] = parsed_args.get('platform', None)
        if platform in {'docker', 'singularity'}:
            runner_run_args = {}
            if parsed_args.get('network', None):
                runner_run_args["--network"] = parsed_args['network']
            if parsed_args.get('security', None):
                key = "--security-opt" if platform == "docker" else "--security"
                runner_run_args[key] = parsed_args['security']
            if parsed_args.get('gpus', None):
                if platform == "docker":
                    runner_run_args["--gpus"] = parsed_args['gpus']
                else:
                    runner_run_args["--nv"] = ""
                    os.environ['SINGULARITYENV_CUDA_VISIBLE_DEVICES'] = parsed_args['gpus']
            if parsed_args.get('memory', None):
                key = "--memory" if platform == "docker" else "--vm-ram"
                runner_run_args[key] = parsed_args['memory']
            if parsed_args.get('cpu', None):
                key = "--cpuset-cpus" if platform == "docker" else "--vm-cpu"
                runner_run_args[key] = parsed_args['cpu']

            mlcube_args.merge_with({platform: runner_run_args})

        return mlcube_args, task_args
