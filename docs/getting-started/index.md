# Installation

Here is the step-by-step guide to install MLCube&reg; library and run simple MLCube cubes.

## Create a python environment

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

## Install MLCube Runners
Reference MLCube [runners](https://mlcommons.github.io/mlcube/getting-started/concepts/#runner) are distributed in
separate python packages.

=== "Docker"
    ```shell
    pip install mlcube-docker    
    ```

=== "Singularity"
    ```shell
    pip install mlcube-singularity    
    ```

=== "GCP (alpha)"
    ```shell
    pip install mlcube-gcp    
    ```

=== "K8S (alpha)"
    ```shell
    pip install mlcube-k8s    
    ```

=== "Kubeflow (alpha)"
    ```shell
    pip install mlcube-kubeflow    
    ```

=== "SSH (alpha)"
    ```shell
    pip install mlcube-ssh    
    ```

!!! warning
    [GCP](https://mlcommons.github.io/mlcube/runners/gcp-runner/) (Google Cloud Platform), 
    [K8S](https://mlcommons.github.io/mlcube/runners/kubernetes/) (Kubernetes), 
    [Kubeflow](https://mlcommons.github.io/mlcube/runners/kubeflow/) and 
    [SSH](https://mlcommons.github.io/mlcube/runners/ssh-runner/) runners are in early stages of development.
 
Check that the [docker runner](https://mlcommons.github.io/mlcube/runners/docker-runner/) has been installed.
```shell
mlcube config --get runners
```

Show MLCube [system settings](https://mlcommons.github.io/mlcube/getting-started/concepts/#system-settings).
```
mlcube config --list
```

!!! information
    This system settings file (`~/mlcube.yaml`) configures local MLCube runners. Documentation for MLCube runners 
    describes each of these parameters in details. A typical first step for enterprise environments that are usually 
    behind a firewall is to configure proxy servers.
    ```yaml
    platforms:
      docker:
        env_args:
          http_proxy: http://ADDRESS:PORT
          https_proxy: https://ADDRESS:PORT
        build_args:
          http_proxy: http://ADDRESS:PORT
          https_proxy: https://ADDRESS:PORT
    ```


## Explore with examples
A great way to learn about MLCube is try out the example MLCube cubes 
located in the [mlcube_examples](https://github.com/mlcommons/mlcube_examples) GitHub repository.
```shell
git clone https://github.com/mlcommons/mlcube_examples.git 
cd ./mlcube_examples
mlcube describe --mlcube ./mnist
```
