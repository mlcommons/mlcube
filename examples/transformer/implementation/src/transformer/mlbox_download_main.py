"""Download and preprocess WMT17 ende training and evaluation datasets."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import os
import random
import sys
import tarfile
import urllib.request
import logging

import tensorflow as tf
import yaml

import mlcube_constants as constants


logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
logging.getLogger().setLevel(logging.INFO)


def find_file(path, filename, max_depth=5):
  """Returns full filepath if the file is in path or a subdirectory."""
  for root, dirs, files in os.walk(path):
    if filename in files:
      return os.path.join(root, filename)

    # Don't search past max_depth
    depth = root[len(path) + 1:].count(os.sep)
    if depth > max_depth:
      del dirs[:]  # Clear dirs
  return None


###############################################################################
# Download and extraction functions
###############################################################################
def get_raw_files(raw_dir, data_source):
  """Return raw files from source. Downloads/extracts if needed.

  Args:
    raw_dir: string directory to store raw files
    data_source: dictionary with
      {"url": url of compressed dataset containing input and target files
       "input": file with data in input language
       "target": file with data in target language}

  Returns:
    dictionary with
      {"inputs": list of files containing data in input language
       "targets": list of files containing corresponding data in target language
      }
  """
  raw_files = {
      "inputs": [],
      "targets": [],
  }  # keys
  for d in data_source:
    if d["url"].endswith("/"): # the url is a dir and not a compressed file
      input_file = download_from_url(raw_dir, d["url"] + d["input"])
      target_file = download_from_url(raw_dir, d["url"] + d["target"])
    else:
      input_file, target_file = download_and_extract(
          raw_dir, d["url"], d["input"], d["target"])
    raw_files["inputs"].append(input_file)
    raw_files["targets"].append(target_file)
  return raw_files


def download_report_hook(count, block_size, total_size):
  """Report hook for download progress.

  Args:
    count: current block number
    block_size: block size
    total_size: total size
  """
  percent = int(count * block_size * 100 / total_size)
  print("\r%d%%" % percent + " completed", end="\r")


def download_from_url(path, url):
  """Download content from a url.

  Args:
    path: string directory where file will be downloaded
    url: string url

  Returns:
    Full path to downloaded file
  """
  filename = url.split("/")[-1]
  found_file = find_file(path, filename, max_depth=0)
  if found_file is None:
    filename = os.path.join(path, filename)
    logging.info("Downloading from %s to %s." % (url, filename))
    inprogress_filepath = filename + ".incomplete"
    inprogress_filepath, _ = urllib.request.urlretrieve(
        url, inprogress_filepath, reporthook=download_report_hook)
    # Print newline to clear the carriage return from the download progress.
    print()
    tf.gfile.Rename(inprogress_filepath, filename)
    return filename
  else:
    logging.info("Already downloaded: %s (at %s)." % (url, found_file))
    return found_file


def download_and_extract(path, url, input_filename, target_filename):
  """Extract files from downloaded compressed archive file.

  Args:
    path: string directory where the files will be downloaded
    url: url containing the compressed input and target files
    input_filename: name of file containing data in source language
    target_filename: name of file containing data in target language

  Returns:
    Full paths to extracted input and target files.

  Raises:
    OSError: if the the download/extraction fails.
  """
  logging.info('Downloading and extracting data to: %s' % path)
  # Check if extracted files already exist in path
  input_file = find_file(path, input_filename)
  target_file = find_file(path, target_filename)
  if input_file and target_file:
    logging.info("Already downloaded and extracted %s." % url)
    return input_file, target_file

  # Download archive file if it doesn't already exist.
  compressed_file = download_from_url(path, url)

  # Extract compressed files
  logging.info("Extracting %s." % compressed_file)
  with tarfile.open(compressed_file, "r:gz") as corpus_tar:
    corpus_tar.extractall(path)

  # Return filepaths of the requested files.
  input_file = find_file(path, input_filename)
  target_file = find_file(path, target_filename)

  if input_file and target_file:
    return input_file, target_file

  raise OSError("Download/extraction failed for url %s to path %s" %
                (url, path))


def make_dir(path):
  if not tf.gfile.Exists(path):
    tf.logging.info("Creating directory %s" % path)
    tf.gfile.MakeDirs(path)


def main(unused_argv):
  """Obtain training and evaluation data for the Transformer model."""
  make_dir(FLAGS.raw_dir)

  # Get paths of download/extracted training and evaluation files.
  print("Downloading data from source")
  train_files = get_raw_files(FLAGS.raw_dir, constants.TRAIN_DATA_SOURCES)
  eval_files = get_raw_files(FLAGS.raw_dir, constants.EVAL_DATA_SOURCES)


if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  # parser.add_argument(
  #     "--parameter_file", "-pf", type=str, default=None,
  #     help="Parameter file to use. The parameter file should be a yaml file "
  #          "that serves as an alternative of command line arguments. If a "
  #          "parameter is set in both parameter file and command line, the "
  #          "value set in command line will be used.",
  #     metavar="<PF>")
  parser.add_argument(
      "--raw_dir", "-rd", type=str, default="/tmp/translate_ende_raw",
      help="[default: %(default)s] Path where the raw data will be downloaded "
           "and extracted.",
      metavar="<RD>")

  FLAGS, unparsed = parser.parse_known_args()

  # Load parameter file and combile flags with those set in command line.
  # The flags set in command line take higher priority.
  #if FLAGS.parameter_file is not None:
  #  try:
  #    with open(FLAGS.parameter_file, "r") as f:
  #      parameters = yaml.load(f) or {}
  #    for key, val in parameters.items():
  #      if getattr(FLAGS, key, None) is None:
  #        setattr(FLAGS, key, val)
  #  except Exception:
  #    print("Failed to load parameter file.")
  #    raise

  main(sys.argv)
