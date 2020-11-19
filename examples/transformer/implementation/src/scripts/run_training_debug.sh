#!/bin/bash

export PYTHONPATH=implementation/src/transformer:${PYTHONPATH}

python3 -m mlcube_transformer_main \
--mlperf_log_dir=workspace/log \
--data_dir=workspace/data/translate_ende \
--model_dir=workspace/model \
--bleu_source=workspace/data/translate_ende_raw/newstest2014.en \
--bleu_ref=workspace/data/translate_ende_raw/newstest2014.de \
--parameter_file=tasks/train/debug.parameters.yaml
