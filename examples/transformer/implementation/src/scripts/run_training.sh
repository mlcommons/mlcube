#!/bin/bash

export PYTHONPATH=implementation/src/transformer:${PYTHONPATH}

python3 -m mlcube_transformer_main "$@"
