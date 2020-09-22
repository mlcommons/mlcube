from mlcommons_box.runner.objects import base
from mlcommons_box.runner.objects.exec_interfaces import cli
from mlcommons_box.runner.objects.exec_interfaces import container


class ExecInterfaces(base.StandardObject):
    fields = {
        "cli": base.ObjectField(cli.CLI),
        "container": base.ObjectField(container.Container)
    }
