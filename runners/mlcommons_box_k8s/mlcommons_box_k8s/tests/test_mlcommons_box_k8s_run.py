from unittest import TestCase
from mlcommons_box.common import mlbox_metadata, objects
from mlcommons_box.common.objects import platform_config
from mlcommons_box_k8s.k8s_run import KubernetesRun


class TestKubernetesRun(TestCase):
    def setUp(self):
        self.path_to_mlbox = "mlcommons_box_k8s/tests/test_data/test_box"
        self.path_to_platform = "mlcommons_box_k8s/tests/test_data/test_box/platforms/docker.yaml"
        self.path_to_task = "mlcommons_box_k8s/tests/test_data/test_box/run/kubernetes.yaml"
        self.mlbox = mlbox_metadata.MLBox(path=self.path_to_mlbox)
        self.mlbox.platform = objects.load_object_from_file(
            file_path=self.path_to_platform,
            obj_class=platform_config.PlatformConfig)
        self.mlbox.invoke = mlbox_metadata.MLBoxInvoke(self.path_to_task)
        self.mlbox_k8s_runner = KubernetesRun(mlbox=self.mlbox,
                                              loglevel="INFO")

    def test_create_job_manifest(self):
        self.mlbox_k8s_runner.create_job_manifest()
        assert True
