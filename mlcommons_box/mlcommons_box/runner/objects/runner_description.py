from mlcommons_box.runner.objects import base
from mlcommons_box.runner.objects import common


class RunnerDescription(base.StandardObject):
    fields = {
        "platform": base.ObjectField(common.PlatformMetadata)
    }
