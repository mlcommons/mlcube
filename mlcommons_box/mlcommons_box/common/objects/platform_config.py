from mlcommons_box.common.objects import base
from mlcommons_box.common.objects import common


class Container(base.StandardObject):
    SCHEMA_TYPE = "mlcommons_box_platform_container"
    SCHEMA_VERSION = "0.1.0"
    fields = {
        "runtime": base.PrimitiveField(),
        "image": base.PrimitiveField()
    }


class PlatformConfig(base.StandardObject):
    SCHEMA_TYPE = "mlcommons_box_platform"
    SCHEMA_VERSION = "0.1.0"
    fields = {
        "platform": base.ObjectField(common.PlatformMetadata),
        "container": base.ObjectField(Container)
    }
