import os
from unittest import TestCase
from mlcube.common import mlcube_metadata, objects
from mlcube.common.objects import platform_config
from mlcube_k8s.k8s_run import KubernetesRun


class TestKubernetesRun(TestCase):
    def setUp(self):
        self.path_to_mlcube = os.path.join(os.path.dirname(__file__), "test_data/test_cube")
        self.path_to_platform = os.path.join(self.path_to_mlcube, "platforms/docker.yaml")
        self.path_to_task = os.path.join(self.path_to_mlcube, "run/kubernetes.yaml")
        self.mlcube = mlcube_metadata.MLCube(path=self.path_to_mlcube)
        self.mlcube.platform = objects.load_object_from_file(
            file_path=self.path_to_platform,
            obj_class=platform_config.PlatformConfig)
        self.mlcube.invoke = mlcube_metadata.MLCubeInvoke(self.path_to_task)
        self.mlcube_k8s_runner = KubernetesRun(mlcube=self.mlcube,
                                              loglevel="INFO")

    def test_create_job_manifest(self):
        self.mlcube_k8s_runner.create_job_manifest()
        assert True
