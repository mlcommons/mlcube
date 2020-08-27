import argparse
try:
    import importlib.resources as pkg_resources # >= python 3.7
except ImportError:
    import importlib_resources as pkg_resources # < python 3.7
import os
import yaml

from mlcommons_box.runner import util


class BaseRunner(object):

    def __init__(self):
        self._init_argparser(self)

    ## CLI

    def _init_argparser(self):
        self.argparser = argparse.ArgumentParser(
                description="MLCommons Box Runner")
        self.action_argparsers = {}
        subparsers_action = self.argparser.add_subparsers(
                description="runner action", dest="action")
        subparsers_action.required = True

        # Sub-command "configure"
        parser_configure = subparsers_action.add_parser("configure",
                help="configure a platform")
        parser_configure.add_argument("--box", type=str, default=None,
                help="root directory to the box")
        parser_configure.add_argument("--platform", type=str, default=None,
                help="platform config file")
        self.action_argparsers["configure"] = parser_configure

        # Sub-command "run"
        parser_run = subparsers_action.add_parser("run", help="run a box")
        parser_run.add_argument("--box", type=str, default=None,
                help="root directory to the box")
        parser_run.add_argument("--task", type=str, default=None,
                help="task config file")
        parser_run.add_argument("--platform", type=str, default=None,
                help="platform config file")
        self.argparsers["run"] = parser_run

    def get_argparser(self):
        return self.argparser

    def get_action_argparser(self, action):
        parser = self.arg_parsers.get(action, None)
        if parser is None:
            raise ValueError("Action not supported: {}".format(action))
        return parser

    def parse_args(self):
        self.args = self.argparser.parse_args()

    def run(self):
        self.parse_args()
        if self.args.action == "configure":
            self.action_configure(self.args)
        elif self.args.action == "run":
            self.action_run(self.args)
        else:
            raise ValueError("Unknonw action: {}".format(self.args.action))

    ## Action implementations

    def action_configure(self, args):
        raise NotImplementedError

    def action_run(self, args):
        raise NotImplementedError

    ## Utils

    @staticmethod
    def get_runner_metadata(package):
        runner_metadata = pkg_resources.open_text(
                package, "mlcommons_box_runner.yaml")
        # TODO: validation
        yaml.load()
        return runner_metadata

    @staticmethod
    def _validate_platform():
        # TODO
        pass

    @staticmethod
    def _load_platform_manifest(platform_file):
        # read a platform config file and return the platform config in it
        # if the file is not a valid platform config, return None
        with open() as f:
            platform = yaml.load(platform_file)
            if not _validate_platform(platform):
                platform = None
        return platform

    @staticmethod
    def _search_platform_base(box_root_path, platform_metadata):
        # search for the platform base that matches the given platform overlay
        platform_base = None
        platform_dir = os.path.join(box_root_path, "platforms")
        for filename in os.listdir(platform_dir):
            if os.path.isfile(os.path.join(platform_dir, filename)):
                candidate = _load_platform_manifest(
                        os.path.join(platform_dir, filename))
                if candidate and candidate["platform_metadata"]["type"] == \
                            platform_metadata["type"]:
                    platform_base = candidate
        return platform_base

    @staticmethod
    def _search_runner_config(platform, action, task):
        # search for the runner config that matches action and task
        if action is None:
            raise ValueError("Action cannot be None.")
        if task is None:
            raise ValueError("Task cannot be None.")

        runner_config = None
        runner_config_list = platform["runner_configs"]
        for candidate in runner_config_list:
            candidate_action = candidate.get("action")
            candidate_task = candidate.get("task", None)
            if candidate_action == action:
                if candidate_task in [None, task]:
                    runner_config = candidate
                    if candidate.get("task", None) == task:
                        break
        if runner_config is None:
            raise ValueError("Runner config not found.")
        return runner_config

    @staticmethod
    def _fuse_runner_configs(runner_config_base, runner_config_overlay):
        runner_config = util.merge_dict(
                runner_config_base, runner_config_overlay)
        # TODO: generate a static exec spec from template and parameters
        return runner_config

    @staticmethod
    def generate_runner_config(box_root_path,
                               platform_overlay_file,
                               action,
                               task):
        runner_config = None

        platform_overlay = _load_platform_manifest(platform_overlay_file)
        if platform_overlay is None:
            raise ValueError("Invalid platform config: {}".format(
                             platform_overlay_file))

        runner_config_overlay = _search_runner_config(
                platform_overlay, action, task)
        
        if runner_config_overlay is None:
            raise ValueError("Runner config not found.")

        platform_base = _search_platform_base(
                box_root_path, platform_overlay["platform_metadata"])
        if platform_base is None:
            print("[WARN] Platform base not found, using overlay directly.")
            runner_config = runner_config_overlay
        else:
            runner_config_base = _search_runner_config(
                    platform_base, action, task)
            runner_config = _fuse_runner_configs(
                    runner_config_base, runner_config_overlay)

        return runner_config
