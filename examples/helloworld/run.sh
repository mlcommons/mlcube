#!/bin/bash

DATA_DIR=/workspace/data
OUTPUT_DIR=/workspace/output
LOG_DIR=/workspace/log

input_file=${DATA_DIR}/hello.txt
output_file=${OUTPUT_DIR}/helloworld.txt
log_file=${LOG_DIR}/hellolog.log

sed 's/Hello/Hello World!/' ${input_file} > ${output_file} && \
  echo "[INFO] Read input: ${input_file}. Written output: ${output_file}." > ${log_file}
