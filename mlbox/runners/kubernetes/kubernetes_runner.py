import argparse
import datetime
import os
import yaml

from mlbox.runners.kubernetes import utils


def run(args):
    platform_config_file = args.platform_config

    # TODO: this is ugly and unsafe
    task = args.mlbox_task_ref.split(":")[-1].split("/")[0]
    task_config_file = os.path.join(
        args.mlbox_task_ref.split(":")[0], "tasks",
        args.mlbox_task_ref.split(":")[-1] + ".yaml")

    resource = utils.get_resource_from_file(platform_config_file)
    task_config = utils.get_task_config_from_file(task_config_file)

    new_resource = utils.modify_resource(resource, task, task_config)

    if args.dry_run:
        print(utils.get_manifest(new_resource))
    else:
        run_manifest_file = os.path.join(
                args.mlbox_task_ref.split(":")[0], "workspace", "runs",
                datetime.datetime.now().strftime("%y%m%d%H%M%S") + ".yaml")
        utils.write_manifest(new_resource, run_manifest_file)
        cmd = "kubectl create -f {}".format(run_manifest_file)
        print(cmd)
        if os.system(cmd) != 0:
            raise Exception('Command failed: {}'.format(cmd))


def main():
    parser = argparse.ArgumentParser(description="MLBox Kubernetes runner")
    # subparsers = parser.add_subparsers(dest="subcommand")
    # subparsers.required = True

    # subparser_run = subparsers.add_parser("run", help="Run an MLBox.")
    # subparser_run.add_argument(
    #         "mlbox_platform_config", type=str, default=None,
    #         help="Platform config to use.")
    # subparser_run.add_argument(
    #         "mlbox_task_ref", type=str, default=None,
    #         help="Reference of MLBox and task.")
    # subparser_run.add_argument(
    #         "--dry_run", action="store_true",
    #         help="Print generated Kubernetes manifest without creating "
    #              "the resources in the cluster.")
    # subparser_run.set_defaults(func=run)
    parser.add_argument(
            "platform_config", type=str, default=None,
            help="Platform config to use.")
    parser.add_argument(
            "mlbox_task_ref", type=str, default=None,
            help="Reference of MLBox and task.")
    parser.add_argument(
            "--dry_run", action="store_true",
            help="Print generated Kubernetes manifest without creating "
                 "the resources in the cluster.")

    args, _ = parser.parse_known_args()
    # args.func(args)
    run(args)


if __name__ == "__main__":
    main()
