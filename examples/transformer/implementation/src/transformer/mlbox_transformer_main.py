# Copyright 2018 MLBenchmark Group. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""Creates an estimator to train the Transformer model."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import logging
import os
import sys
import tempfile
import random
import numpy.random

from six.moves import xrange  # pylint: disable=redefined-builtin
import tensorflow as tf
import yaml

from mlperf_logging import mllog
from mlperf_logging.mllog import constants as mllog_const

import compute_bleu
import mlcube_constants as mlcube_const
import mlcube_model_params
from model import transformer
import translate
from utils import dataset
from utils import metrics
from utils import tokenizer

INF = 10000

mllogger = mllog.get_mllogger()


def model_fn(features, labels, mode, params):
  """Defines how to train, evaluate and predict from the transformer model."""
  with tf.variable_scope("model"):
    inputs, targets = features, labels

    # Create model and get output logits.
    model = transformer.Transformer(params, mode == tf.estimator.ModeKeys.TRAIN)

    output = model(inputs, targets)

    # When in prediction mode, the labels/targets is None. The model output
    # is the prediction
    if mode == tf.estimator.ModeKeys.PREDICT:
      return tf.estimator.EstimatorSpec(
          tf.estimator.ModeKeys.PREDICT,
          predictions=output)

    logits = output

    # Calculate model loss.
    xentropy, weights = metrics.padded_cross_entropy_loss(
        logits, targets, params.label_smoothing, params.vocab_size)
    loss = tf.reduce_sum(xentropy * weights) / tf.reduce_sum(weights)

    if mode == tf.estimator.ModeKeys.EVAL:
      return tf.estimator.EstimatorSpec(
          mode=mode, loss=loss, predictions={"predictions": logits},
          eval_metric_ops=metrics.get_eval_metrics(logits, labels, params))
    else:
      train_op = get_train_op(loss, params)
      return tf.estimator.EstimatorSpec(mode=mode, loss=loss, train_op=train_op)


def get_learning_rate(learning_rate, hidden_size, learning_rate_warmup_steps):
  """Calculate learning rate with linear warmup and rsqrt decay."""
  with tf.name_scope("learning_rate"):
    warmup_steps = tf.to_float(learning_rate_warmup_steps)
    step = tf.to_float(tf.train.get_or_create_global_step())

    learning_rate *= (hidden_size ** -0.5)
    # Apply linear warmup
    learning_rate *= tf.minimum(1.0, step / warmup_steps)
    # Apply rsqrt decay
    learning_rate *= tf.rsqrt(tf.maximum(step, warmup_steps))

    # Save learning rate value to TensorBoard summary.
    tf.summary.scalar("learning_rate", learning_rate)

    return learning_rate


def get_train_op(loss, params):
  """Generate training operation that updates variables based on loss."""
  with tf.variable_scope("get_train_op"):
    mllogger.event(key=mllog_const.OPT_LR_WARMUP_STEPS,
                   value=params.learning_rate_warmup_steps)
    learning_rate = get_learning_rate(
        params.learning_rate, params.hidden_size,
        params.learning_rate_warmup_steps)

    # Create optimizer. Use LazyAdamOptimizer from TF contrib, which is faster
    # than the TF core Adam optimizer.
    mllogger.event(key=mllog_const.OPT_NAME,
                   value=mllog_const.LAZY_ADAM)
    mllogger.event(key=mllog_const.OPT_ADAM_BETA_1,
                   value=params.optimizer_adam_beta1)
    mllogger.event(key=mllog_const.OPT_ADAM_BETA_2,
                   value=params.optimizer_adam_beta2)
    mllogger.event(key=mllog_const.OPT_ADAM_EPSILON,
                   value=params.optimizer_adam_epsilon)
    optimizer = tf.contrib.opt.LazyAdamOptimizer(
        learning_rate,
        beta1=params.optimizer_adam_beta1,
        beta2=params.optimizer_adam_beta2,
        epsilon=params.optimizer_adam_epsilon)

    # Calculate and apply gradients using LazyAdamOptimizer.
    global_step = tf.train.get_global_step()
    tvars = tf.trainable_variables()
    gradients = optimizer.compute_gradients(
        loss, tvars, colocate_gradients_with_ops=True)
    train_op = optimizer.apply_gradients(
        gradients, global_step=global_step, name="train")

    # Save gradient norm to Tensorboard
    tf.summary.scalar("global_norm/gradient_norm",
                      tf.global_norm(list(zip(*gradients))[0]))

    return train_op


