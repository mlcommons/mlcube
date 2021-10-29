import os
import logging
import typing as t
from pathlib import Path
from omegaconf import (DictConfig, OmegaConf)
from mlcube.validate import Validate
from mlcube_ssh.ssh_run import Shell
from ssh_config.client import (SSHConfig, Host)
from mlcube.runner import (RunnerConfig, Runner)
from mlcube_gcp.gcp_client.instance import Instance as GCPInstance, Status as GCPInstanceStatus
from mlcube_gcp.gcp_client.service import Service


logger = logging.getLogger(__name__)


class Config(RunnerConfig):

    DEFAULT = OmegaConf.create({
        'runner': 'gcp',

        'gcp': {
            'project_id': '',
            'zone': '',
            'credentials': ''
        },
        'instance': {
            'name': '',
            'machine_type': '',
            'disk_size_gb': ''
        },
        'platform': ''
    })

    @staticmethod
    def validate(mlcube: DictConfig) -> None:
        Validate(mlcube.runner, 'runner')\
            .check_unknown_keys(Config.DEFAULT.keys())\
            .check_values(['gcp', 'instance'], DictConfig)\
            .check_values(['platform'], str, blanks=False)
        Validate(mlcube.runner.gcp, 'runner.gcp')\
            .check_unknown_keys(['project_id', 'zone', 'credentials'])\
            .check_values(['project_id', 'zone'], str, blanks=False) \
            .not_none(['credentials'])
        Validate(mlcube.runner.instance, 'runner.instance')\
            .check_unknown_keys(['name', 'machine_type', 'disk_size_gb'])\
            .not_none(['name', 'machine_type', 'disk_size_gb']) \
            .check_values(['name', 'machine_type'], str, blanks=False)


class GCPRun(Runner):

    CONFIG = Config

    def __init__(self, mlcube: t.Union[DictConfig, t.Dict], task: t.Text) -> None:
        super().__init__(mlcube, task)

    def configure(self) -> None:
        """  """
        gcp: DictConfig = self.mlcube.runner

        # Check that SSH is configured.
        ssh_config_file = os.path.join(Path.home(), '.ssh', 'mlcube')
        try:
            ssh_config = SSHConfig.load(ssh_config_file)
            gcp_host: Host = ssh_config.get(gcp.instance.name)
        except KeyError:
            raise ValueError(f"SSH mlcube ({ssh_config_file}) does not provide connection "
                             f"details for '{gcp.instance.name}'")
        # TODO: I can try to add this info on the fly assuming standard paths. Need to figure out the user name.
        if gcp_host.get('User', None) is None or gcp_host.get('IdentityFile', None) is None:
            raise ValueError(f"SSH mlcube does not provide connection details for '{gcp.instance.name}'")

        # Connect to GCP
        logger.info("Connecting to GCP ...")
        service = Service(project_id=gcp.gcp.project_id, zone=gcp.gcp.zone, credentials=gcp.gcp.credentials)

        # Figure out if an instance needs to be created
        instance = GCPInstance(service.get_instance(gcp.instance.name))
        if instance.name is None:
            print("Creating GCP instance ...")
            service.wait_for_operation(
                service.create_instance(name=gcp.instance.name, machine_type=gcp.instance.machine_type,
                                        disk_size_gb=gcp.instance.disk_size_gb)
            )
            instance = GCPInstance(service.get_instance(gcp.instance.name))

        # Check its running status
        if instance.status != GCPInstanceStatus.RUNNING:
            print("Starting GCP instance ...")
            service.wait_for_operation(service.start_instance(instance.name))
            instance = GCPInstance(service.get_instance(gcp.instance.name))

        # Make sure SSH mlcube is up-to-date
        if gcp_host.get('HostName', None) != instance.public_ip:
            print(f"Updating SSH mlcube (prev={gcp_host.get('HostName')}, new={instance.public_ip}, "
                  f"file={ssh_config_file})")
            ssh_config.update(instance.name, {'HostName': instance.public_ip})
            ssh_config.write(ssh_config_file)
            # TODO: clean '.ssh/known_hosts'.

        # Configure remote instance. This is specific for docker-based images now.
        Shell.ssh(
            gcp.instance.name,
            'sudo snap install docker && sudo addgroup --system docker && sudo adduser ${USER} docker && '
            'sudo snap disable docker && sudo snap enable docker && '
            'sudo apt update && yes | sudo apt install python3-pip virtualenv && sudo apt clean'
        )

        # Remote GCP instance has been configured
        print(instance)

        # Should be as simple as invoking SSH configure.
        Shell.run('mlcube', 'configure', f'--mlcube={self.mlcube.root}', f'--platform={gcp.platform}')

    def run(self) -> None:
        gcp: DictConfig = self.mlcube.runner
        Shell.run('mlcube', 'run', f'--mlcube={self.mlcube.root}', f'--platform={gcp.platform}', f'--task={self.task}')
