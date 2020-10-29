import logging
import os
from typing import Tuple
from mlcommons_box.common import mlbox_metadata


logger = logging.getLogger(__name__)


class DockerRun(object):
    def __init__(self, mlbox: mlbox_metadata.MLBox) -> None:
        """Docker Runner.
        Args:
            mlbox (mlbox_metadata.MLBox): MLBox specification including platform configuration for Docker.
        """
        self.mlbox: mlbox_metadata.MLBox = mlbox

    @staticmethod
    def get_env_variables() -> dict:
        env_vars = {}
        for proxy_var in ('http_proxy', 'https_proxy'):
            if os.environ.get(proxy_var, None) is not None:
                env_vars[proxy_var] = os.environ[proxy_var]
        return env_vars

    def configure(self) -> None:
        """Build Docker Image on a current host."""
        image_name: str = self.mlbox.platform.configuration.image

        # According to MLBox specs (?), build directory is {mlbox.root}/build that contains all files to build MLBox.
        # Dockerfiles are built taking into account that {mlbox.root}/build is the context (build) directory.
        build_path: str = self.mlbox.build_path
        docker_file: str = os.path.join(build_path, 'Dockerfile')
        if not os.path.exists(docker_file):
            cmd: str = f"docker pull {image_name}"
        else:
            env_args = ' '.join([f"--build-arg {var}={name}" for var, name in DockerRun.get_env_variables().items()])
            cmd: str = f"cd {build_path}; docker build {env_args} -t {image_name} -f Dockerfile ."
        logger.info(cmd)
        DockerRun.run_or_die(cmd)

    def run(self) -> None:
        """Run a box."""
        # The 'mounts' dictionary maps host path to container path
        mounts, args = self._generate_mounts_and_args()
        print(f"mounts={mounts}, args={args}")

        volumes_str = ' '.join(['--volume {}:{}'.format(t[0], t[1]) for t in mounts.items()])
        image_name: str = self.mlbox.platform.configuration.image
        container_params: str = self.mlbox.platform.configuration.parameters
        if container_params is None or container_params == '':
            container_params = "--rm --net=host --privileged=true"
        env_args = ' '.join([f"-e {var}={name}" for var, name in DockerRun.get_env_variables().items()])

        # Let's assume singularity containers provide entry point in the right way.
        docker_runner = self.mlbox.platform.platform.name
        cmd = f"{docker_runner} run {container_params} {volumes_str} {env_args} {image_name} {' '.join(args)}"
        logger.info(cmd)
        DockerRun.run_or_die(cmd)

    def _generate_mounts_and_args(self) -> Tuple[dict, list]:
        mounts, args = {}, [self.mlbox.invoke.task_name]

        def _create(binding_: dict, input_specs_: dict):
            # name: parameter name, path: parameter value
            for name, path in binding_.items():
                path = path.replace('$WORKSPACE', self.mlbox.workspace_path)

                path_type = input_specs_[name]
                if path_type == 'directory':
                    os.makedirs(path, exist_ok=True)
                    mounts[path] = mounts.get(
                        path,
                        '/mlbox_io{}/{}'.format(len(mounts), os.path.basename(path))
                    )
                    args.append('--{}={}'.format(name, mounts[path]))
                elif path_type == 'file':
                    file_path, file_name = os.path.split(path)
                    os.makedirs(file_path, exist_ok=True)
                    mounts[file_path] = mounts.get(
                        file_path,
                        '/mlbox_io{}/{}'.format(len(mounts), file_path)
                    )
                    args.append('--{}={}'.format(name, mounts[file_path] + '/' + file_name))
                else:
                    raise RuntimeError(f"Invalid path type: '{path_type}'")

        _create(self.mlbox.invoke.input_binding, self.mlbox.task.inputs)
        _create(self.mlbox.invoke.output_binding, self.mlbox.task.outputs)

        return mounts, args

    @staticmethod
    def run_or_die(cmd) -> None:
        print(cmd)
        if os.system(cmd) != 0:
            raise RuntimeError('Command failed: {}'.format(cmd))
