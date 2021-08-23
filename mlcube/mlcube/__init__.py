import pkgutil
import importlib

"""mlcube
"""

__version__ = "0.0.4"
name = "mlcube"


discovered_plugins = {
    name: importlib.import_module(name)
    for finder, name, ispkg
    in pkgutil.iter_modules()
    if name.startswith('mlcube_')
}


default_runners = [
    dict(platform='docker', name='mlcube_docker', priority=0, cls='mlcube_docker.docker_run.DockerRun'),
    dict(platform='singularity', name='mlcube_singularity', priority=0,
         cls='mlcube_singularity.singularity_run.SingularityRun'),
    dict(platform='ssh', name='mlcube_ssh', priority=0, cls='mlcube_ssh.ssh_run.SSHRun'),
    dict(platform='gcp', name='mlcube_gcp', priority=0, cls='mlcube_gcp.gcp_run.GCPRun'),
    dict(platform='k8s', name='mlcube_k8s', priority=0, cls='mlcube_k8s.k8s_run.KubernetesRun')
]


def validate_type(obj, expected_type) -> None:
    if not isinstance(obj, expected_type):
        raise TypeError(f"Actual object type ({type(obj)}) != expected type ({expected_type}).")
