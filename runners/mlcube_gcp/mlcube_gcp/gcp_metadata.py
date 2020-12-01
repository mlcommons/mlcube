import os
from mlcube.common.utils import Utils


class GCP(object):
    def __init__(self, config: dict) -> None:
        self.project_id = config.get('project_id', None)
        self.zone = config.get('zone', None)
        self.credentials = config.get('credentials', None)

        if isinstance(self.credentials, dict) and self.credentials.get('file', None) is not None:
            self.credentials['file'] = os.path.expandvars(self.credentials['file'])

    def __str__(self) -> str:
        return f"GCP(project_id={self.project_id}, zone={self.zone}, credentials={self.credentials})"


class Instance(object):
    def __init__(self, config: dict) -> None:
        self.name = config.get('name', 'gcp-f1-micro')
        self.machine_type = config.get('machine_type', 'f1-micro')
        self.disk_size_gb = config.get('disk_size_gb', 20)


class Platform(object):
    def __init__(self, path: str) -> None:
        self.type: str = 'ssh'

        cfg = Utils.load_yaml(path)
        if not isinstance(cfg, dict):
            raise ValueError(f"Invalid platform configuration, type={type(cfg)}. Expected: 'dict'.")

        self.gcp: GCP = GCP(cfg.get('gcp', {}))
        self.instance: Instance = Instance(cfg.get('instance', {}))
        self.platform = cfg.get('platform', None)

    def __str__(self) -> str:
        return f"Platform(gcp={self.gcp}, instance={self.instance}, platform={self.platform})"
