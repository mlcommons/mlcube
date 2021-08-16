import os
import logging
import typing as t
from pathlib import Path
from omegaconf import DictConfig
from mlcube_ssh.ssh_run import Shell
from ssh_config.client import (SSHConfig, Host)
from mlcube.runner import (BaseConfig, BaseRunner)
from mlcube_gcp.gcp_client.instance import Instance as GCPInstance, Status as GCPInstanceStatus
from mlcube_gcp.gcp_client.service import Service


logger = logging.getLogger(__name__)


class Config(BaseConfig):

    CONFIG_SECTION = 'gcp'

    DEFAULT_CONFIG = {}

    """
    gcp:
        gcp:
            project_id:
            zone:
            credentials:
        instance:
            name:              # gcp-f1-micro
            machine_type:      # f1-micro
            disk_size_gb:      # 20
        platform:
    """

    @staticmethod
    def from_dict(gcp_env: DictConfig) -> DictConfig:
        Config.assert_keys_not_none('gcp', gcp_env, ['gcp', 'instance', 'platform'])
        Config.assert_keys_not_none('gcp.gcp', gcp_env.gcp, ['project_id', 'zone', 'credentials'])
        Config.assert_keys_not_none('gcp.instance', gcp_env.instance, ['name', 'machine_type', 'disk_size_gb'])
        return gcp_env


class GCPRun(BaseRunner):

    PLATFORM_NAME = 'gcp'

    def __init__(self, mlcube: t.Union[DictConfig, t.Dict], task: t.Text) -> None:
        super().__init__(mlcube, task, Config)

    def configure(self) -> None:
        """  """
        gcp: DictConfig = self.mlcube.gcp

        # Check that SSH is configured.
        ssh_config_file = os.path.join(Path.home(), '.ssh', 'config')
        try:
            ssh_config = SSHConfig.load(ssh_config_file)
            gcp_host: Host = ssh_config.get(gcp.instance.name)
        except KeyError:
            raise ValueError(f"SSH config ({ssh_config_file}) does not provide connection "
                             f"details for '{gcp.instance.name}'")
        # TODO: I can try to add this info on the fly assuming standard paths. Need to figure out the user name.
        if gcp_host.get('User', None) is None or gcp_host.get('IdentityFile', None) is None:
            raise ValueError(f"SSH config does not provide connection details for '{gcp.instance.name}'")

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

        # Make sure SSH config is up-to-date
        if gcp_host.get('HostName', None) != instance.public_ip:
            print(f"Updating SSH config (prev={gcp_host.get('HostName')}, new={instance.public_ip}, "
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
        gcp: DictConfig = self.mlcube.gcp
        Shell.run('mlcube', 'run', f'--mlcube={self.mlcube.root}', f'--platform={gcp.platform}', f'--task={self.task}')
