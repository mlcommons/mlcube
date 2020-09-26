import logging
import os

import yaml

from mlcommons_box.common.objects import base

logger = logging.getLogger(__name__)


def load_object_from_file(file_path: str,
                          obj_class: base.BaseObject) -> base.BaseObject:
    """Load an object from a yaml file.

    Args:
        file_path: Path to the file to load.
        obj_class: Class of the output object.

    Returns:
        An object loaded from the file.
    """
    try:
        with open(file_path, "r") as f:
            yaml_dict = yaml.load(f, Loader=yaml.Loader)
    except Exception:
        logger.error("Unable to load yaml file: {}".format(file_path))
        raise
    try:
        obj_instance = obj_class()
        obj_instance.from_primitive(yaml_dict)
    except Exception:
        logger.error("Failed to parse platform config file: {}".format(
                file_path))
        raise
    return obj_instance
