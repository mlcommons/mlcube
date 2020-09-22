from mlcommons_box.runner.objects import base


class EnvironmentVariable(base.StandardObject):
    fields = {
        "name": base.PrimitiveField(),
        "value": base.PrimitiveField()
    }


class EnvironmentVariableList(base.StandardObjectList):
    item_class = EnvironmentVariable


class Container(base.StandardObject):
    fields = {
        "runtime": base.PrimitiveField(),
        "image": base.PrimitiveField(),
        "command": base.PrimitiveField(),
        "args": base.PrimitiveField(),
        "env": base.ObjectField(EnvironmentVariableList)
    }
