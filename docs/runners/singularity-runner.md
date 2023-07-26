# Singularity Runner
Singularity runner uses singularity to run MLCube&reg; cubes. It supports two mandatory commands - `configure` and
`run` with standard arguments - `mlcube`, `platform` and `task`. Users can configure Singularity runner in MLCube 
configuration file, system setting file, and override parameters on a command line.


## Configuration parameters
MLCube reference singularity runner supports the following configuration parameters (with default values):
```yaml
# Name of a singularity image, for instance "mnist-0.0.1.simg".
image: ${singularity.image}
# Path where to build the image. By default, it is `.image` inside workspace directory.
image_dir: ${runtime.workspace}/.image

# Singularity executable
singularity: singularity

# Build arguments
build_args: --fakeroot
# Singularity recipe file relative to workspace.
build_file: Singularity.recipe
```


## Configuring MLCubes
Users do not need to run the `configure` command manually, singularity docker runs this whenever image is not found. 
Singularity runner under the hood runs the following command line:  
```
cd {recipe_path} && ${singularity} build ${build_args} {image_uri} ${build_file}
```  
where:  

- `{recipe_path}` is the MLCube root directory.
- `${singularity}` is the singularity executable.
- `${build_args}` is the singularity build arguments.
- `{image_uri}` is the full image path (`${image_dir}/${image}`).  
- `${build_file}` is the singularity build file. 


## Running MLCubes
Singularity runner runs the following command:    
```
${singularity} run {volumes} {image_path} {task_args}
```  
where:   

- `${singularity}` is the singularity executable.
- `{volumes}` are the mount points that the runner automatically constructs based upon the task input/output
  specifications.  
- `{image_path}` is the path to Singularity image (`{image_dir}/{image}`).  
- `{task_args}` is the task command line arguments, constructed automatically by the runner.  
 