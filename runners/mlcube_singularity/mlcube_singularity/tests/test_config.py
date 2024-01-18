from unittest import TestCase

from mlcube_singularity.singularity_run import Config

from omegaconf import OmegaConf


class TestConfig(TestCase):
    def test_merge(self) -> None:
        scfg = {'image': 'mnist-0.0.1.sif', 'image_dir': '/path/to/image', 'singularity': 'singularity'}
        runtime = {'workspace': '/path/to/workspace', 'root': '/path/to/root'}
        config = OmegaConf.create({
            'singularity': scfg,
            'runtime': runtime,
            'runner': Config.DEFAULT
        })
        Config.merge(config)
        self.assertEqual(
            config,
            OmegaConf.create({
                'runner': OmegaConf.merge(Config.DEFAULT, scfg),
                'singularity': scfg,
                'runtime': runtime
            })
        )

    def test_validate(self) -> None:
        config = OmegaConf.create({
            'singularity': {'image': 'mnist-0.0.1.sif'},
            'runtime': {'workspace': '/path/to/workspace'},
            'runner': Config.DEFAULT.copy()
        })
        Config.validate(config)
