from unittest import TestCase
from unittest.mock import (mock_open, patch)

from mlcube.config import (IOType, MLCubeConfig, ParameterType)

from omegaconf import (DictConfig, ListConfig, OmegaConf)


_MLCUBE_MNIST_CONFIG = """
name: mnist
description: MLCommons MNIST MLCube example
authors:
  - {name: "First Second", email: "first.second@company.com", org: "Company Inc."}

platform:
  accelerator_count: 0
  accelerator_maker: NVIDIA
  accelerator_model: A100-80GB
  host_memory_gb: 40
  need_internet_access: True
  host_disk_space_gb: 100

docker:
  image: mlcommons/mnist:0.0.1

singularity:
  image: mnist-0.0.1.sif

tasks:
  download:
    parameters:
      inputs:
        data_config: {type: file, default: data.yaml}
      outputs:
        data_dir: {type: directory, default: data}
        log_dir: {type: directory, default: logs}
  train:
    parameters:
      inputs:
        data_dir: {type: directory, default: data}
        train_config: {type: file, default: train.yaml}
      outputs:
        log_dir: {type: directory, default: logs}
        model_dir: {type: directory, default: model}
"""


class TestConfig(TestCase):

    def _check_standard_config(self, mlcube: DictConfig) -> None:
        self.assertIsInstance(mlcube, DictConfig)

        for key in ('name', 'description', 'authors',
                    'platform',
                    'docker', 'singularity',
                    'tasks',
                    'runtime', 'runner'):
            self.assertIn(key, mlcube)
            self.assertIsNotNone(mlcube[key])

        self.assertIsInstance(mlcube.name, str)
        self.assertEqual(mlcube.name, 'mnist')

        self.assertIsInstance(mlcube.description, str)
        self.assertEqual(mlcube.description, 'MLCommons MNIST MLCube example')

        self.assertIsInstance(mlcube.authors, ListConfig)
        self.assertListEqual(
            OmegaConf.to_container(mlcube.authors),
            [{'name': 'First Second', 'email': 'first.second@company.com', 'org': 'Company Inc.'}]
        )

        self.assertIsInstance(mlcube.platform, DictConfig)
        self.assertDictEqual(
            OmegaConf.to_container(mlcube.platform),
            {'accelerator_count': 0, 'accelerator_maker': 'NVIDIA', 'accelerator_model': 'A100-80GB',
             'host_memory_gb': 40, 'need_internet_access': True, 'host_disk_space_gb': 100}
        )

        self.assertIsInstance(mlcube.docker, DictConfig)
        self.assertDictEqual(OmegaConf.to_container(mlcube.docker), {'image': 'mlcommons/mnist:0.0.1'})

        self.assertIsInstance(mlcube.singularity, DictConfig)
        self.assertDictEqual(OmegaConf.to_container(mlcube.singularity), {'image': 'mnist-0.0.1.sif'})

        self.assertIsInstance(mlcube.tasks, DictConfig)
        self.assertDictEqual(
            OmegaConf.to_container(mlcube.tasks),
            {
                'download': {
                    'parameters': {
                        'inputs': {
                            'data_config': {'type': 'file', 'default': 'data.yaml'}
                        },
                        'outputs': {
                            'data_dir': {'type': 'directory', 'default': 'data'},
                            'log_dir': {'type': 'directory', 'default': 'logs'}
                        }
                    },
                },
                'train': {
                    'parameters': {
                        'inputs': {
                            'data_dir': {'type': 'directory', 'default': 'data'},
                            'train_config': {'type': 'file', 'default': 'train.yaml'}
                        },
                        'outputs': {
                            'log_dir': {'type': 'directory', 'default': 'logs'},
                            'model_dir': {'type': 'directory', 'default': 'model'}
                        }
                    }
                }
            }
        )

        self.assertIsInstance(mlcube.runtime, DictConfig)
        self.assertDictEqual(
            OmegaConf.to_container(mlcube.runtime),
            {'root': '/some/path/to', 'workspace': '/some/path/to/workspace'}
        )

        self.assertIsInstance(mlcube.runner, DictConfig)
        self.assertDictEqual(OmegaConf.to_container(mlcube.runner), {})

    @patch("io.open", mock_open(read_data=_MLCUBE_MNIST_CONFIG))
    def test_create_mlcube_config_default(self) -> None:
        mlcube: DictConfig = MLCubeConfig.create_mlcube_config("/some/path/to/mlcube.yaml")
        self._check_standard_config(mlcube)

    @patch("io.open", mock_open(read_data=_MLCUBE_MNIST_CONFIG))
    def test_create_mlcube_config_with_mlcube_cli_args(self) -> None:
        # MLCube parameters are passed to MLCube on a command line using `-P` prefix. The below CLI argument has the
        # following form on a command line: -Pdocker.image='mlcommons/mnist:0.0.2'
        mlcube: DictConfig = MLCubeConfig.create_mlcube_config(
            "/some/path/to/mlcube.yaml",
            mlcube_cli_args=OmegaConf.create({'docker': {'image': 'mlcommons/mnist:0.0.2'}})
        )

        self.assertIsInstance(mlcube.docker.image, str)
        self.assertEqual(mlcube.docker.image, 'mlcommons/mnist:0.0.2')

        mlcube.docker.image = 'mlcommons/mnist:0.0.1'
        self._check_standard_config(mlcube)

    def test_io_type(self) -> None:
        self.assertEqual(IOType.INPUT, 'input')
        self.assertTrue(IOType.is_valid('input'))

        self.assertEqual(IOType.OUTPUT, 'output')
        self.assertTrue(IOType.is_valid('output'))

        self.assertFalse(IOType.is_valid('unknown'))

    def test_parameter_type(self) -> None:
        self.assertEqual(ParameterType.FILE, 'file')
        self.assertTrue(ParameterType.is_valid('file'))

        self.assertEqual(ParameterType.DIRECTORY, 'directory')
        self.assertTrue(ParameterType.is_valid('directory'))

        self.assertEqual(ParameterType.UNKNOWN, 'unknown')
        self.assertTrue(ParameterType.is_valid('unknown'))

        self.assertFalse(ParameterType.is_valid('parameter'))
