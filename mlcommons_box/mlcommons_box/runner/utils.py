import os

import yaml

from mlcommons_box.runner.objects import platform_config


def build_runner_config(box_root_path,
                        user_platform_file,
                        action,
                        task):
    """Build runner config.
    The runner config is built by combining the runner config information from
    the user provided platform file (i.e. user platform file) and the box
    included platform file (i.e. box platform file) for a given combination of
    runner action and task.

    Args:
        box_root_path: path to the box root
        user_platform_file: path to the user platform file
        action: runner action name
        task: box task name
    
    Returns:
        The built runner config.
    """

    runner_config = None

    user_platform_config = _load_platform_config(user_platform_file)
    if user_platform_config is None:
        raise ValueError("Invalid platform config: {}".format(
                            user_platform_file))

    user_runner_config = _search_runner_config(
            user_platform_config, action, task)

    box_platform_config = _search_box_platform_config(
            box_root_path, user_platform_config.platform.name)
    if box_platform_config is None:
        raise ValueError("Box platform config not found.")
        runner_config = user_runner_config
    else:
        box_runner_config = _search_runner_config(
                box_platform_config, action, task)
        runner_config = _merge_runner_configs(
                box_runner_config, user_runner_config)
        runner_config.exec.resolve_parameters()

    return runner_config


def _load_platform_config(filepath):
    try:
        with open(filepath, "r") as f:
            config_dict = yaml.load(f)
    except Exception:
        raise
    try:
        config_instance = platform_config.PlatformConfig(primitive=config_dict)
    except Exception:
        raise
    return config_instance


def _search_box_platform_config(box_root_path, platform_name):
    # find the box platform config that matches the user platform config
    box_platform_config = None
    platform_dir = os.path.join(box_root_path, "platforms")
    for filename in os.listdir(platform_dir):
        if os.path.isfile(os.path.join(platform_dir, filename)):
            try:
                candidate = _load_platform_config(
                        os.path.join(platform_dir, filename))
            except Exception:
                candidate = None
            if candidate and (candidate.platform.name == platform_name):
                box_platform_config = candidate
                break
    return box_platform_config


def _search_runner_config(platform_config, action, task):
    # search for the runner config that matches action and task
    if action is None:
        raise ValueError("Action cannot be None.")

    matching_list = []
    runner_config_list = platform_config.runner_configs
    for candidate in runner_config_list:
        if candidate.action is None and candidate.task is None:
            matching_list.append((candidate, 0))
        elif candidate.action == action:
            if candidate.task is None:
                matching_list.append((candidate, 1))
            elif candidate.task == task:
                matching_list.append((candidate, 2))
    result = None
    if matching_list:
        matching_list.sort(reverse=True, key=lambda x: x[1])
        result = matching_list[0][0]
    return result


def _merge_runner_configs(box_runner_config, user_runner_config):
    result = box_runner_config
    if user_runner_config is not None:
        result.merge(user_runner_config)
    return result
