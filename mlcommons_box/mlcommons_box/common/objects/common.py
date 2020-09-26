from mlcommons_box.common.objects import base


class PlatformMetadata(base.StandardObject):
    SCHEMA_TYPE = "mlcommons_box_platform_metadata"
    SCHEMA_VERSION = "0.1.0"
    fields = {
        "name": base.PrimitiveField(),
        "version": base.PrimitiveField()
    }
