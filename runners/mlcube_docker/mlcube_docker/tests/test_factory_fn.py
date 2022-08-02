import typing as t
from unittest import TestCase

import mlcube_docker
from mlcube_docker.docker_run import DockerRun


class TestFactoryFunction(TestCase):

    def test_factory_fn(self) -> None:
        self.assertTrue(hasattr(mlcube_docker, 'get_runner_class'))
        self.assertTrue(callable(mlcube_docker.get_runner_class))

        runner_cls: t.Type[DockerRun] = mlcube_docker.get_runner_class()
        self.assertIs(runner_cls, DockerRun)
