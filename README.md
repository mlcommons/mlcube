# MLBox

This is the MLBox Prototype. This is  still under construction, some parts probably don't work yet.

## Installation

To install:

```sh
git clone https://github.com/xyhuang/mlbox.git
cd mlbox

pip install .
```

To uninstall:

```sh
pip uninstall mlbox
```

## Run an MLBox

TO run an example, such as our toy "fake model", 

```# To use the default values
mlbox local_run examples/fake_model:train/small_batch
```

```# To override and specify different files, 
mlbox local_run examples/fake_model:train/small_batch --log_file=/tmp/my_log_file
```

## Examples

Check out the [examples directory](examples) for detailed examples.
