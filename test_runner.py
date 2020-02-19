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

# noinspection PyArgumentList
logging.basicConfig(
    level=logging.INFO,
    format="[MLBOX] %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)

from mlbox.runners.local import LocalRunner


def load_config(file_path: str) -> dict:
  with open(file_path, 'r') as config_stream:
      return yaml.load(config_stream, Loader=yaml.FullLoader)


def main():
  # Get command line arguments
  action, target = sys.argv[1], sys.argv[2]
  if action == 'configure':
    mlbox_path = sys.argv[3]
  else:
    task = sys.argv[3]
    mlbox_path = sys.argv[4]

  # Load configuration file
  mlbox_path = os.path.abspath(mlbox_path)
  config = load_config(os.path.join(mlbox_path, 'mlbox.yaml'))
  # Temporary solution to pass path to runners
  config['_mlbox_path'] = mlbox_path
  config['mlbox_docker_info']['context_path'] = os.path.join(mlbox_path, 'internals')
  if config['implementation'] != 'mlbox_docker':
    raise ValueError("Unknown MLBox docker implementation ('{}')".format(config['implementation']))

  # Add proxy info if found in the environment
  for proxy in ('http_proxy', 'https_proxy'):
    proxy_val = os.environ.get(proxy, os.environ.get(proxy.upper(), None))
    if proxy_val is not None:
      config['mlbox_docker_info']['build_args'].update({proxy: proxy_val})
      config['mlbox_docker_info']['run_args'].extend(['-e', '{}={}'.format(proxy, proxy_val)])

  # Instantiate a runner
  if target == 'local':
    runner = LocalRunner(config)
  else:
    raise ValueError("Unknown runner ('{}')".format(target))

  # Execute task or configure
  if action == 'configure':
    runner.configure()
  elif action == 'execute':
    # For the sake of PoC, just take it from the configuration
    dc = config['mlbox_docker_info']
    cmd = [dc['docker'], 'run'] + dc['run_args'] + [dc['image']] + dc['run_cmd']
    runner.execute(cmd)


if __name__ == '__main__':
  main()

