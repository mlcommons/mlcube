
"""
https://www.tensorflow.org/tutorials/quickstart/beginner
Disable GPUs - not all nodes used for testing have GPUs
os.environ['CUDA_VISIBLE_DEVICES'] = ''
"""

from __future__ import (absolute_import, division, print_function, unicode_literals)

import argparse
import logging.config
import os
from enum import Enum
from typing import List

import numpy as np
import tensorflow as tf
import yaml
from tensorflow.keras.utils import get_file

logger = logging.getLogger(__name__)

class Task(str, Enum):
    DownloadData = 'download'
    Train = 'train'
    Kubernetes = 'kubernetes'


def download(task_args: List[str]) -> None:
    """ Task: download.
    Input parameters:
        --data_dir
    """
    logger.info(f"Starting '{Task.DownloadData}' task")
    parser = argparse.ArgumentParser()
    parser.add_argument('--data_dir', '--data-dir', type=str, default=None, help="Dataset path.")
    parser.add_argument('--model_dir', '--model-dir', type=str, default=None, help="Model output directory.")
    parser.add_argument('--parameters_file', '--parameters-file', type=str, default=None,
                        help="Parameters default values.")
    args = parser.parse_args(args=task_args)

    data_dir = args.data_dir
    if data_dir is None:
        raise ValueError("Data directory is not specified (did you use --data-dir=PATH?)")
    if not data_dir.startswith("/"):
        logger.warning("Data directory seems to be a relative path.")

    data_file = os.path.join(data_dir, 'mnist.npz')
    if os.path.exists(data_file):
        logger.info("MNIST data has already been download (file exists: %s)", data_file)
        return

    data_file = get_file(
        fname=data_file,
        origin='https://storage.googleapis.com/tensorflow/tf-keras-datasets/mnist.npz',
        file_hash='731c5ac602752760c8e48fbffcf8c3b850d9dc2a2aedcf2cc48468fc17b673d1'
    )

    if not os.path.isfile(data_file):
        raise ValueError(f"MNIST dataset has not been downloaded - dataset file does not exist: {data_file}")
    else:
        logger.info("MNIST dataset has been downloaded.")
    logger.info("The '%s' task has been completed.", Task.DownloadData)


def train(task_args: List[str]) -> None:
    """ Task: train.
    Input parameters:
        --data_dir, --log_dir, --model_dir, --parameters_file
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--data_dir', '--data-dir', type=str, default=None, help="Dataset path.")
    parser.add_argument('--model_dir', '--model-dir', type=str, default=None, help="Model output directory.")
    parser.add_argument('--parameters_file', '--parameters-file', type=str, default=None,
                        help="Parameters default values.")
    args = parser.parse_args(args=task_args)

    with open(args.parameters_file, 'r') as stream:
        parameters = yaml.load(stream, Loader=yaml.FullLoader)
    logger.info("Parameters have been read (%s).", args.parameters_file)

    dataset_file = os.path.join(args.data_dir, 'mnist.npz')
    with np.load(dataset_file, allow_pickle=True) as f:
        x_train, y_train = f['x_train'], f['y_train']
        x_test, y_test = f['x_test'], f['y_test']
    x_train, x_test = x_train / 255.0, x_test / 255.0
    logger.info("Dataset has been loaded (%s).", dataset_file)

    model = tf.keras.models.Sequential([
        tf.keras.layers.Flatten(input_shape=(28, 28)),
        tf.keras.layers.Dense(128, activation='relu'),
        tf.keras.layers.Dropout(0.2),
        tf.keras.layers.Dense(10, activation='softmax')
    ])
    logger.info("Model has been built.")

    model.compile(
        optimizer=parameters.get('optimizer', 'adam'),
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy']
    )
    logger.info("Model has been compiled.")

    # Train and evaluate
    model.fit(
        x_train,
        y_train,
        batch_size=parameters.get('batch_size', 32),
        epochs=parameters.get('train_epochs', 5)
    )
    logger.info("Model has been trained.")

    model.evaluate(x_test, y_test, verbose=2)
    logger.info("Model has been evaluated.")

    model.save(os.path.join(args.model_dir, 'mnist_model'))
    logger.info("Model has been saved.")


def main():
    """
    mnist.py task task_specific_parameters...
    """
    # noinspection PyBroadException
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument('mlcube_task', type=str, help="Task for this MLBOX.")
        parser.add_argument('--log_dir', '--log-dir', type=str, required=True, help="Logging directory.")
        ml_cube_args, task_args = parser.parse_known_args()
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
                    "filename": os.path.join(ml_cube_args.log_dir, f"mlcube_mnist_{ml_cube_args.mlcube_task}.log")
                },
                "stream_handler": {
                    "class": "logging.StreamHandler",
                    "level": "INFO",
                    "formatter": "standard",
                }
            },
            "loggers": {
                "": {"level": "INFO", "handlers": ["file_handler", "stream_handler"]},
                "__main__": {"level": "NOTSET", "propagate": "yes"},
                "tensorflow": {"level": "NOTSET", "propagate": "yes"}
            }
        }
        logging.config.dictConfig(logger_config)
        if ml_cube_args.mlcube_task == Task.DownloadData:
            download(task_args)
        elif ml_cube_args.mlcube_task == Task.Train:
            train(task_args)
        elif ml_cube_args.mlcube_task == Task.Kubernetes:
            download(task_args)
            train(task_args)
        else:
            raise ValueError(f"Unknown task: {task_args}")
    except Exception as err:
        logger.exception(err)


if __name__ == '__main__':
    main()
