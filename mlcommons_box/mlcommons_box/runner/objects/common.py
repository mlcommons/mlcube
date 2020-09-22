from mlcommons_box.runner.objects import base


class VersionFilter(base.StandardObject):
    fields = {
        "min": base.PrimitiveField(),
        "max": base.PrimitiveField(),
        "good_list": base.PrimitiveField(),
        "bad_list": base.PrimitiveField()
    }


class PlatformMetadata(base.StandardObject):
    fields = {
        "name": base.PrimitiveField(),
        "version_filter": base.ObjectField(VersionFilter)
    }
