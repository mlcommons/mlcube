import os
import typing as t
from unittest import TestCase

from mlcube.parser import CliParser, MLCubeDirectory

from omegaconf import (DictConfig, OmegaConf)


class TestParser(TestCase):
    def setUp(self) -> None:
        if 'SINGULARITYENV_CUDA_VISIBLE_DEVICES' in os.environ:
            self._singularityenv_cuda_visible_devices = os.environ['SINGULARITYENV_CUDA_VISIBLE_DEVICES']

    def tearDown(self) -> None:
        if hasattr(self, '_singularityenv_cuda_visible_devices'):
            os.environ['SINGULARITYENV_CUDA_VISIBLE_DEVICES'] = self._singularityenv_cuda_visible_devices
        elif 'SINGULARITYENV_CUDA_VISIBLE_DEVICES' in os.environ:
            del os.environ['SINGULARITYENV_CUDA_VISIBLE_DEVICES']

    def _check_mlcube_directory(self, mlcube: MLCubeDirectory, path: str, file: str) -> None:
        self.assertIsInstance(mlcube, MLCubeDirectory)
        self.assertEqual(mlcube.path, path)
        self.assertEqual(mlcube.file, file)

    def test_mlcube_instances(self) -> None:
        self._check_mlcube_directory(MLCubeDirectory(), os.getcwd(), "mlcube.yaml")
        self._check_mlcube_directory(MLCubeDirectory(os.getcwd()), os.getcwd(), "mlcube.yaml")

    def test_cli_parser(self) -> None:
        for method_name in ("parse_mlcube_arg", "parse_list_arg", "parse_extra_arg"):
            self.assertTrue(getattr(CliParser, method_name))

    def test_parse_mlcube_arg(self) -> None:
        self._check_mlcube_directory(CliParser.parse_mlcube_arg(os.getcwd()), os.getcwd(), "mlcube.yaml")
        self._check_mlcube_directory(CliParser.parse_mlcube_arg(None), os.getcwd(), "mlcube.yaml")

    def test_parse_list_arg(self) -> None:
        for arg in ("", None):
            self.assertListEqual(CliParser.parse_list_arg(arg, 'main'), ['main'])

        self.assertListEqual(CliParser.parse_list_arg('download'), ['download'])
        self.assertListEqual(CliParser.parse_list_arg('download,train'), ['download', 'train'])

    def _check_cli_args(
            self,
            actual_mlcube_args: DictConfig, actual_task_args: t.Dict,
            expected_mlcube_args: t.Dict, expected_task_args: t.Dict
    ) -> None:
        self.assertIsInstance(actual_mlcube_args, DictConfig)
        self.assertEqual(OmegaConf.to_container(actual_mlcube_args), expected_mlcube_args)

        self.assertIsInstance(actual_task_args, dict)
        self.assertEqual(actual_task_args, expected_task_args)

    def test_parse_extra_args_unparsed(self) -> None:
        mlcube_args, task_args = CliParser.parse_extra_arg(
            unparsed_args=[
                "-Pdocker.image=IMAGE_NAME",
                "data_config=/configs/data.yaml",
                "-Pplatform.host_memory_gb=30",
                "data_dir=/data/imagenet"
            ],
            parsed_args={}
        )
        self._check_cli_args(
            actual_mlcube_args=mlcube_args,
            actual_task_args=task_args,
            expected_mlcube_args={'docker': {'image': 'IMAGE_NAME'}, 'platform': {'host_memory_gb': 30}},
            expected_task_args={'data_config': '/configs/data.yaml', 'data_dir': '/data/imagenet'}
        )

    def test_parse_extra_args_parsed_docker(self) -> None:
        mlcube_args, task_args = CliParser.parse_extra_arg(
            unparsed_args=[],
            parsed_args={
                "platform": "docker",
                "network": "NETWORK_1", "security": "SECURITY_1", "gpus": "GPUS_1", "memory": "MEMORY_1", "cpu": "CPU_1"
            }
        )
        self._check_cli_args(
            actual_mlcube_args=mlcube_args,
            actual_task_args=task_args,
            expected_mlcube_args={
                'docker': {
                    '--network': 'NETWORK_1',
                    '--security-opt': 'SECURITY_1',
                    '--gpus': 'GPUS_1',
                    '--memory': 'MEMORY_1',
                    '--cpuset-cpus': 'CPU_1'
                }
            },
            expected_task_args={}
        )

    def test_parse_extra_args_parsed_singularity(self) -> None:
        mlcube_args, task_args = CliParser.parse_extra_arg(
            unparsed_args=[],
            parsed_args={
                "platform": "singularity",
                "network": "NETWORK_2", "security": "SECURITY_2", "gpus": "GPUS_2", "memory": "MEMORY_2", "cpu": "CPU_2"
            }
        )
        self._check_cli_args(
            actual_mlcube_args=mlcube_args,
            actual_task_args=task_args,
            expected_mlcube_args={
                'singularity': {
                    '--network': 'NETWORK_2',
                    '--security': 'SECURITY_2',
                    '--nv': '',
                    '--vm-ram': 'MEMORY_2',
                    '--vm-cpu': 'CPU_2'
                }
            },
            expected_task_args={}
        )
        self.assertIn('SINGULARITYENV_CUDA_VISIBLE_DEVICES', os.environ)
        self.assertEqual(os.environ['SINGULARITYENV_CUDA_VISIBLE_DEVICES'], 'GPUS_2')
