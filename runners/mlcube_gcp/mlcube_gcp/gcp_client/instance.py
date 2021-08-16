import typing as t


class Status(object):
    RUNNING = 'RUNNING'
    STOPPING = 'STOPPING'
    TERMINATED = 'TERMINATED'


class Instance(object):
    """ Just a wrapper around GCP instance dict v1. """

    def __init__(self, instance: t.Optional[t.Dict]) -> None:
        self.instance: t.Dict = instance if isinstance(instance, dict) else {}

    @property
    def name(self) -> t.Optional[t.Text]:
        return self.instance.get('name', None)

    @property
    def id(self) -> t.Optional[t.Text]:
        return self.instance.get('id', None)

    @property
    def status(self) -> t.Optional[t.Text]:
        return self.instance.get('status', None)

    @property
    def public_ip(self) -> t.Optional[t.Text]:
        for interface in self.instance.get('networkInterfaces', None) or []:
            for access_config in interface.get('accessConfigs', None) or []:
                if access_config.get('name', '') == 'External NAT':
                    return access_config.get('natIP', None)
        return None

    def __str__(self) -> t.Text:
        return f"Instance(name={self.name}, id={self.id}, status={self.status}, public_ip={self.public_ip})"