def translate_and_compute_bleu(estimator, subtokenizer, bleu_source, bleu_ref):
  """Translate file and report the cased and uncased bleu scores."""
  # Create temporary file to store translation.
  tmp = tempfile.NamedTemporaryFile(delete=False)
  tmp_filename = tmp.name

  translate.translate_file(
      estimator, subtokenizer, bleu_source, output_file=tmp_filename,
      print_all_translations=False)

  # Compute uncased and cased bleu scores.
  uncased_score = compute_bleu.bleu_wrapper(bleu_ref, tmp_filename, False)
  cased_score = compute_bleu.bleu_wrapper(bleu_ref, tmp_filename, True)
  os.remove(tmp_filename)
  return uncased_score, cased_score


def get_global_step(estimator):
  """Return estimator's last checkpoint."""
  return int(estimator.latest_checkpoint().split("-")[-1])


def evaluate_and_log_bleu(estimator, bleu_writer, bleu_source, bleu_ref):
  """Calculate and record the BLEU score."""
  subtokenizer = tokenizer.Subtokenizer(
      os.path.join(FLAGS.data_dir, FLAGS.vocab_file))

  uncased_score, cased_score = translate_and_compute_bleu(
      estimator, subtokenizer, bleu_source, bleu_ref)

  print("Bleu score (uncased):", uncased_score)
  print("Bleu score (cased):", cased_score)

  summary = tf.Summary(value=[
      tf.Summary.Value(tag="bleu/uncased", simple_value=uncased_score),
      tf.Summary.Value(tag="bleu/cased", simple_value=cased_score),
  ])

  bleu_writer.add_summary(summary, get_global_step(estimator))
  bleu_writer.flush()
  return uncased_score, cased_score


