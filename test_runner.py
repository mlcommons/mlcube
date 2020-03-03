"""
This file is used for testing some of the functionality (MLBox runners) and will be removed once testing is done.
Simulates the following functionality:
  test_runner configure local ./examples/ngc_resnet_50   # Pull docker container from NGC
  test_runner configure local ./examples/mnist           # Build docker container

  test_runner execute local train ./examples/ngc_resnet_50     # Run several training iterations.
  test_runner execute local train ./examples/mnist             # Run several training iterations.
"""
import sys
import yaml
import os
import logging
import subprocess
from typing import List

# noinspection PyArgumentList
logging.basicConfig(level=logging.INFO, format="[MLBOX] %(message)s", handlers=[logging.StreamHandler()])


def load_config(file_path: str) -> dict:
    with open(file_path, 'r') as config_stream:
        return yaml.load(config_stream, Loader=yaml.FullLoader)


def get_task_parameters(task: str, config: dict) -> List[str]:
    task_spec = config['tasks'][task]
    return list(task_spec['inputs'].keys()) + list(task_spec['outputs'].keys())


def main():
    """
    test_runner [configure|run] [runner] mlbox ...

    test_runner configure local ./examples/mnist
    test_runner run local ./examples/mnist:downloaddata/default
    test_runner run local ./examples/mnist:train/default
    """
    action, runner, task = sys.argv[1], sys.argv[2], sys.argv[3]

    #                       action    runner mlbox
    # python test_runner.py configure local  ./examples/mnist
    if action != "run":
        raise NotImplemented("Only 'run' action is implemented")
    if runner != "local":
        raise NotImplemented("Only 'local' runner is implemented")

    # Parse task: mlbox_path:task/parameters
    task, param_set = task.rsplit('/', 1)
    mlbox, task = task.rsplit(':', 1)
    print("MLBox={}, task={}, parameter_set={}".format(mlbox, task, param_set))

    # Load MLBox specs
    mlbox_root_dir = os.path.abspath(mlbox)
    config = load_config(os.path.join(mlbox_root_dir, 'mlbox.yaml'))

    # Get task parameters
    # TODO: This is not used. Why?
    task_params = get_task_parameters(task, config)

    # Load task parameter values. Each parameter is either a directory or a file.
    task_param_values = load_config(os.path.join(os.path.abspath(mlbox), 'tasks', task, "{}.yaml".format(param_set)))

    # Compute directory/file mappings for docker: --volume HOST_PATH:DOCKER_PATH. Naive implementation.
    docker_args, mlbox_args = [], []
    # The param_name and param_value are defined in task/default.yaml configuration file.
    for param_name, host_path in task_param_values.items():
        # If it's a workspace path, convert to absolute host path
        if host_path.startswith('workspace/'):
            host_path = os.path.join(mlbox_root_dir, host_path)
        host_path = os.path.abspath(host_path)
        # Always mount host folder in /mlbox_io inside container. The concrete folder name is the name of the
        # parameter, for instance, /mlbox_io/data_dir or /mlbox_io/model_dir.
        docker_args.append('--volume')
        docker_path = "/mlbox_io/{}".format(param_name)
        #
        if os.path.isdir(host_path):
            docker_args.append("{}:{}".format(host_path, docker_path))
            mlbox_args.extend(["--{}".format(param_name), docker_path])
        elif os.path.isfile(host_path):
            host_path, file_name = host_path.rsplit('/', 1)
            docker_args.append("{}:{}".format(host_path, docker_path))
            mlbox_args.extend(["--{}".format(param_name), "{}/{}".format(docker_path, file_name)])
        else:
            raise ValueError("Wrong configuration parameter: {} = {}".format(param_name, host_path))

    #
    cmd = ["docker", "run"] + \
          docker_args + \
          ["--rm", "-i", "mlperf/mlbox-example-mnist", "/bin/bash", "-c",
           "cd /workspace && python3 ./mnist.py {} {}".format(task, " ".join(mlbox_args))]
    print(cmd)

    try:
        return subprocess.check_call(cmd, stdout=sys.stdout, stderr=sys.stderr)
    except subprocess.CalledProcessError as err:
        logging.warning("Error while executing MLBox: cmd=%s, err=%s", str(cmd), str(err))
        return err.returncode


if __name__ == '__main__':
    main()
