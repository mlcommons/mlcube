"""Collection of classes to parse instantiate MLCube configuration from various sources.

- `MLCubeInstance`: Base class for various MLCube flavours (directory, archive ...).
- `MLCubeDirectory`: Class to work with directory-based MLCubes.
- `CliParser`: Helper utilities to parse command linea arguments.
"""
import abc
import logging
import os
import typing as t
from dataclasses import dataclass

from omegaconf import DictConfig, OmegaConf

from mlcube.errors import ConfigurationError

logger = logging.getLogger(__name__)


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


class DeviceSpecs:
    """GPU specifications."""
    @dataclass
    class Device:
        index: t.Optional[int] = None     # GPU index in a system (depends on ordering - see `CUDA_DEVICE_ORDER`).
        uuid: t.Optional[str] = None      # always unique, e.g., GPU-1f22a253-c329-dfb7-0db4-e005efb6a4c7.

        @classmethod
        def create(cls, device: str) -> "DeviceSpecs.Device":
            device = device.strip()
            try:
                return cls(index=int(device))
            except ValueError:
                return cls(uuid=device)

        def str_spec(self) -> str:
            return str(self.index) if self.index is not None else self.uuid

        def __str__(self) -> str:
            return f"Device(index={self.index}, uuid={self.uuid})"

    @dataclass
    class DockerSpecs:
        gpus: t.Optional[str] = None
        cuda_visible_devices: t.Optional[str] = None

    def __init__(self) -> None:
        """Init GPU specs so that it's none by default.

        The values are set in factory methods. Only one instance variable out of 4 must be set.
        """
        self._none: bool = True
        """No GPUs requested - use this to check if GPUs have not been requested."""
        self._all: bool = False
        """All GPUs requested (--gpus=all)."""
        self._num_devices: t.Optional[int] = None  # Just number of GPUs
        """Some number of GPUs requested (--gpus=2 for 2 (first) GPUs) - this either None or positive, never zero."""
        self._devices: t.Optional[t.List[DeviceSpecs.Device]] = None
        """List of GPU indices or IDs (--gpus=1,2 or --gpus=GPU-f234r2f23) - either None or at least one device."""

    @property
    def none(self) -> bool:
        return self._none

    @property
    def all(self) -> bool:
        return self._all

    @property
    def num_devices(self) -> t.Optional[int]:
        return self._num_devices

    @property
    def devices(self) -> t.Optional[t.List["DeviceSpecs.Device"]]:
        return self._devices if self._devices is None else self._devices.copy()

    def check_with_platform_specs(self, accelerator_count: t.Optional[int] = None) -> None:
        if accelerator_count is None:
            # Number of accelerators is not specified in the MLCube configuration file. We assume this is really
            # optional now, so will not be doing any further checks.
            return
        if accelerator_count < 0:
            # This should generally never happen here since MLCube needs to validate values before this method is
            # called (what is normally should happen right before MLCube runs the MLCube project).
            return
        if accelerator_count == 0:
            # The accelerator count value has been set to 0
            if self.none:
                logger.info(
                    "`platform.accelerator_count = 0` is consistent with device specs (%s).", str(self)
                )
                return
            logger.warning(
                "`platform.accelerator_count = 0` is not consistent with device specs (%s).", str(self)
            )
        # Some number of accelerators has been specified
        if (
                self.all is True or
                self.num_devices is not None and self.num_devices == accelerator_count or
                self._devices is not None and len(self._devices) == accelerator_count
        ):
            logger.info(
                "`platform.accelerator_count = %d` is probably consistent with device specs (%s).",
                accelerator_count, str(self)
            )
        logger.warning(
            "`platform.accelerator_count = %d` is not consistent with device specs (%s).",
            accelerator_count, str(self)
        )

    def get_docker_specs(self) -> "DeviceSpecs.DockerSpecs":
        if self.none:
            # Do not provide --gpus flag
            return DeviceSpecs.DockerSpecs()
        if self.all:
            # provide --gpus=all, do not know yet how to compute total number of devices
            logger.warning(
                "Device docker specs: identifying CUDA_VISIBLE_DEVICES when gpus = 'all' is not supported yet."
            )
            return DeviceSpecs.DockerSpecs(gpus="all")
        if self.num_devices is not None:
            # --gpus=N, CUDA_VISIBLE_DEVICES=0,1,2,..N-1
            return DeviceSpecs.DockerSpecs(
                gpus=f"{self.num_devices}",
                cuda_visible_devices=",".join(str(i) for i in range(self.num_devices))
            )
        # --gpus=device=A,B,C, CUDA_VISIBLE_DEVICES=0,1,2,..N-1
        assert isinstance(self._devices, list) and len(self._devices) > 0
        return DeviceSpecs.DockerSpecs(
            gpus="device=" + ",".join(dev.str_spec() for dev in self._devices),
            cuda_visible_devices=",".join(str(i) for i in range(len(self._devices)))
        )

    @classmethod
    def from_string(cls, gpus: t.Optional[str] = None) -> "DeviceSpecs":
        _gpus = str(gpus)
        gpus = (gpus or "").strip()

        # No GPUs requested
        if not gpus:
            logger.debug("Device specs (`%s`) resolved to `none`.", _gpus)
            return DeviceSpecs()

        # Exposes all available GPUs (e.g., 8). To set CUDA_VISIBLE_DEVICES, MLCube needs to identify the number of
        # available GPUs. The NVIDIA_VISIBLE_DEVICES=all will be set automatically by docker.
        if gpus == "all":
            logger.debug("Device specs (`%s`) resolved to `all`.", _gpus)
            gpu_specs = DeviceSpecs()
            gpu_specs._none = False
            gpu_specs._all = True
            return gpu_specs

        # Exposes "first" N GPUs. CUDA_VISIBLE_DEVICES is set to list(0, range(N)). The NVIDIA_VISIBLE_DEVICES will be
        # set automatically (in this case, it seems like these two environment variables will have the same value).
        try:
            num_gpus = int(gpus)
            if num_gpus <= 0:
                logger.debug("Device spec (`%s`) resolved to `none`.", _gpus)
                return DeviceSpecs()
            logger.debug("Device spec (`%s`) resolved to device count (num_devices=%d)", _gpus, num_gpus)
            gpu_specs = DeviceSpecs()
            gpu_specs._none = False
            gpu_specs._num_devices = num_gpus
            return gpu_specs
        except ValueError:
            ...

        if gpus.startswith("device="):
            _devices = [
                device for device in (
                    device.strip() for device in gpus[7:].split(",")
                ) if device
            ]
            if not _devices:
                logger.debug("Device spec (`%s`) resolved to `none`.", _gpus)
                return DeviceSpecs()

            logger.debug("Device spec (`%s`) resolved to device list (devices=%s).", _gpus, _devices)
            gpu_specs = DeviceSpecs()
            gpu_specs._none = False
            gpu_specs._devices = [DeviceSpecs.Device.create(device) for device in _devices]
            return gpu_specs

        # Do not know how to parse
        raise ConfigurationError(
            f"The `gpus` configuration parameter has invalid or unsupported value (gpus=`{gpus}`). It can take one"
            "of the following values: (1) empty or not specified, (2) 'all', (3) be single integer value or (4) "
            "be a string that starts with 'device=' that is followed by a comma-separated list of integers or device "
            "IDs (strings). For more details, see "
            "https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/docker-specialized.html."
        )

    @classmethod
    def from_config(cls, accelerator_count: t.Optional[int] = None, gpus: t.Optional[str] = None) -> "DeviceSpecs":
        """Probably a temporary workaround to infer device specs based upon platform section and CLI's --gpus arg."""

        # Determine initial device specs. The `accelerator_count` is part of the MLCube's `platform` section that
        # defines (optionally) number of GPUs required by an MLCube. If not set, specs set to none (not needed).
        if accelerator_count is not None and accelerator_count > 0:
            platform_device_specs = DeviceSpecs.from_string(str(accelerator_count))
        else:
            platform_device_specs = DeviceSpecs()

        # The `gpus` arg is none when it's not provided by a user. We need to differentiate between not set (None) and
        # empty (e.g., --gpus="") what means disable GPUs.
        if gpus is None:
            device_specs = platform_device_specs
        else:
            # Get device specs from CLI (e.g., mlcube run ... --gpus='"device=1,5"'). These always, always override
            # platform device specs when present. We also print out warning (no actions will be taken) if user specs
            # (--gpus) conflict with platform specs (platform.accelerator_count).
            device_specs = DeviceSpecs.from_string(gpus)
            device_specs.check_with_platform_specs(platform_device_specs.num_devices)

        logger.info(
            "Device params `platform.accelerator_count` (%s) and `--gpus` (%s) resolved to device specs (%s).",
            str(accelerator_count), str(gpus), str(device_specs)
        )

        return device_specs

    def __str__(self) -> str:
        devices = "None" if self._devices is None else str([str(dev) for dev in self._devices])
        return f"{self.__class__.__name__}(none={self._none}, all={self._all}, num_gpus={self._num_devices}, "\
               f"devices={devices})"


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
                    - `platform`: Platform to use to run this MLCube (docker, singularity, gcp, k8s, etc.).
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

        task_args = [
            arg.split("=") for arg in unparsed_args if not arg.startswith("-P")
        ]
        task_args = {arg[0]: arg[1] for arg in task_args}

        # Set runner-specific parameters - think about refactoring, this needs to be done by runners.
        # Orr, maybe, these parameters can go first into platform section, and then be parsed by runners.
        # When not present, they need to be None. Empty values (e.g., --gpus="") will be interpreted as set.
        platform: t.Optional[str] = parsed_args.get("platform", None)
        if platform in {"docker", "singularity"}:
            runner_run_args = {}
            if parsed_args.get("network", None):
                runner_run_args["--network"] = parsed_args["network"]
            if parsed_args.get("security", None):
                key = "--security-opt" if platform == "docker" else "--security"
                runner_run_args[key] = parsed_args["security"]
            if parsed_args.get("gpus", None) is not None:
                if platform == "docker":
                    runner_run_args["--gpus"] = parsed_args["gpus"].strip()
                else:
                    runner_run_args["--nv"] = ""
            if parsed_args.get("memory", None):
                key = "--memory" if platform == "docker" else "--vm-ram"
                runner_run_args[key] = parsed_args["memory"]
            if parsed_args.get("cpu", None):
                key = "--cpuset-cpus" if platform == "docker" else "--vm-cpu"
                runner_run_args[key] = parsed_args["cpu"]
            if parsed_args.get("mount", None):
                runner_run_args["--mount_opts"] = parsed_args["mount"]

            mlcube_args.merge_with({platform: runner_run_args})

        return mlcube_args, task_args

    @staticmethod
    def parse_optional_arg(
        platform: t.Optional[str],
        network_option: t.Optional[str],
        security_option: t.Optional[str],
        gpus_option: t.Optional[str],
        memory_option: t.Optional[str],
        cpu_option: t.Optional[str],
        mount_option: t.Optional[str],
    ) -> t.Tuple[DictConfig, t.Dict]:
        """platform: Platform to use to run this MLCube (docker, singularity, gcp, k8s, etc.).
        network_option: Networking options defined during MLCube container execution.
        security_option: Security options defined during MLCube container execution.
        gpus_option: GPU usage options defined during MLCube container execution.
        memory_option: Memory RAM options defined during MLCube container execution.
        cpu_option: CPU options defined during MLCube container execution.
        mount_option: Mount options for paths.
        """
        mlcube_args, opts = {}, {}

        opts["--mount_opts"] = mount_option
        if network_option is not None:
            opts["--network"] = network_option

        if security_option is not None:
            key = "--security-opt" if platform == "docker" else "--security"
            opts[key] = security_option

        if gpus_option is not None:
            key = "--gpus" if platform == "docker" else "--nv"
            opts[key] = gpus_option

        if memory_option is not None:
            key = "--memory" if platform == "docker" else "--vm-ram"
            opts[key] = memory_option

        if cpu_option is not None:
            key = "--cpu-shares" if platform == "docker" else "--vm-cpu"
            opts[key] = cpu_option

        mlcube_args[platform] = opts
        return mlcube_args, {}
