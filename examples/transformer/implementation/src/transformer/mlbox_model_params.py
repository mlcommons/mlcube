"""Defines Transformer model parameters."""

class MLBoxTransformerParams(object):
  """Parameters for the base Transformer model."""
  def __init__(self, flags):
    # Input params
    self.batch_size = flags.batch_size  # Maximum number of tokens per batch of examples.
    self.max_length = flags.max_length  # Maximum number of tokens per example.

    # Model params
    self.initializer_gain = flags.initializer_gain  # Used in trainable variable initialization.
    self.vocab_size = flags.vocab_size  # Number of tokens defined in the vocabulary file.
    self.hidden_size = flags.hidden_size  # Model dimension in the hidden layers.
    self.num_hidden_layers = flags.num_hidden_layers  # Number of layers in the encoder and decoder stacks.
    self.num_heads = flags.num_heads  # Number of heads to use in multi-headed attention.
    self.filter_size = flags.filter_size  # Inner layer dimensionality in the feedforward network.

    # Dropout values (only used when training)
    self.layer_postprocess_dropout = flags.layer_postprocess_dropout
    self.attention_dropout = flags.attention_dropout
    self.relu_dropout = flags.relu_dropout

    # Training params
    self.label_smoothing = flags.label_smoothing
    self.learning_rate = flags.learning_rate
    self.learning_rate_decay_rate = flags.learning_rate_decay_rate
    self.learning_rate_warmup_steps = flags.learning_rate_warmup_steps

    # Optimizer params
    self.optimizer_adam_beta1 = flags.optimizer_adam_beta1
    self.optimizer_adam_beta2 = flags.optimizer_adam_beta2
    self.optimizer_adam_epsilon = flags.optimizer_adam_epsilon

    # Default prediction params
    self.extra_decode_length = flags.extra_decode_length
    self.beam_size = flags.beam_size
    self.alpha = flags.alpha  # used to calculate length normalization in beam search

    if flags.train_steps is not None:
      self.train_eval_iterations = flags.train_steps // flags.steps_between_eval
      self.single_iteration_train_steps = flags.steps_between_eval
      self.single_iteration_train_epochs = None
    else:
      self.train_eval_iterations = flags.train_epochs // flags.epochs_between_eval
      self.single_iteration_train_steps = None
      self.single_iteration_train_epochs = flags.epochs_between_eval
    self.repeat_dataset = self.single_iteration_train_epochs

    # Add flag-defined parameters to params object
    self.data_dir = flags.data_dir
    self.num_cpu_cores = flags.num_cpu_cores
    self.epochs_between_eval = flags.epochs_between_eval
