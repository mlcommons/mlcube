### Data Processing

# Data sources for training/evaluating the transformer translation model.
# If any of the training sources are changed, then either:
#   1) use the flag `--search` to find the best min count or
#   2) update the _TRAIN_DATA_MIN_COUNT constant.
# min_count is the minimum number of times a token must appear in the data
# before it is added to the vocabulary. "Best min count" refers to the value
# that generates a vocabulary set that is closest in size to _TARGET_VOCAB_SIZE.
TRAIN_DATA_SOURCES = [
  {
    "url": "http://data.statmt.org/wmt17/translation-task/"
           "training-parallel-nc-v12.tgz",
    "input": "news-commentary-v12.de-en.en",
    "target": "news-commentary-v12.de-en.de",
  },
  {
    "url": "http://www.statmt.org/wmt13/training-parallel-commoncrawl.tgz",
    "input": "commoncrawl.de-en.en",
    "target": "commoncrawl.de-en.de",
  },
  {
    "url": "http://www.statmt.org/wmt13/training-parallel-europarl-v7.tgz",
    "input": "europarl-v7.de-en.en",
    "target": "europarl-v7.de-en.de",
  },
]

# Use pre-defined minimum count to generate subtoken vocabulary.
TRAIN_DATA_MIN_COUNT = 6

EVAL_DATA_SOURCES = [
  {
    "url": "https://raw.githubusercontent.com/tensorflow/models/v1.13.0/"
           "official/transformer/test_data/",
    "input": "newstest2014.en",
    "target": "newstest2014.de",
  }
]

# Vocabulary constants
TARGET_VOCAB_SIZE = 32768  # Number of subtokens in the vocabulary list.
TARGET_THRESHOLD = 327  # Accept vocabulary if size is within this threshold
VOCAB_FILE = "vocab.ende.%d" % TARGET_VOCAB_SIZE

# Number of files to split train and evaluation data
TRAIN_SHARDS = 100
EVAL_SHARDS = 1


### Training

DEFAULT_TRAIN_EPOCHS = 10
