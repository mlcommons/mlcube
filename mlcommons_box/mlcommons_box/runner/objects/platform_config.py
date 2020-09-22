from mlcommons_box.runner.objects import base
from mlcommons_box.runner.objects import common
from mlcommons_box.runner.objects import exec_interfaces


class Parameter(base.StandardObject):
    fields = {
        "name": base.PrimitiveField(),
        "default": base.PrimitiveField(),
        "value": base.PrimitiveField()
    }


class ParameterList(base.StandardObjectList):
    item_class = Parameter


class ExecConfig(base.StandardObject):
    fields = {
        "type": base.PrimitiveField(),
        "parameters": base.ObjectField(ParameterList),
        "exec_interfaces": base.ObjectField(
                exec_interfaces.ExecInterfaces, embedded=True),
    }

    def resolve_parameters(self):
        param_map = {}
        for param in self.parameters:
            param_map.setdefault(param.name, param)
            param_map[param.name].merge(param)
        # TODO: actually resolve parameters
        # (replacing template placeholders with actual value)


class RunnerConfig(base.StandardObject):
    fields = {
        "action": base.PrimitiveField(),
        "task": base.PrimitiveField(),
        "exec": base.ObjectField(ExecConfig)
    }


class RunnerConfigList(base.StandardObjectList):
    item_class = RunnerConfig


class ResourceConfig(base.StandardObject):
    fields = {
        "cpus": base.PrimitiveField(),
        "gpus": base.PrimitiveField(),
        "memory_gb": base.PrimitiveField()
    }


class PlatformConfig(base.StandardObject):
    fields = {
        "platform": base.ObjectField(common.PlatformMetadata),
        "resources": base.ObjectField(ResourceConfig),
        "runner_configs": base.ObjectField(RunnerConfigList)
    }
