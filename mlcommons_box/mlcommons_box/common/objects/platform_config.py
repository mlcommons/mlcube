from mlcommons_box.common.objects import base
from mlcommons_box.common.objects import common


class Container(base.StandardObject):
    """ Generic configuration for container-based platforms such as Docker and Singularity. """
    SCHEMA_TYPE = "mlcommons_box_platform_container"
    SCHEMA_VERSION = "0.1.0"
    fields = {
        "image": base.PrimitiveField(),
        "parameters": base.PrimitiveField()
    }


class PlatformConfig(base.StandardObject):
    """ Generic platform configuration for MLCommons-Box runners. """
    SCHEMA_TYPE = "mlcommons_box_platform"
    SCHEMA_VERSION = "0.1.0"
    fields = {
        "platform": base.ObjectField(common.PlatformMetadata),
        "configuration": base.DictOfObject()
    }


class ContainerPlatformConfig(base.StandardObject):
    """ Generic platform configuration for container-based runners. """
    SCHEMA_TYPE = "mlcommons_box_platform"
    SCHEMA_VERSION = "0.1.0"
    fields = {
        "platform": base.ObjectField(common.PlatformMetadata),
        "configuration": base.ObjectField(Container)
    }
