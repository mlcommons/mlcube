import os
import yaml


def get_resource_from_file(filename):
    with open(filename, "r") as f:
        resource = yaml.safe_load(f)
    return resource


def get_task_config_from_file(filename):
    with open(filename, "r") as f:
        task_config = yaml.safe_load(f)
    return task_config


def get_manifest(resource):
    manifest = yaml.dump(resource, default_flow_style=False)
    return manifest


def write_manifest(resource, filename):
    if not os.path.exists(os.path.dirname(filename)):
        os.makedirs(os.path.dirname(filename))
    with open(filename, "w") as f:
        yaml.dump(resource, f)


def _add_task_arg(resource, task):
    # Currently a demo for "job" resource only.
    # TODO: this needs to be generalized.
    pod_template = resource["spec"]["template"]
    target_containers = pod_template.get("metadata", {}).get(
                        "annotations", {}).get("mlbox/target-containers", "")
    target_containers = target_containers.split(",")
    containers = pod_template["spec"]["containers"]
    for container in containers:
        if container["name"] in target_containers:
            if not container.get("args"):
                container["args"] = []
            container["args"].append("--mlbox_task={}".format(task))
    return resource


def _add_io_arg(resource, name, path):
    # Currently a demo for "job" resource and hostPath volumes only.
    # TODO: this needs to be generalized.
    pod_template = resource["spec"]["template"]
    volumes = pod_template["spec"]["volumes"]
    matching_volume = None
    matching_path = None
    for vol in volumes:
        if path.startswith(vol["hostPath"]["path"]):
            if matching_path is None or (
                        len(matching_path) < vol["hostPath"]["path"]):
                matching_volume = vol["name"]
                matching_path = vol["hostPath"]["path"]
    if matching_path is None:
        raise Exception(
                "Unable to find matching volume for path: {}".format(path))
    subpath = path[len(matching_path):].lstrip(os.path.sep)

    target_containers = pod_template.get("metadata", {}).get(
                        "annotations", {}).get("mlbox/target-containers", "")
    target_containers = target_containers.split(",")
    containers = pod_template["spec"]["containers"]
    for container in containers:
        if container["name"] not in target_containers:
            continue
        volume_mounts = container["volumeMounts"]
        for vmnt in volume_mounts:
            if vmnt["name"] == matching_volume:
                mount_path = vmnt["mountPath"]
                new_path = os.path.join(mount_path, subpath)
                if not container.get("args"):
                    container["args"] = []
                container["args"].append("--{}={}".format(name, new_path))

    return resource


def modify_resource(resource, task, task_config):
    # Currently a demo for "job" resource and hostPath volumes only.
    # TODO: this needs to be generalized.
    resource = _add_task_arg(resource, task)
    for key, val in task_config.items():
        resource = _add_io_arg(resource, key, val)
    return resource