def train_schedule(
    estimator, train_eval_iterations, single_iteration_train_steps=None,
    single_iteration_train_epochs=None, bleu_source=None, bleu_ref=None,
    bleu_threshold=None):
  """Train and evaluate model, and optionally compute model's BLEU score.

  **Step vs. Epoch vs. Iteration**

  Steps and epochs are canonical terms used in TensorFlow and general machine
  learning. They are used to describe running a single process (train/eval):
    - Step refers to running the process through a single or batch of examples.
    - Epoch refers to running the process through an entire dataset.

  E.g. training a dataset with 100 examples. The dataset is
  divided into 20 batches with 5 examples per batch. A single training step
  trains the model on one batch. After 20 training steps, the model will have
  trained on every batch in the dataset, or, in other words, one epoch.

  Meanwhile, iteration is used in this implementation to describe running
  multiple processes (training and eval).
    - A single iteration:
      1. trains the model for a specific number of steps or epochs.
      2. evaluates the model.
      3. (if source and ref files are provided) compute BLEU score.

  This function runs through multiple train+eval+bleu iterations.

  Args:
    estimator: tf.Estimator containing model to train.
    train_eval_iterations: Number of times to repeat the train+eval iteration.
    single_iteration_train_steps: Number of steps to train in one iteration.
    single_iteration_train_epochs: Number of epochs to train in one iteration.
    bleu_source: File containing text to be translated for BLEU calculation.
    bleu_ref: File containing reference translations for BLEU calculation.
    bleu_threshold: minimum BLEU score before training is stopped.

  Raises:
    ValueError: if both or none of single_iteration_train_steps and
      single_iteration_train_epochs were defined.
  """
  # Ensure that exactly one of single_iteration_train_steps and
  # single_iteration_train_epochs is defined.
  if single_iteration_train_steps is None:
    if single_iteration_train_epochs is None:
      raise ValueError(
          "Exactly one of single_iteration_train_steps or "
          "single_iteration_train_epochs must be defined. Both were none.")
  else:
    if single_iteration_train_epochs is not None:
      raise ValueError(
          "Exactly one of single_iteration_train_steps or "
          "single_iteration_train_epochs must be defined. Both were defined.")

  evaluate_bleu = bleu_source is not None and bleu_ref is not None

  # Print out training schedule
  print("Training schedule:")
  if single_iteration_train_epochs is not None:
    print("\t1. Train for %d epochs." % single_iteration_train_epochs)
  else:
    print("\t1. Train for %d steps." % single_iteration_train_steps)
  print("\t2. Evaluate model.")
  if evaluate_bleu:
    print("\t3. Compute BLEU score.")
    if bleu_threshold is not None:
      print("Repeat above steps until the BLEU score reaches", bleu_threshold)
  if not evaluate_bleu or bleu_threshold is None:
    print("Repeat above steps %d times." % train_eval_iterations)

  if evaluate_bleu:
    # Set summary writer to log bleu score.
    bleu_writer = tf.summary.FileWriter(
        os.path.join(estimator.model_dir, FLAGS.bleu_dir))
    if bleu_threshold is not None:
      # Change loop stopping condition if bleu_threshold is defined.
      train_eval_iterations = INF

  # Loop training/evaluation/bleu cycles
  for i in xrange(train_eval_iterations):
    print("Starting iteration", i + 1)
    if single_iteration_train_epochs is not None:
        first_epoch_num = i * single_iteration_train_epochs + 1
    else:
        first_epoch_num = None
    mllogger.start(
        key=mllog_const.BLOCK_START,
        metadata={mllog_const.FIRST_EPOCH_NUM: first_epoch_num,
                  mllog_const.EPOCH_COUNT: single_iteration_train_epochs})

    # Train the model for single_iteration_train_steps or until the input fn
    # runs out of examples (if single_iteration_train_steps is None).
    estimator.train(dataset.train_input_fn, steps=single_iteration_train_steps)

    mllogger.start(
        key=mllog_const.EVAL_START,
        metadata={mllog_const.EPOCH_NUM: first_epoch_num})
    eval_results = estimator.evaluate(dataset.eval_input_fn)
    print("Evaluation results (iter %d/%d):" % (i + 1, train_eval_iterations),
          eval_results)

    if evaluate_bleu:
      uncased_score, _ = evaluate_and_log_bleu(
          estimator, bleu_writer, bleu_source, bleu_ref)
      mllogger.event(key=mllog_const.EVAL_ACCURACY, value=uncased_score,
          metadata={mllog_const.EPOCH_NUM: first_epoch_num})
      if bleu_threshold is not None and uncased_score > bleu_threshold:
        bleu_writer.close()
        mllogger.end(key=mllog_const.EVAL_STOP,
                      metadata={mllog_const.EPOCH_NUM: first_epoch_num})
        mllogger.end(
            key=mllog_const.BLOCK_STOP,
            metadata={mllog_const.FIRST_EPOCH_NUM: first_epoch_num,
                      mllog_const.EPOCH_COUNT: single_iteration_train_epochs})
        break
    mllogger.end(key=mllog_const.EVAL_STOP,
        metadata={mllog_const.EPOCH_NUM: first_epoch_num})
    mllogger.end(
        key=mllog_const.BLOCK_STOP,
        metadata={mllog_const.FIRST_EPOCH_NUM: first_epoch_num,
                  mllog_const.EPOCH_COUNT: single_iteration_train_epochs})


def main(_):
  if not tf.gfile.Exists(FLAGS.mlperf_log_dir):
    print("Creating directory %s" % FLAGS.mlperf_log_dir)
    tf.gfile.MakeDirs(FLAGS.mlperf_log_dir)
  mllog.config(
    filename=os.path.join(FLAGS.mlperf_log_dir, "mlperf_compliance.log"),
    root_dir=os.path.normpath(os.path.dirname(os.path.realpath(__file__))))

  mllogger.start(key=mllog_const.INIT_START)
  # Set logging level to INFO to display training progress (logged by the
  # estimator)
  tf.logging.set_verbosity(tf.logging.INFO)

  # Set random seed.
  if FLAGS.random_seed is None:
    raise Exception('No Random seed given')
  print('Setting random seed = ', FLAGS.random_seed)
  seed = FLAGS.random_seed
  random.seed(seed)
  tf.set_random_seed(seed)
  numpy.random.seed(seed)

  # Determine training schedule based on flags.
  if FLAGS.train_steps is not None and FLAGS.train_epochs is not None:
    raise ValueError("Both --train_steps and --train_epochs were set. Only one "
                     "may be defined.")
  if FLAGS.train_steps is None and FLAGS.train_epochs is None:
    FLAGS.train_epochs = mlcube_const.DEFAULT_TRAIN_EPOCHS

  params = mlcube_model_params.MLCubeTransformerParams(FLAGS)

  # Make sure that the BLEU source and ref files if set
  if FLAGS.bleu_source is not None and FLAGS.bleu_ref is not None:
    if not tf.gfile.Exists(FLAGS.bleu_source):
      raise ValueError("BLEU source file %s does not exist" % FLAGS.bleu_source)
    if not tf.gfile.Exists(FLAGS.bleu_ref):
      raise ValueError("BLEU source file %s does not exist" % FLAGS.bleu_ref)

  mllogger.end(key=mllog_const.INIT_STOP)
  mllogger.start(key=mllog_const.RUN_START)

  estimator = tf.estimator.Estimator(
      model_fn=model_fn, model_dir=FLAGS.model_dir, params=params)
  train_schedule(
      estimator, params.train_eval_iterations, params.single_iteration_train_steps,
      params.single_iteration_train_epochs, FLAGS.bleu_source, FLAGS.bleu_ref,
      FLAGS.bleu_threshold)

  mllogger.end(key=mllog_const.RUN_STOP)


