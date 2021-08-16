import time
import typing as t
import googleapiclient.discovery
from google.oauth2 import service_account
from mlcube_gcp.gcp_client.operation import Operation


class Service(object):
    """
    https://cloud.google.com/compute/docs/tutorials/python-guide
    https://stackoverflow.com/questions/51303178/launch-gcp-instance-from-my-pc-using-python
    https://stackoverflow.com/questions/49444290/googleapiclient-authentication-using-personal-account
    """
    def __init__(self, project_id: t.Text, zone: t.Text, credentials: t.Optional[t.Text] = None) -> None:
        self.project_id: t.Text = project_id
        self.zone: t.Text = zone
        if isinstance(credentials, t.Dict) and 'file' in credentials:
            credentials = service_account.Credentials.from_service_account_file(
                credentials.get('file'),
                scopes=credentials.get('scopes', ['https://www.googleapis.com/auth/cloud-platform'])
            )
        else:
            credentials = None
        self.service = googleapiclient.discovery.build('compute', 'v1', credentials=credentials)

    def list_instances(self) -> t.List:
        response = self.service.instances().list(project=self.project_id, zone=self.zone).execute()
        return response.get('items', [])

    def get_instance(self, name: t.Text) -> t.Optional[t.Dict]:
        for instance in self.list_instances():
            if instance.get('name', None) == name:
                return instance
        return None

    def start_instance(self, name: t.Text) -> t.Dict:
        return self.service.instances().start(project=self.project_id, zone=self.zone, instance=name).execute()

    def stop_instance(self, name: t.Text) -> t.Dict:
        return self.service.instances().stop(project=self.project_id, zone=self.zone, instance=name).execute()

    def delete_instance(self, name: t.Text) -> t.Dict:
        return self.service.instances().delete(project=self.project_id, zone=self.zone, instance=name).execute()

    def create_instance(self, **kwargs) -> t.Dict:
        """
        https://cloud.google.com/compute/docs/reference/rest/v1/instances/setMachineType
        Assumed: https://cloud.google.com/compute/docs/instances/adding-removing-ssh-keys#project-wide
        https://cloud.google.com/compute/docs/reference/rest/v1/instances/insert
        """
        name = kwargs.get('name', 'gcp-f1-micro')
        machine_type = kwargs.get('machine_type', 'f1-micro')
        image = kwargs.get('image', {'project': 'ubuntu-os-cloud', 'family': 'ubuntu-1804-lts'})
        disk_size_gb = kwargs.get('disk_size_gb', 20)

        image_response = self.service.images().getFromFamily(project=image['project'], family=image['family']).execute()
        config: t.Dict = {
            'name': name,
            'machine_type': f"zones/{self.zone}/machineTypes/{machine_type}",
            'disks': [{
                'boot': True,
                'autoDelete': True,
                'initializeParams': {
                    'sourceImage': image_response['selfLink'],
                    'diskSizeGb': disk_size_gb
                }
            }],
            'networkInterfaces': [{
                'network': 'global/networks/default',
                'accessConfigs': [{
                    "kind": "compute#accessConfig",
                    'type': 'ONE_TO_ONE_NAT',
                    'name': 'External NAT',
                    "networkTier": "PREMIUM",
                }]
            }],
            'serviceAccounts': [{
                'email': 'default',
                'scopes': [
                    'https://www.googleapis.com/auth/devstorage.read_write',
                    'https://www.googleapis.com/auth/logging.write',
                    "https://www.googleapis.com/auth/monitoring.write",
                    "https://www.googleapis.com/auth/servicecontrol",
                    "https://www.googleapis.com/auth/service.management.readonly",
                    "https://www.googleapis.com/auth/trace.append"
                ]
            }],
        }
        return self.service.instances().insert(project=self.project_id, zone=self.zone, body=config).execute()

    def wait_for_operation(self, operation: t.Union[t.Text, t.Dict, Operation], retry_pause: float = 5):
        if isinstance(operation, t.Dict):
            operation = operation.get('name', None)
        elif isinstance(operation, Operation):
            operation = operation.name
        while True:
            result = self.service.zoneOperations().get(
                project=self.project_id, zone=self.zone, operation=operation
            ).execute()
            if result['status'] == 'DONE':
                if 'error' in result:
                    raise Exception(result['error'])
                return result
            time.sleep(retry_pause)
