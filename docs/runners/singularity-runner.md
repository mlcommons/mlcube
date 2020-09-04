# Singularity Runner
Singularity runner uses singularity to run MLBoxes. It supports two mandatory commands - `configure` and `run` with
standard arguments - `mlbox`, `platform` and `task`. Singularity platform configuration is used to configure Singularity
runner.


## Platform Configuration File
Singularity platform configuration file is a YAML file that follows `mlbox_singularity` ML schema. The configuration
file for the reference MNIST MLBox is the following:
```yaml
schema_version: 1.0.0
schema_type: mlbox_singularity

image: /opt/singularity/mlperf_mlbox_mnist-0.01.simg   # Path to or name of a Singularity image.
```

The `image` field above is a path to a singularity container. It is relative to `{MLBOX_ROOT}/workspace`:
- By default, containers are stored in `{MLBOX_ROOT}/workspace` if image is a file name.
- If it is a relative path, it is relative to `{MLBOX_ROOT}/workspace`.
- Absolute paths (starting with /) are used as is.

In the example above, Singularity image is stored in the directory outside of the `{MLBOX_ROOT}` to avoid copying it
back to the user host when using runners such as SSH.


## Build command
Singularity runner uses `{MLBOX_ROOT}/build` directory as the build context directory. This implies that all files that
must be packaged in a singularity image, must be located in that directory, including source files, python requirements,
resource files, ML models etc. The singularity recipe must have the standard name `Singularity.recipe`.

Singularity runner under the hood runs the following command line:  
```
cd {build_path}; singularity build --fakeroot {image_path} Singularity.recipe
```  
where:  
- `{build_path}` is `{MLBOX_ROOT}/build` root directory.  
- `{image_path}` is the path to Singularity image that is computed as described above. 


## Run command
Singularity runner runs the following command:    
```
singularity run {volumes} {image_path} {args}
```  
where:    
- `{volumes}` are the mount points that MLBox library automatically constructed based upon task input/output
  specifications.  
- `{image_path}` is the path to Singularity image that is computed as described above.  
- `{args}` is the task command line arguments, constructed automatically by the MLBox library.  
 