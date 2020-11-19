import logging
from typing import List, Dict
from mlcube.common import mlcube_metadata
from kubernetes import client, config

volume_mount_prefix = "/mnt/mlcube/"


class KubernetesRun(object):
    logger: logging.Logger = None
    mlcube_job_manifest: client.V1Job = None
    namespace: str = "default"

    def __init__(self, mlcube: mlcube_metadata.MLCube, loglevel: str):
        """Kubernetes Runner.
        Args:
            mlcube (mlcube_metadata.MLCube): MLCube specification. Reuses platform config from Docker.
        """
        logging.basicConfig(format='%(asctime)s - %(message)s',
                            datefmt='%d-%b-%y-%H:%M:%S',
                            level=loglevel)
        self.logger = logging.getLogger(__name__)

        self.mlcube: mlcube_metadata.MLCube = mlcube
        logging.info("MLCube instantiated!")

    def binding_to_volumes(self, binding: Dict, args: List[str], volume_mounts: Dict, volumes: Dict):
        for key, value in binding.items():
            args.append("--" + key + "=" + volume_mount_prefix +
                                  value['k8s']['pvc'] + "/" +
                                  value['path'])
            volume_mounts[
                value['k8s']['pvc']] = client.V1VolumeMount(
                    name=value['k8s']['pvc'],
                    mount_path=volume_mount_prefix +
                    value['k8s']['pvc'],
                )
            volumes[value['k8s']['pvc']] = client.V1Volume(
                name=value['k8s']['pvc'],
                persistent_volume_claim=client.
                V1PersistentVolumeClaimVolumeSource(
                    claim_name=value['k8s']['pvc']))

    def create_job_manifest(self):
        image: str = self.mlcube.platform.container.image
        logging.info(f"Using image: {image}")

        container_args: List[str] = []
        container_volume_mounts: Dict = dict()
        container_volumes: Dict = dict()
        
        self.binding_to_volumes(self.mlcube.invoke.input_binding, container_args, container_volume_mounts, container_volumes)
        self.binding_to_volumes(self.mlcube.invoke.output_binding, container_args, container_volume_mounts, container_volumes)
        logging.info("Using Container arguments: %s" % container_args)

        container = client.V1Container(name="mlcube-container",
                                       image=image,
                                       args=container_args,
                                       volume_mounts=list(
                                           container_volume_mounts.values()))
        pod_template = client.V1PodTemplateSpec(
            metadata=client.V1ObjectMeta(labels={
                "app": "mlcube",
                "app-name": self.mlcube.name,
            }),
            spec=client.V1PodSpec(restart_policy="Never",
                                  containers=[container],
                                  volumes=list(container_volumes.values())))
        job_spec = client.V1JobSpec(
            template=pod_template,
            backoff_limit=4,
        )

        self.mlcube_job_manifest = client.V1Job(
            api_version="batch/v1",
            kind="Job",
            metadata=client.V1ObjectMeta(generate_name="mlcube-" +
                                         self.mlcube.name + "-"),
            spec=job_spec,
        )

        logging.info("The MLCube Kubernetes Job manifest %s" %
                     self.mlcube_job_manifest)

    def create_job(self, k8s_job_client: client.BatchV1Api):
        job_creation_response = k8s_job_client.create_namespaced_job(
            body=self.mlcube_job_manifest,
            namespace=self.namespace,
        )

        logging.info("MLCommons Box k8s job created. Status='%s'" %
                     str(job_creation_response.status))

    def run(self):
        """Run a cube"""
        if self.mlcube.invoke.task_name != "kubernetes":
            raise RuntimeError("Uh oh. \
                Task file doesn't seem to be right, please use the correct kubernetes task file."
                               )
        logging.info("Configuring MLCube as a Kubernetes Job...")
        self.create_job_manifest()

        config.load_kube_config()
        batch_v1 = client.BatchV1Api()
        # create job on k8s cluster
        self.create_job(batch_v1)
