"""
https://www.tensorflow.org/tutorials/quickstart/beginner
"""

from __future__ import absolute_import, division, print_function, unicode_literals

# Disable GPUs - not all nodes used for testing have GPUs
import argparse
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''

import tensorflow as tf


def main(args):
  # Print TF version
  print("MNIST example (TensorFlow = {})".format(tf.__version__))

  # Get MNIST data set
  mnist = tf.keras.datasets.mnist
  (x_train, y_train), (x_test, y_test) = mnist.load_data()
  x_train, x_test = x_train / 255.0, x_test / 255.0

  # Create and compile a model
  model = tf.keras.models.Sequential([
    tf.keras.layers.Flatten(input_shape=(28, 28)),
    tf.keras.layers.Dense(128, activation='relu'),
    tf.keras.layers.Dropout(0.2),
    tf.keras.layers.Dense(10, activation='softmax')
  ])
  model.compile(optimizer=args.optimizer,
                loss='sparse_categorical_crossentropy',
                metrics=['accuracy'])

  # Train and evaluate
  model.fit(x_train, y_train, batch_size=args.batch_size, epochs=args.train_epochs)
  model.evaluate(x_test, y_test, verbose=2)


if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('--optimizer', required=False, type=str, default='adam',
                      help="Optimizer to use")
  parser.add_argument('--train_epochs', required=False, type=int, default=5,
                      help="Number of train epochs.")
  parser.add_argument('--batch_size', required=False, type=int, default=32,
                      help="Effective batch size.")

  main(parser.parse_args())
