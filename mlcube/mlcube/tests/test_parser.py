import os
import typing as t
from unittest import TestCase

from omegaconf import DictConfig, OmegaConf

from mlcube.errors import ConfigurationError
from mlcube.parser import CliParser, MLCubeDirectory, DeviceSpecs


class TestParser(TestCase):
    def setUp(self) -> None:
        if "SINGULARITYENV_CUDA_VISIBLE_DEVICES" in os.environ:
            self._singularityenv_cuda_visible_devices = os.environ[
                "SINGULARITYENV_CUDA_VISIBLE_DEVICES"
            ]

    def tearDown(self) -> None:
        if hasattr(self, "_singularityenv_cuda_visible_devices"):
            os.environ[
                "SINGULARITYENV_CUDA_VISIBLE_DEVICES"
            ] = self._singularityenv_cuda_visible_devices
        elif "SINGULARITYENV_CUDA_VISIBLE_DEVICES" in os.environ:
            del os.environ["SINGULARITYENV_CUDA_VISIBLE_DEVICES"]

    def _check_mlcube_directory(
        self, mlcube: MLCubeDirectory, path: str, file: str
    ) -> None:
        self.assertIsInstance(mlcube, MLCubeDirectory)
        self.assertEqual(mlcube.path, path)
        self.assertEqual(mlcube.file, file)

    def test_mlcube_instances(self) -> None:
        self._check_mlcube_directory(MLCubeDirectory(), os.getcwd(), "mlcube.yaml")
        self._check_mlcube_directory(
            MLCubeDirectory(os.getcwd()), os.getcwd(), "mlcube.yaml"
        )

    def test_cli_parser(self) -> None:
        for method_name in ("parse_mlcube_arg", "parse_list_arg", "parse_extra_arg"):
            self.assertTrue(getattr(CliParser, method_name))

    def test_parse_mlcube_arg(self) -> None:
        self._check_mlcube_directory(
            CliParser.parse_mlcube_arg(os.getcwd()), os.getcwd(), "mlcube.yaml"
        )
        self._check_mlcube_directory(
            CliParser.parse_mlcube_arg(None), os.getcwd(), "mlcube.yaml"
        )

    def test_parse_list_arg(self) -> None:
        for arg in ("", None):
            self.assertListEqual(CliParser.parse_list_arg(arg, "main"), ["main"])

        self.assertListEqual(CliParser.parse_list_arg("download"), ["download"])
        self.assertListEqual(
            CliParser.parse_list_arg("download,train"), ["download", "train"]
        )

    def _check_cli_args(
        self,
        actual_mlcube_args: DictConfig,
        actual_task_args: t.Dict,
        expected_mlcube_args: t.Dict,
        expected_task_args: t.Dict,
    ) -> None:
        self.assertIsInstance(actual_mlcube_args, DictConfig)
        self.assertEqual(
            OmegaConf.to_container(actual_mlcube_args), expected_mlcube_args
        )

        self.assertIsInstance(actual_task_args, dict)
        self.assertEqual(actual_task_args, expected_task_args)

    def test_parse_extra_args_unparsed(self) -> None:
        mlcube_args, task_args = CliParser.parse_extra_arg(
            unparsed_args=[
                "-Pdocker.image=IMAGE_NAME",
                "data_config=/configs/data.yaml",
                "-Pplatform.host_memory_gb=30",
                "data_dir=/data/imagenet",
            ],
            parsed_args={},
        )
        self._check_cli_args(
            actual_mlcube_args=mlcube_args,
            actual_task_args=task_args,
            expected_mlcube_args={
                "docker": {"image": "IMAGE_NAME"},
                "platform": {"host_memory_gb": 30},
            },
            expected_task_args={
                "data_config": "/configs/data.yaml",
                "data_dir": "/data/imagenet",
            },
        )

    def test_parse_extra_args_parsed_docker(self) -> None:
        mlcube_args, task_args = CliParser.parse_extra_arg(
            unparsed_args=[],
            parsed_args={
                "platform": "docker",
                "network": "NETWORK_1",
                "security": "SECURITY_1",
                "gpus": "GPUS_1",
                "memory": "MEMORY_1",
                "cpu": "CPU_1",
                "mount": "MOUNT_1",
            },
        )
        self._check_cli_args(
            actual_mlcube_args=mlcube_args,
            actual_task_args=task_args,
            expected_mlcube_args={
                "docker": {
                    "--network": "NETWORK_1",
                    "--security-opt": "SECURITY_1",
                    "--gpus": "GPUS_1",
                    "--memory": "MEMORY_1",
                    "--cpuset-cpus": "CPU_1",
                    "--mount_opts": "MOUNT_1",
                }
            },
            expected_task_args={},
        )

    def test_parse_extra_args_parsed_singularity(self) -> None:
        mlcube_args, task_args = CliParser.parse_extra_arg(
            unparsed_args=[],
            parsed_args={
                "platform": "singularity",
                "network": "NETWORK_2",
                "security": "SECURITY_2",
                "gpus": "GPUS_2",
                "memory": "MEMORY_2",
                "cpu": "CPU_2",
                "mount": "MOUNT_2",
            },
        )
        self._check_cli_args(
            actual_mlcube_args=mlcube_args,
            actual_task_args=task_args,
            expected_mlcube_args={
                "singularity": {
                    "--network": "NETWORK_2",
                    "--security": "SECURITY_2",
                    "--nv": "",
                    "--vm-ram": "MEMORY_2",
                    "--vm-cpu": "CPU_2",
                    "--mount_opts": "MOUNT_2",
                }
            },
            expected_task_args={},
        )
        # self.assertIn("SINGULARITYENV_CUDA_VISIBLE_DEVICES", os.environ)
        # self.assertEqual(os.environ["SINGULARITYENV_CUDA_VISIBLE_DEVICES"], "GPUS_2")


