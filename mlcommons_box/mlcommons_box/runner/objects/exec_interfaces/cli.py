from mlcommons_box.runner.objects import base


class CLI(base.StandardObject):
    fields = {
        "commmand": base.PrimitiveField(),
    }
