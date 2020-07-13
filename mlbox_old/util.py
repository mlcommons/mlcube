import yaml


def get_config(file):
  """Read and parse a config file.
  Arguments:
    file: string value path to the config file
  Returns:
    Parsed configuration for MLBox to use internally
  """

  config = {}

  runtime_config = _load_yaml_config(file)
  mlbox_spec_file = runtime_config.get("mlbox", None)
  mlbox_config = _load_yaml_config(mlbox_spec_file)

  config["container"] = mlbox_config.get("container", None)
  config["volumes"] = []

  runtime_io_spec = runtime_config.get("io", None)
  mlbox_io_spec = mlbox_config.get("io", None)
  if runtime_io_spec and mlbox_io_spec:
    for io_key, runtime_io_value in runtime_io_spec.items():
      if io_key in mlbox_io_spec:
        mlbox_io_value = mlbox_io_spec[io_key]
        volume = mlbox_io_value
        volume.update(runtime_io_value)
        config["volumes"].append(volume)
  return config

def _load_yaml_config(file):
  try:
    with open(file, "r") as f:
      config = yaml.safe_load(f)
  except:
    # TODO: need error handling
    raise
  return config
