# MLBox

This is the MLBox Prototype. This is  still under construction, some parts probably don't work yet.

MLBox is a contract for packaging ML tasks and models which enables models, experiments and benchmarks to be shared and reproduced. Designed to be simple and extensible, MLBox aims to supports a wide variety of ML tasks, products and frameworks.

## Running Locally

```
cd mlbox/
python mlbox_local_run.py ../examples/transformer:downloaddata/default
python mlbox_local_run.py ../examples/transformer:preprocess/default
python mlbox_local_run.py ../examples/transformer:train/default
```

## Examples

Check out the [examples directory](examples) for detailed examples.
