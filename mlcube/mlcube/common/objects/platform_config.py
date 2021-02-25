from mlcube.common.objects import base
from mlcube.common.objects import common


class Container(base.StandardObject):
    SCHEMA_TYPE = "mlcube_platform_container"
    SCHEMA_VERSION = "0.1.0"
    fields = {
        "runtime": base.PrimitiveField(),    # Runtime should be deprecated.
        "command": base.PrimitiveField(),    # Executable (docker/nvidia-docker/podman).
        "run_args": base.PrimitiveField(),   # Arguments for "docker run" excluding image name and MLCube mount points.
        "image": base.PrimitiveField()       # Name of a docker image.
    }


class PlatformConfig(base.StandardObject):
    SCHEMA_TYPE = "mlcube_platform"
    SCHEMA_VERSION = "0.1.0"
    fields = {
        "platform": base.ObjectField(common.PlatformMetadata),
        "container": base.ObjectField(Container)
    }
