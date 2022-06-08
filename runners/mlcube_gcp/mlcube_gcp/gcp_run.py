import os
import logging
import typing as t
from pathlib import Path
from omegaconf import (DictConfig, OmegaConf)
from mlcube.validate import Validate
from mlcube_ssh.ssh_run import Shell
from ssh_config.client import (SSHConfig, Host)
from mlcube.runner import (RunnerConfig, Runner)
from mlcube.errors import ExecutionError
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
        # TODO: (Sergey) why am I doing it here (copy-past bug)?
        ssh_config_file = os.path.join(Path.home(), '.ssh', 'mlcube')
        try:
            ssh_config = SSHConfig.load(ssh_config_file)
            gcp_host: Host = ssh_config.get(gcp.instance.name)
        except KeyError:
            raise ExecutionError.mlcube_configure_error(
                self.__class__.__name__,
                f"SSH configuration file ({ssh_config_file}) does not provide connection details for GCP instance "
                f"(name={gcp.instance.name}). Most likely this error has occurred due to implementation error - "
                "please, contact MLCube developers."
            )
        # TODO: I can try to add this info on the fly assuming standard paths. Need to figure out the user name.
        if gcp_host.get('User', None) is None or gcp_host.get('IdentityFile', None) is None:
            raise ExecutionError.mlcube_configure_error(
                self.__class__.__name__,
                f"SSH configuration file ({ssh_config_file}) provides connection details for GCP instance "
                f"(name={gcp.instance.name}), but these details do not include information about `User` "
                "and/or `IdentifyFile`."
            )

        # Connect to GCP
        logger.info("Connecting to GCP ...")
        try:
            service = Service(project_id=gcp.gcp.project_id, zone=gcp.gcp.zone, credentials=gcp.gcp.credentials)
        except Exception as err:
            raise ExecutionError.mlcube_configure_error(
                self.__class__.__name__,
                "The error most like is associated with either reading credentials, or connecting using google API ("
                f"project_id={gcp.gcp.project_id}, zone={gcp.gcp.zone}, credentials={gcp.gcp.credentials}). See "
                "context for more details.",
                error=str(err),
                gcp_info={'project_id': gcp.gcp.project_id, 'zone': gcp.gcp.zone, 'credentials': gcp.gcp.credentials}
            )

        # Figure out if an instance needs to be created
        try:
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
        except Exception as err:
            raise ExecutionError.mlcube_configure_error(
                self.__class__.__name__,
                "Failed to create or connect to remote GCP instance. See context for more details.",
                error=str(err),
                gcp_instance_info={
                    'name': gcp.instance.name, 'machine_type': gcp.instance.machine_type,
                    'disk_size_gb': gcp.instance.disk_size_gb
                }
            )

        # Make sure SSH mlcube is up-to-date
        if gcp_host.get('HostName', None) != instance.public_ip:
            print(f"Updating SSH mlcube (prev={gcp_host.get('HostName')}, new={instance.public_ip}, "
                  f"file={ssh_config_file})")
            ssh_config.update(instance.name, {'HostName': instance.public_ip})
            ssh_config.write(ssh_config_file)
            # TODO: clean '.ssh/known_hosts'.

        # Configure remote instance. This is specific for docker-based images now.
        try:
            Shell.ssh(
                gcp.instance.name,
                'sudo snap install docker && sudo addgroup --system docker && sudo adduser ${USER} docker && '
                'sudo snap disable docker && sudo snap enable docker && '
                'sudo apt update && yes | sudo apt install python3-pip virtualenv && sudo apt clean'
            )
        except ExecutionError as err:
            raise ExecutionError.mlcube_configure_error(
                self.__class__.__name__,
                "Failed to install system packages on a remote instance. See context for more details.",
                error=str(err)
            )

        # Remote GCP instance has been configured
        print(instance)

        # Should be as simple as invoking SSH configure.
        try:
            Shell.run(f"mlcube configure --mlcube={self.mlcube.root} --platform={gcp.platform}")
        except ExecutionError as err:
            raise ExecutionError.mlcube_configure_error(
                self.__class__.__name__,
                f"Error occurred while running mlcube configure with GCP platform (platform={gcp.platform}). See "
                "context for more details.",
                error=str(err)
            )

    def run(self) -> None:
        gcp: DictConfig = self.mlcube.runner
        try:
            Shell.run(f"mlcube run --mlcube={self.mlcube.root} --platform={gcp.platform} --task={self.task}")
        except ExecutionError as err:
            raise ExecutionError.mlcube_run_error(
                self.__class__.__name__,
                f"Error occurred while running MLCube task (platform={gcp.platform}, task={self.task}).",
                **err.context
            )
