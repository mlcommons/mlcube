from unittest import TestCase

from mlcube.parser import CliParser

from omegaconf import (DictConfig, OmegaConf)


class TestParser(TestCase):
    def test_parse_list_arg(self) -> None:
        for arg in ("", None):
            self.assertListEqual(CliParser.parse_list_arg(arg, 'main'), ['main'])

        self.assertListEqual(CliParser.parse_list_arg('download'), ['download'])
        self.assertListEqual(CliParser.parse_list_arg('download,train'), ['download', 'train'])

    def test_parse_extra_args(self) -> None:
        mlcube_args, task_args = CliParser.parse_extra_arg(
            "-Pdocker.image=IMAGE_NAME",
            "data_config=/configs/data.yaml",
            "-Pplatform.host_memory_gb=30",
            "data_dir=/data/imagenet"
        )
        self.assertIsInstance(mlcube_args, DictConfig)
        self.assertEqual(
            OmegaConf.to_container(mlcube_args),
            {'docker': {'image': 'IMAGE_NAME'}, 'platform': {'host_memory_gb': 30}}
        )

        self.assertIsInstance(task_args, dict)
        self.assertEqual(
            task_args,
            {'data_config': '/configs/data.yaml', 'data_dir': '/data/imagenet'}
        )
