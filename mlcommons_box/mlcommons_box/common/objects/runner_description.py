from mlcommons_box.common.objects import base
from mlcommons_box.common.objects import common


class RunnerDescription(base.StandardObject):
    SCHEMA_TYPE = "mlcommons_box_runner"
    SCHEMA_VERSION = "0.1.0"
    fields = {
        "platform": base.ObjectField(common.PlatformMetadata)
    }
