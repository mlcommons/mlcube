# MLBox

This is the MLBox Prototype. This is  still under construction, some parts probably don't work yet, or may have unexpected/inconsistent behaviours.

## Get MLBox

### Downloading

You can get the MLBox project as a zip file for direct download from https://github.com/mlperf/mlbox/archive/master.zip

Expand this locally on the filesystem in your location of choice.

### Git Clone

You can clone the MLBox project using Git from https://github.com/mlperf/mlbox.git

```git clone https://github.com/mlperf/mlbox.git```

## Installing

After downloading or cloning, you can install:

```sh
cd mlbox
pip install .
```

To uninstall:

```sh
pip uninstall mlbox
```

## Running Locally

### Toy Implementation

To run the toy implementation (aka "fake model"): 

```# NOTICE: This is not yet fully implemented. This will print a docker command simliar to what will be run.
cd mlbox
python mlbox_run.py ../examples/fake_model:train/small_batch
```

```# To override and specify different files, 
--log_file=/tmp/my_log_file
```

### Transformer Implementation

To run the transformer implementation: 

```
cd mlbox/
python mlbox_local_run.py ../examples/transformer:downloaddata/default
python mlbox_local_run.py ../examples/transformer:preprocess/default
python mlbox_local_run.py ../examples/transformer:train/default
```

## Usage Examples

Check out the [examples directory](examples) for detailed examples.

## License
mlperf/mlbox is licensed under the Apache License 2.0. 

See https://github.com/mlperf/mlbox/blob/master/LICENSE for more information

## Support

Create an issue https://github.com/mlperf/mlbox/issues/new/choose
