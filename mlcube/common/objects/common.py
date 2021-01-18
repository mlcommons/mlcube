from mlcube.common.objects import base


class PlatformMetadata(base.StandardObject):
    SCHEMA_TYPE = "mlcube_platform_metadata"
    SCHEMA_VERSION = "0.1.0"
    fields = {
        "name": base.PrimitiveField(),
        "version": base.PrimitiveField()
    }