if __name__ == "__main__":
  mlcube_parser = argparse.ArgumentParser()

  mlcube_parser.add_argument(
      "--parameter_file", type=str, default=None,
      help="Parameter file to use. The parameter file should be a yaml file "
           "that serves as command line arguments.",
      metavar="<PF>")

  mlcube_parser.add_argument(
      "--data_dir", type=str, default="/tmp/translate_ende",
      help="[default: %(default)s] Directory containing training and "
           "evaluation data, and vocab file used for encoding.",
      metavar="<DD>")
  mlcube_parser.add_argument(
      "--vocab_file", type=str, default=mlcube_const.VOCAB_FILE,
      help="[default: %(default)s] Name of vocabulary file.",
      metavar="<VF>")
  mlcube_parser.add_argument(
      "--model_dir", type=str, default="/tmp/transformer_model",
      help="[default: %(default)s] Directory to save Transformer model "
           "training checkpoints",
      metavar="<MD>")
  mlcube_parser.add_argument(
      "--bleu_dir", type=str, default="/tmp/bleu",
      help="[default: %(default)s] Directory to save BLEU scores."
  )
  mlcube_parser.add_argument(
      "--mlperf_log_dir", type=str, default="/tmp/mlperf_log",
      help="[default: %(default)s] Directory for mlperf log files.", metavar="<LD>"
  )

  # parser.add_argument(
  #     "--num_cpu_cores", "-nc", type=int, default=4,
  #     help="[default: %(default)d] Number of CPU cores to use in the input "
  #          "pipeline.",
  #     metavar="<NC>")

  # # Flags for training with epochs. (default)
  # parser.add_argument(
  #     "--train_epochs", "-te", type=int, default=None,
  #     help="The number of epochs used to train. If both --train_epochs and "
  #          "--train_steps are not set, the model will train for %d epochs." %
  #     mlcube_const.DEFAULT_TRAIN_EPOCHS,
  #     metavar="<TE>")
  # parser.add_argument(
  #     "--epochs_between_eval", "-ebe", type=int, default=1,
  #     help="[default: %(default)s] The number of training epochs to run "
  #          "between evaluations.",
  #     metavar="<EBE>")

  # # Flags for training with steps (may be used for debugging)
  # parser.add_argument(
  #     "--train_steps", "-ts", type=int, default=None,
  #     help="Total number of training steps. If both --train_epochs and "
  #          "--train_steps are not set, the model will train for %d epochs." %
  #     mlcube_const.DEFAULT_TRAIN_EPOCHS,
  #     metavar="<TS>")
  # parser.add_argument(
  #     "--steps_between_eval", "-sbe", type=int, default=1000,
  #     help="[default: %(default)s] Number of training steps to run between "
  #          "evaluations.",
  #     metavar="<SBE>")

  # # BLEU score computation
  # parser.add_argument(
  #     "--bleu_source", "-bs", type=str, default=None,
  #     help="Path to source file containing text translate when calculating the "
  #          "official BLEU score. Both --bleu_source and --bleu_ref must be "
  #          "set. The BLEU score will be calculated during model evaluation.",
  #     metavar="<BS>")
  # parser.add_argument(
  #     "--bleu_ref", "-br", type=str, default=None,
  #     help="Path to file containing the reference translation for calculating "
  #          "the official BLEU score. Both --bleu_source and --bleu_ref must be "
  #          "set. The BLEU score will be calculated during model evaluation.",
  #     metavar="<BR>")
  # parser.add_argument(
  #     "--bleu_threshold", "-bt", type=float, default=None,
  #     help="Stop training when the uncased BLEU score reaches this value. "
  #          "Setting this overrides the total number of steps or epochs set by "
  #          "--train_steps or --train_epochs.",
  #     metavar="<BT>")

  # parser.add_argument(
  #     "--random_seed", "-rs", type=int, default=None,
  #     help="the random seed to use", metavar="<SEED>")

  # # model parameters
  # parser.add_argument(
  #     "--batch_size", type=int, default=2048,
  #     help="Maximum number of tokens per batch of examples.", metavar="<BS>")
  # parser.add_argument(
  #     "--max_length", type=int, default=256,
  #     help="Maximum number of tokens per example.", metavar="<ML>")
  # parser.add_argument(
  #     "--initializer_gain", type=float, default=1.0,
  #     help="Gain value in trainable variable initialization.", metavar="<IG>")
  # parser.add_argument(
  #     "--vocab_size", type=int, default=33708,
  #     help="Number of tokens defined in the vocabulary file.", metavar="<VS>")
  # parser.add_argument(
  #     "--hidden_size", type=int, default=512,
  #     help="Model dimension in the hidden layers.", metavar="<HS>")
  # parser.add_argument(
  #     "--num_hidden_layers", type=int, default=6,
  #     help="Number of layers in the encoder and decoder stacks.", metavar="<NHL>")
  # parser.add_argument(
  #     "--num_heads", type=int, default=8,
  #     help="Number of heads to use in multi-headed attention.", metavar="<NH>")
  # parser.add_argument(
  #     "--filter_size", type=int, default=2048,
  #     help="Inner layer dimensionality in the feedforward network.", metavar="<FS>")
  # parser.add_argument(
  #     "--layer_postprocess_dropout", type=float, default=0.1,
  #     help="Layer postprocess dropout.", metavar="<LPD>")
  # parser.add_argument(
  #     "--attention_dropout", type=float, default=0.1,
  #     help="Attention dropout.", metavar="<AD>")
  # parser.add_argument(
  #     "--relu_dropout", type=float, default=0.1,
  #     help="Relu droupout.", metavar="<RD>")
  # parser.add_argument(
  #     "--label_smoothing", type=float, default=0.1,
  #     help="Label smoothing.", metavar="<LS>")
  # parser.add_argument(
  #     "--learning_rate", type=float, default=2.0,
  #     help="Learning rate.", metavar="<LR>")
  # parser.add_argument(
  #     "--learning_rate_decay_rate", type=float, default=1.0,
  #     help="Learning rate decay rate", metavar="<LRD>")
  # parser.add_argument(
  #     "--learning_rate_warmup_steps", type=int, default=16000,
  #     help="Learning rate warmup steps", metavar="<LRW>")
  # parser.add_argument(
  #     "--optimizer_adam_beta1", type=float, default=0.9,
  #     help="Adam optimizer parameter beta1", metavar="<OAB1>")
  # parser.add_argument(
  #     "--optimizer_adam_beta2", type=float, default=0.997,
  #     help="Adam optimizer parameter beta2", metavar="<OAB2>")
  # parser.add_argument(
  #     "--optimizer_adam_epsilon", type=float, default=1e-09,
  #     help="Adam optimizer parameter epsilon", metavar="<OAE>")
  # parser.add_argument(
  #     "--extra_decode_length", type=int, default=50,
  #     help="Prediction parameter: extra decode length", metavar="<EDL>")
  # parser.add_argument(
  #     "--beam_size", type=int, default=4,
  #     help="Prediction parameter: beam size", metavar="<BS>")
  # parser.add_argument(
  #     "--alpha", type=float, default=0.6,
  #     help="Prediction parameter: alpha, for calculating length " +
  #          "normalization in beam search",
  #     metavar="<ALPHA>")

  FLAGS, unparsed = mlcube_parser.parse_known_args()

  # Load parameter file and combile flags with those set in command line.
  # The flags set in command line take higher priority.
  if FLAGS.parameter_file is not None:
    try:
      with open(FLAGS.parameter_file, "r") as f:
        parameters = yaml.load(f) or {}
      for key, val in parameters.items():
        if getattr(FLAGS, key, None) is None:
          setattr(FLAGS, key, val)
    except Exception:
      print("Failed to load parameter file.")
      raise

  tf.app.run(main=main, argv=[sys.argv[0]] + unparsed)
