from mlcommons_box.runner import base_runner

class TemplateRunner(base_runner.BaseRunner):

    def action_configure(self, args):
        raise NotImplementedError

    def action_run(self, args):
        raise NotImplementedError
