# MLCube

MLCube is a project that reduces friction for machine learning by ensuring that models are easily portable and 
reproducible, e.g., between different stacks such as different clouds, between cloud and on-prem, etc.

Interested in getting started with MLCube? Follow the 
[Getting Started](https://mlcommons.github.io/mlcube/getting-started/) instructions, or watch the video below.

<div style="text-align: center" markdown="block">
[![Watch the video](https://img.youtube.com/vi/ByG24HmBLUM/0.jpg)](https://youtu.be/ByG24HmBLUM){style="align: center"}
</div>

## Installing MLCube

Create python environment
=== "Conda"
    ```shell
    conda create -n mlcube python=3.8
    conda activate mlcube
    ```

=== "VirtualEnv" 
    ```shell
    virtualenv --python=3.8 .mlcube
    source .mlcube/bin/activate
    ```

Install MLCube with docker and singularity runners
```shell
pip install mlcube mlcube-docker docker-singularity
```


## Usage Examples

Check out the [examples](https://github.com/mlcommons/mlcube_examples) for detailed examples.

## License
[MLCube](https://github.com/mlcommons/mlcube/) is licensed under the Apache License 2.0. 

See [LICENSE](https://github.com/mlcommons/mlcube/blob/master/LICENSE) for more information.

## Support

[Create a GitHub issue](https://github.com/mlcommons/mlcube/issues/new/choose)
