#!/bin/bash

export PYTHONPATH=implementation/src/transformer:${PYTHONPATH}

python3 -m mlbox_preprocess_main \
--data_dir=workspace/data/translate_ende \
--raw_dir=workspace/data/translate_ende_raw
