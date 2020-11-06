from typing import Optional
from mlcommons_box.common.utils import Utils


class Status(object):
    RUNNING = 'RUNNING'
    STOPPING = 'STOPPING'
    TERMINATED = 'TERMINATED'


class Instance(object):
    """ Just a wrapper around GCP instance dict v1. """

    def __init__(self, instance: Optional[dict]) -> None:
        self.instance: dict = instance if isinstance(instance, dict) else {}

    @property
    def name(self) -> Optional[str]:
        return self.instance.get('name', None)

    @property
    def id(self) -> Optional[str]:
        return self.instance.get('id', None)

    @property
    def status(self) -> Optional[str]:
        return self.instance.get('status', None)

    @property
    def public_ip(self) -> Optional[str]:
        for interface in Utils.get(self.instance, 'networkInterfaces', []):
            for access_config in Utils.get(interface, 'accessConfigs', []):
                if Utils.get(access_config, 'name', '') == 'External NAT':
                    return Utils.get(access_config, 'natIP', None)
        return None

    def __str__(self) -> str:
        return f"Instance(name={self.name}, id={self.id}, status={self.status}, public_ip={self.public_ip})"
