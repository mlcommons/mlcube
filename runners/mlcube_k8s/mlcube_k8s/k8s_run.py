import logging
import urllib3
import kubernetes
import time
import typing as t
from omegaconf import (DictConfig, OmegaConf)
from mlcube.errors import ExecutionError
from mlcube.runner import (RunnerConfig, Runner)
from mlcube.validate import Validate

logger = logging.getLogger(__name__)


class Config(RunnerConfig):
    """ Helper class to manage `k8s` environment configuration."""

    DEFAULT = OmegaConf.create({
        'runner': 'k8s',

        'pvc': '${name}',             # By default, PVC name equals to the name of this MLCube (mnist, matmul, ...).
        'image': '${docker.image}',   # Use image name from docker configuration section.
        'namespace': 'default'        # ...
    })

    @staticmethod
    def validate(mlcube: DictConfig) -> None:
        Validate(mlcube.runner, 'runner')\
            .check_unknown_keys(Config.DEFAULT.keys())\
            .check_values(['pvc', 'image', 'namespace'], str, blanks=False)


class KubernetesRun(Runner):

    CONFIG = Config

    def __init__(self, mlcube: t.Union[DictConfig, t.Dict], task: t.Text) -> None:
        super().__init__(mlcube, task)

    def binding_to_volumes(self, params: DictConfig,                                        # inputs
                           args: t.List[t.Text], volume_mounts: t.Dict, volumes: t.Dict):   # outputs
        logger.warning(
            "You are running Kubernetes MLCube runner. In current implementation, the following must be true:"
            "  - Default workspace must be used."
            "  - Default workspace must be the PVC named as self.mlcube.runner.pvc."
            "  - All paths in tasks must be relative (relative to workspace). Do not prefix them with "
            "    {runtime.workspace}."
        )
        pvc_name = self.mlcube.runner.pvc
        vol_mount_prefix = '/mnt/mlcube'
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
        image: t.Text = self.mlcube.runner.image
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
            namespace=self.mlcube.runner.namespace
        )
        logging.info("MLCommons Box k8s job created. Status='%s'" % str(job_creation_response.status))
        print("MLCommons Box k8s job created with name= %s for task= %s" % (str(job_creation_response.metadata.name), str(self.task)))
        return job_creation_response

    def wait_for_completion(self, job):
        k8s_job_client = kubernetes.client.BatchV1Api()
        print("Waiting for Job to complete in the kubernetes cluster")
        while(1):
            job = k8s_job_client.read_namespaced_job_status(job.metadata.name, job.metadata.namespace)
            status = job.status
            logging.info("Current job status='%s'" % str(status))
            if  status.conditions:
                if status.conditions[0].status and status.conditions[0].type == "Complete":
                    print("Job is successful")
                else:
                    print("Job has failed")
                break
            time.sleep(10)

    def configure(self) -> None:
        ...

    def run(self) -> None:
        """Run a cube"""
        try:
            logging.info("Configuring MLCube as a Kubernetes Job...")
            kubernetes.config.load_kube_config()

            mlcube_job_manifest = self.create_job_manifest()
            job = self.create_job(mlcube_job_manifest)
            self.wait_for_completion(job)
        except Exception as err:
            raise ExecutionError.mlcube_run_error(
                self.__class__.__name__,
                "See context for more details.",
                error=str(err)
            )
