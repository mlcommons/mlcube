from __future__ import absolute_import, division, print_function, unicode_literals
import yaml
import os
import argparse
import logging
import logging.config
from typing import List


logger = logging.getLogger(__name__)


def train(task_args: List[str], log_dir: str) -> None:
    """ Task: train.
    Input parameters:
        --data_dir, --log_dir, --model_dir, --parameters_file
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--parameters_file', '--parameters-file', type=str, default=None,
                        help="Parameters default values.")
    args = parser.parse_args(args=task_args)

    with open(args.parameters_file, 'r') as stream:
        parameters = yaml.load(stream, Loader=yaml.FullLoader)
    logger.info("Parameters have been read (%s).", args.parameters_file)

    #
    cmd = "mpiexec --allow-run-as-root --bind-to socket -np 1 python ./{}.py --log_dir={} {}".format(
        parameters.pop('model'),
        log_dir,
        ' '.join(["--{}={}".format(param, value) for param, value in parameters.items()])
    )
    print(cmd)
    logger.info("Command: %s", cmd)

    if os.system(cmd) != 0:
        raise RuntimeError('Command failed: {}'.format(cmd))


def main():
    """
    mnist.py task task_specific_parameters...
    """
    # noinspection PyBroadException
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument('--mlbox_task', '--mlbox-task', type=str, required=True, help="Task for this MLBOX.")
        parser.add_argument('--log_dir', '--log-dir', type=str, required=True, help="Logging directory.")
        ml_box_args, task_args = parser.parse_known_args()

        logger_config = {
            "version": 1,
            "disable_existing_loggers": True,
            "formatters": {
                "standard": {"format": "%(asctime)s - %(name)s - %(threadName)s - %(levelname)s - %(message)s"},
            },
            "handlers": {
                "file_handler": {
                    "class": "logging.FileHandler",
                    "level": "INFO",
                    "formatter": "standard",
                    "filename": os.path.join(ml_box_args.log_dir, "mlbox_mnist_{}.log".format(ml_box_args.mlbox_task))
                }
            },
            "loggers": {
                "": {"level": "INFO", "handlers": ["file_handler"]},
                "__main__": {"level": "NOTSET", "propagate": "yes"},
                "tensorflow": {"level": "NOTSET", "propagate": "yes"}
            }
        }
        logging.config.dictConfig(logger_config)

        if ml_box_args.mlbox_task == 'train':
            train(task_args, log_dir=ml_box_args.log_dir)
        else:
            raise ValueError("Unknown task: {}".format(task_args))
    except Exception as err:
        logger.exception(err)


if __name__ == '__main__':
    main()
