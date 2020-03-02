# MLBox

This is the MLBox Prototype. This is  still under construction, some parts probably dont work yet.

## Running Locally

```
cd mlbox/
python mlbox_local_run.py ../examples/transformer:downloaddata/default
python mlbox_local_run.py ../examples/transformer:preprocess/default
python mlbox_local_run.py ../examples/transformer:train/default
```

## Old Documentation (Ignore below)

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

```# NOTICE: This is not yet fully implemented. This will print a docker command simliar to what will be run.
cd mlbox
python mlbox_run.py ../examples/fake_model:train/small_batch
```

```# To override and specify different files, 
--log_file=/tmp/my_log_file
```

## Examples

Check out the [examples directory](examples) for detailed examples.