class TestDeviceSpecs(TestCase):
    def _check_val(self, actual: t.Optional = None, expected: t.Optional = None) -> None:
        if expected is None:
            self.assertIsNone(actual)
        else:
            self.assertEqual(expected, actual)

    def _check_device(
            self, device: DeviceSpecs.Device, index: t.Optional[int] = None, uuid: t.Optional[str] = None
    ) -> None:
        self.assertIsInstance(device, DeviceSpecs.Device)
        self._check_val(device.index, index)
        self._check_val(device.uuid, uuid)

    def test_device_init(self) -> None:
        device = DeviceSpecs.Device()
        self.assertIsNone(device.index)
        self.assertIsNone(device.uuid)

        device = DeviceSpecs.Device(index=1)
        self.assertEqual(1, device.index)
        self.assertIsNone(device.uuid)

        device = DeviceSpecs.Device(uuid="GPU-1f22a253-c329-dfb7-0db4-e005efb6a4c7")
        self.assertIsNone(device.index)
        self.assertEqual("GPU-1f22a253-c329-dfb7-0db4-e005efb6a4c7", device.uuid)

    def test_device_create(self) -> None:
        device = DeviceSpecs.Device.create("2")
        self.assertEqual(2, device.index)
        self.assertIsNone(device.uuid)

        device = DeviceSpecs.Device.create("GPU-1f22a253-c329-dfb7-0db4-e005efb6a4c7")
        self.assertIsNone(device.index)
        self.assertEqual("GPU-1f22a253-c329-dfb7-0db4-e005efb6a4c7", device.uuid)

    def _check_none(self, specs: DeviceSpecs) -> None:
        self.assertIsInstance(specs, DeviceSpecs)
        self.assertIsInstance(str(specs), str)
        self.assertTrue(specs.none is not None and specs.none is True)
        self.assertTrue(specs.all is not None and specs.all is False)
        self.assertIsNone(specs.num_devices)
        self.assertIsNone(specs.devices)

    def _check_devices_specified(self, specs: DeviceSpecs) -> None:
        self.assertIsInstance(specs, DeviceSpecs)
        self.assertIsInstance(str(specs), str)
        self.assertTrue(specs.none is not None and specs.none is False)
        self.assertTrue(specs.all is not None and specs.all is False)
        self.assertIsNone(specs.num_devices)
        self.assertIsInstance(specs.devices, list)
        self.assertTrue(len(specs.devices) > 0)
        for device in specs.devices:
            self.assertIsInstance(device, DeviceSpecs.Device)

    def test_init(self) -> None:
        self._check_none(DeviceSpecs())

    def test_none(self) -> None:
        for gpus in (None, "", "   ", "0"):
            self._check_none(DeviceSpecs.from_string(gpus))

    def test_all(self) -> None:
        specs = DeviceSpecs.from_string("all")
        self.assertTrue(specs.none is not None and specs.none is False)
        self.assertTrue(specs.all is not None and specs.all is True)
        self.assertIsNone(specs.num_devices)
        self.assertIsNone(specs.devices)

    def test_num_devices(self) -> None:
        for num_devices in (1, 3, 5):
            specs = DeviceSpecs.from_string(f"{num_devices}")
            self.assertTrue(specs.none is not None and specs.none is False)
            self.assertTrue(specs.all is not None and specs.all is False)
            self.assertTrue(specs.num_devices is not None and specs.num_devices == num_devices)
            self.assertIsNone(specs.devices)

    def test_devices(self) -> None:
        specs = DeviceSpecs.from_string("device=1")
        self._check_devices_specified(specs)
        self.assertEqual(1, len(specs.devices))
        self._check_device(specs.devices[0], index=1, uuid=None)

        specs = DeviceSpecs.from_string("device=2,3")
        self._check_devices_specified(specs)
        self.assertEqual(2, len(specs.devices))
        self._check_device(specs.devices[0], index=2, uuid=None)
        self._check_device(specs.devices[1], index=3, uuid=None)

        specs = DeviceSpecs.from_string("device=GPU-1f22a253-c329-dfb7-0db4-e005efb6a4c7")
        self._check_devices_specified(specs)
        self.assertEqual(1, len(specs.devices))
        self._check_device(specs.devices[0], index=None, uuid="GPU-1f22a253-c329-dfb7-0db4-e005efb6a4c7")

        specs = DeviceSpecs.from_string("device=GPU-1f22a253-c329-dfb7-0db4-e005efb6a4c7,7")
        self._check_devices_specified(specs)
        self.assertEqual(2, len(specs.devices))
        self._check_device(specs.devices[0], index=None, uuid="GPU-1f22a253-c329-dfb7-0db4-e005efb6a4c7")
        self._check_device(specs.devices[1], index=7, uuid=None)

        # Check that exception is raised when device list is provided without `device=` prefix.
        self.assertRaises(
            ConfigurationError,
            DeviceSpecs.from_string,
            gpus="0,1,2"
        )

    def _check_docker_specs(
            self, specs: DeviceSpecs.DockerSpecs, gpus: t.Optional[str] = None,
            cuda_visible_devices: t.Optional[str] = None
    ) -> None:
        self.assertIsInstance(specs, DeviceSpecs.DockerSpecs)
        self._check_val(specs.gpus, gpus)
        self._check_val(specs.cuda_visible_devices, cuda_visible_devices)

    def test_get_docker_specs(self) -> None:
        docker_specs: DeviceSpecs.DockerSpecs = DeviceSpecs.from_string("").get_docker_specs()
        self._check_docker_specs(docker_specs, gpus=None, cuda_visible_devices=None)

        docker_specs: DeviceSpecs.DockerSpecs = DeviceSpecs.from_string("all").get_docker_specs()
        self._check_docker_specs(docker_specs, gpus="all", cuda_visible_devices=None)

        docker_specs: DeviceSpecs.DockerSpecs = DeviceSpecs.from_string("1").get_docker_specs()
        self._check_docker_specs(docker_specs, gpus="1", cuda_visible_devices="0")

        docker_specs: DeviceSpecs.DockerSpecs = DeviceSpecs.from_string("3").get_docker_specs()
        self._check_docker_specs(docker_specs, gpus="3", cuda_visible_devices="0,1,2")

        docker_specs: DeviceSpecs.DockerSpecs = DeviceSpecs.from_string("device=3").get_docker_specs()
        self._check_docker_specs(docker_specs, gpus="device=3", cuda_visible_devices="0")

        docker_specs: DeviceSpecs.DockerSpecs = DeviceSpecs.from_string("device=7,GPU-UUID").get_docker_specs()
        self._check_docker_specs(docker_specs, gpus="device=7,GPU-UUID", cuda_visible_devices="0,1")

    def test_check_with_platform_specs(self) -> None:
        """Run all execution paths to check does not crash."""
        for accelerator_count in (None, -1):
            DeviceSpecs().check_with_platform_specs(accelerator_count=accelerator_count)

        for gpus in ("", "1"):
            DeviceSpecs.from_string(gpus).check_with_platform_specs(accelerator_count=0)

        for gpus in ("all", "2", "device=4,5", "1", "device=2", "device=5,6,7"):
            DeviceSpecs.from_string(gpus).check_with_platform_specs(accelerator_count=2)

    def test_from_config(self) -> None:
        for count in (None, 0, -1):
            specs = DeviceSpecs.from_config(accelerator_count=count, gpus=None)
            self.assertTrue(specs.none)

        for num_dev in (1, 3):
            # This must set GPUs spec.
            specs = DeviceSpecs.from_config(accelerator_count=num_dev, gpus=None)
            self.assertIsNotNone(specs.num_devices)
            self.assertEqual(num_dev, specs.num_devices)
            # Check that we can override and disable GPUs
            for gpus in ("", "0"):
                self.assertTrue(DeviceSpecs.from_config(accelerator_count=num_dev, gpus=gpus).none)
