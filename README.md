# MLBox

This is the MLBox 📦 Prototype. This is  still under construction, some parts probably don't work yet, or may have unexpected/inconsistent behaviours.

[Documentation](https://mlperf.github.io/mlbox)

## Get MLBox

### Direct Download

Directly download the project

```
wget -O mlbox-master.zip https://github.com/mlperf/mlbox/archive/master.zip
unzip mlbox-master.zip -d mlbox
rm -r mlbox-master.zip
cd mlbox
```

### Git Clone

You can clone the MLBox project using Git

```
git clone https://github.com/mlperf/mlbox.git
cd mlbox
```

## Installing

After downloading or cloning, from the root of the project directory you can install:

```sh
pip install .
```

To uninstall:

```sh
pip uninstall mlbox
```

## Running Locally

### Toy Implementation

To run the toy implementation (aka "fake model"): 

!!! notice
    This is not yet fully implemented. This will print a docker command simliar to what will be run.
    ```
    cd mlbox
    python mlbox_run.py ../examples/fake_model:train/small_batch
    ```

    To override and specify different files:
    ``` 
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
[MLBox](https://github.com/mlperf/mlbox/) is licensed under the Apache License 2.0. 

See [LICENSE](https://github.com/mlperf/mlbox/blob/master/LICENSE) for more information.

## Support

[Create a GitHub issue](https://github.com/mlperf/mlbox/issues/new/choose)
