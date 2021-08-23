import logging
import urllib3
import kubernetes
import typing as t
from omegaconf import (DictConfig, OmegaConf)
from mlcube.runner import (BaseConfig, BaseRunner)

logger = logging.getLogger(__name__)


class Config(BaseConfig):
    """ Helper class to manage `k8s` environment configuration."""

    CONFIG_SECTION = 'k8s'

    DEFAULT_CONFIG = {}

    """
    k8s:
        image: ${docker.image}
        pvc: ${name}
        namespace:            # default
        volume_mount_prefix   # /mnt/mlcube/
    """

    @staticmethod
    def from_dict(k8s_env: DictConfig) -> DictConfig:
        k8s_env['image'] = k8s_env.get('image', None) or '${docker.image}'
        k8s_env['pvc'] = k8s_env.get('pvc', None) or '${name}'
        k8s_env['namespace'] = k8s_env.get('namespace', None) or 'default'
        k8s_env['volume_mount_prefix'] = k8s_env.get('volume_mount_prefix', None) or '/mnt/mlcube/'
        Config.assert_keys_not_none('k8s', k8s_env, ['image', 'pvc', 'namespace', 'volume_mount_prefix'])
        return k8s_env


class KubernetesRun(BaseRunner):

    PLATFORM_NAME = 'k8s'

    def __init__(self, mlcube: t.Union[DictConfig, t.Dict], task: t.Text) -> None:
        super().__init__(mlcube, task, Config)

    def binding_to_volumes(self, params: DictConfig,                                        # inputs
                           args: t.List[t.Text], volume_mounts: t.Dict, volumes: t.Dict):   # outputs
        logger.warning(
            "You are running Kubernetes MLCube runner. In current implementation, the following must be true:"
            "  - Default workspace must be used."
            "  - Default workspace must be the PVC named as self.mlcube.k8s.pvc."
            "  - All paths in tasks must be relative (relative to workspace). Do not prefix them with "
            "    {runtime.workspace}."
        )
        pvc_name = self.mlcube.k8s.pvc
        vol_mount_prefix = self.mlcube.k8s.volume_mount_prefix
        for param_name, param_def in params.items():
            # We assume all paths are RELATIVE! So, just adding parameter value is fine.
            # Workspace in a host OS ({runtime.workspace}) will be mounted as $vol_mount_prefix/$pvc_name.
            args.append(f"--{param_name}=" + vol_mount_prefix + pvc_name + "/" + param_def.default)
            volume_mounts[pvc_name] = kubernetes.client.V1VolumeMount(
                name=pvc_name,
                mount_path=vol_mount_prefix + pvc_name
            )
            volumes[pvc_name] = kubernetes.client.V1Volume(
                name=pvc_name,
                persistent_volume_claim=kubernetes.client.V1PersistentVolumeClaimVolumeSource(claim_name=pvc_name)
            )

    def create_job_manifest(self) -> kubernetes.client.V1Job:
        image: t.Text = self.mlcube.k8s.image
        logging.info(f"Using image: {image}")

        container_args: t.List[t.Text] = []
        container_volume_mounts: t.Dict = dict()
        container_volumes: t.Dict = dict()

        params = self.mlcube.tasks[self.task].parameters

        container_args.append(self.task)
        self.binding_to_volumes(params.inputs, container_args, container_volume_mounts, container_volumes)
        self.binding_to_volumes(params.outputs, container_args, container_volume_mounts, container_volumes)

        logging.info("Using Container arguments: %s" % container_args)

        container = kubernetes.client.V1Container(
            name="mlcube-container", image=image, args=container_args,
            volume_mounts=list(container_volume_mounts.values())
        )
        pod_template = kubernetes.client.V1PodTemplateSpec(
            metadata=kubernetes.client.V1ObjectMeta(labels={
                "app": "mlcube",
                "app-name": self.mlcube.name,
            }),
            spec=kubernetes.client.V1PodSpec(
                restart_policy="Never", containers=[container], volumes=list(container_volumes.values()))
        )
        job_spec = kubernetes.client.V1JobSpec(
            template=pod_template,
            backoff_limit=4,
        )

        mlcube_job_manifest = kubernetes.client.V1Job(
            api_version="batch/v1",
            kind="Job",
            metadata=kubernetes.client.V1ObjectMeta(generate_name="mlcube-" + self.mlcube.name + "-"),
            spec=job_spec,
        )
        logging.info("The MLCube Kubernetes Job manifest %s", mlcube_job_manifest)
        return mlcube_job_manifest

    def create_job(self, job_manifest: kubernetes.client.V1Job) -> t.Any:
        k8s_job_client = kubernetes.client.BatchV1Api()
        job_creation_response = k8s_job_client.create_namespaced_job(
            body=job_manifest,
            namespace=self.mlcube.k8s.namespace
        )
        logging.info("MLCommons Box k8s job created. Status='%s'" % str(job_creation_response.status))
        return job_creation_response

    def configure(self) -> None:
        ...

    def run(self) -> None:
        """Run a cube"""
        try:
            logging.info("Configuring MLCube as a Kubernetes Job...")
            kubernetes.config.load_kube_config()

            mlcube_job_manifest = self.create_job_manifest()
            _ = self.create_job(mlcube_job_manifest)
        except urllib3.exceptions.HTTPError:
            print(f"K8S runner failed to run MLCube. The actual error is printed below. "
                  "Your MLCube k8s configuration was:")
            print(OmegaConf.to_yaml(self.mlcube.k8s, resolve=True))
            raise
