import os
import logging
from pathlib import Path
from ssh_config.client import SSHConfig, Host
from mlcommons_box.common import mlbox_metadata
from mlcommons_box_gcp.gcp_client.instance import Instance as GCPInstance, Status as GCPInstanceStatus
from mlcommons_box_gcp.gcp_client.service import Service
from mlcommons_box_gcp.gcp_metadata import Platform
from mlcommons_box_ssh.ssh_run import Shell
from mlcommons_box_ssh.__main__ import (configure_ as configure_ssh, run_ as run_ssh)

logger = logging.getLogger(__name__)


class GCPRun(object):
    def __init__(self, mlbox: mlbox_metadata.MLBox) -> None:
        """Docker Runner.
        Args:
            mlbox (mlbox_metadata.MLBox): MLBox specification including platform configuration for Docker.
        """
        self.mlbox: mlbox_metadata.MLBox = mlbox

    def configure(self) -> None:
        """  """
        platform: Platform = self.mlbox.platform

        # Check that SSH is configured.
        try:
            ssh_config_file = os.path.join(Path.home(), '.ssh', 'config')
            ssh_config = SSHConfig.load(ssh_config_file)
            gcp_host: Host = ssh_config.get(platform.instance.name)
        except KeyError:
            raise ValueError(f"SSH config ({ssh_config_file}) does not provide connection "
                             f"details for '{platform.instance.name}'")
        # TODO: I can try to add this info on the fly assuming standard paths. Need to figure out the user name.
        if gcp_host.get('User', None) is None or gcp_host.get('IdentityFile', None) is None:
            raise ValueError(f"SSH config does not provide connection details for '{platform.instance.name}'")

        # Connect to GCP
        logger.info("Connecting to GCP ...")
        service = Service(project_id=platform.gcp.project_id, zone=platform.gcp.zone)

        # Figure out if an instance needs to be created
        instance = GCPInstance(service.get_instance(platform.instance.name))
        if instance.name is None:
            print("Creating GCP instance ...")
            service.wait_for_operation(
                service.create_instance(name=platform.instance.name, machine_type=platform.instance.machine_type,
                                        disk_size_gb=platform.instance.disk_size_gb)
            )
            instance = GCPInstance(service.get_instance(platform.instance.name))

        # Check its running status
        if instance.status != GCPInstanceStatus.RUNNING:
            print("Starting GCP instance ...")
            service.wait_for_operation(
                service.start_instance(instance.name)
            )
            instance = GCPInstance(service.get_instance(platform.instance.name))

        # Make sure SSH config is up-to-date
        if gcp_host.get('HostName', None) != instance.public_ip:
            print(f"Updating SSH config (prev={gcp_host.get('HostName')}, new={instance.public_ip}, "
                  f"file={ssh_config_file})")
            ssh_config.update(instance.name, {'HostName': instance.public_ip})
            ssh_config.write(ssh_config_file)
            # TODO: clean '.ssh/known_hosts'.

        # Configure remote instance. This is specific for docker-based images now.
        Shell.ssh(
            platform.instance.name,
            'sudo snap install docker && sudo addgroup --system docker && sudo adduser ${USER} docker && '
            'sudo snap disable docker && sudo snap enable docker && '
            'sudo apt update && yes | sudo apt install python3-pip virtualenv && sudo apt clean'
        )

        # Remote GCP instance has been configured
        print(instance)

        # Should be as simple as invoking SSH configure.
        configure_ssh(
            mlbox=self.mlbox.root,
            platform=os.path.join(self.mlbox.root, 'platforms', platform.platform)
        )

    def run(self, task_file: str) -> None:
        run_ssh(
            mlbox=self.mlbox.root,
            platform=os.path.join(self.mlbox.root, 'platforms', self.mlbox.platform.platform),
            task=task_file
        )
