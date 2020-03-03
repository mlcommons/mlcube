# MNIST MLBox example

An MNIST MLBox example that is compatible with `mlbox_local_run.py` runner.

MLPerf implements two tasks - `downloaddata` and `train`:
```bash
# Download data
python ./mlbox_local_run.py ../examples/mnist:download/default

# Train MNIST model. 
python ./mlbox_local_run.py ../examples/mnist:train/default
```
