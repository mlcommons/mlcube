from unittest import TestCase

from mlcube_singularity.singularity_run import Config

from omegaconf import OmegaConf


class TestConfig(TestCase):
    def test_merge(self) -> None:
        scfg = {'image': 'mnist-0.0.1.sif', 'image_dir': '/path/to/image', 'singularity': 'singularity'}
        config = OmegaConf.create({
            'singularity': scfg,
            'runtime': {'workspace': '/path/to/workspace'}
        })
        Config.merge(config)
        self.assertEqual(
            config,
            OmegaConf.create({
                'runner': scfg,
                'singularity': scfg,
                'runtime': {'workspace': '/path/to/workspace'}
            })
        )

    def test_validate(self) -> None:
        config = OmegaConf.create({
            'singularity': {'image': 'mnist-0.0.1.sif'},
            'runtime': {'workspace': '/path/to/workspace'},
            'runner': Config.DEFAULT.copy()
        })
        Config.validate(config)
