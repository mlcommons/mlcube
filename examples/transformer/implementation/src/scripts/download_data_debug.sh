#!/bin/bash

export PYTHONPATH=implementation/src/transformer:${PYTHONPATH}

python3 -m mlcube_download_main \
--raw_dir=workspace/data/translate_ende_raw
