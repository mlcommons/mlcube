from mlcube.common.objects import base
from mlcube.common.objects import common


class RunnerDescription(base.StandardObject):
    SCHEMA_TYPE = "mlcube_runner"
    SCHEMA_VERSION = "0.1.0"
    fields = {
        "platform": base.ObjectField(common.PlatformMetadata)
    }
