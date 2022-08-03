from unittest import TestCase

from mlcube.errors import IllegalParameterValueError

from mlcube_docker.docker_run import Config


from omegaconf import OmegaConf


class TestConfig(TestCase):

    def test_build_strategy(self) -> None:
        self.assertEqual('pull', Config.BuildStrategy.PULL)
        self.assertEqual('auto', Config.BuildStrategy.AUTO)
        self.assertEqual('always', Config.BuildStrategy.ALWAYS)

        for strategy in ('pull', 'auto', 'always'):
            Config.BuildStrategy.validate(strategy)

        self.assertRaises(IllegalParameterValueError, Config.BuildStrategy.validate, 'push')

    def test_merge(self) -> None:
        config = OmegaConf.create({'docker': {'image': 'mlcommons/mnist:0.01'}})
        Config.merge(config)
        self.assertEqual(
            config,
            OmegaConf.create({
                'runner': {'image': 'mlcommons/mnist:0.01'},
                'docker': {'image': 'mlcommons/mnist:0.01'}
            })
        )

    def test_validate(self) -> None:
        config = OmegaConf.create({
            'docker': {'image': 'mlcommons/mnist:0.01'},
            'runner': Config.DEFAULT.copy()
        })
        Config.validate(config)

        self.assertIsInstance(config.runner.build_args, str)
        self.assertIsInstance(config.runner.env_args, str)
