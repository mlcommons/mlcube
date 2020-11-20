import logging
import os
import typing

from mlcube.common import mlcube_metadata


logger = logging.getLogger(__name__)


class DockerRun(object):
    def __init__(self, mlcube: mlcube_metadata.MLCube):
        """Docker Runner.
        Args:
            mlcube (mlcube_metadata.MLCube): MLCube specification including platform configuration for Docker.
        """
        self.mlcube: mlcube_metadata.MLCube = mlcube

    @staticmethod
    def get_env_variables() -> dict:
        env_vars = {}
        for proxy_var in ('http_proxy', 'https_proxy'):
            if os.environ.get(proxy_var, None) is not None:
                env_vars[proxy_var] = os.environ[proxy_var]
        return env_vars

    def image_exists(self, image_name: str) -> bool:
        """Check if docker image exists.
        Args:
            image_name (str): Name of a docker image.
        Returns:
            True if image exists, else false.
        """
        return self._run_or_die(f"docker inspect --type=image {image_name} > /dev/null 2>&1", die_on_error=False) == 0

    def configure(self):
        """Build Docker Image on a current host."""
        image_name: str = self.mlcube.platform.container.image

        # According to MLCube specs (?), build directory is {mlcube.root}/build that contains all files to build MLCube.
        # Dockerfiles are built taking into account that {mlcube.root}/build is the context (build) directory.
        build_path: str = self.mlcube.build_path
        docker_file: str = os.path.join(build_path, 'Dockerfile')
        if not os.path.exists(docker_file):
            cmd: str = f"docker pull {image_name}"
        else:
            env_args = ' '.join([f"--build-arg {var}={name}" for var, name in DockerRun.get_env_variables().items()])
            cmd: str = f"docker build {env_args} -t {image_name} -f {docker_file} {build_path}"
        logger.info(cmd)
        self._run_or_die(cmd)

    def run(self):
        """Run a cube."""
        image_name: str = self.mlcube.platform.container.image
        if not self.image_exists(image_name):
            logger.warning("Docker image (%s) does not exist. Running 'configure' phase.", image_name)
            self.configure()

        # The 'mounts' dictionary maps host path to container path
        mounts, args = self._generate_mounts_and_args()
        print(f"mounts={mounts}, args={args}")

        volumes_str = ' '.join(['--volume {}:{}'.format(t[0], t[1]) for t in mounts.items()])
        runtime: str = self.mlcube.platform.container.runtime
        runtime_arg = "--runtime=" + runtime if runtime is not None else ""
        env_args = ' '.join([f"-e {var}={name}" for var, name in DockerRun.get_env_variables().items()])

        # Let's assume singularity containers provide entry point in the right way.
        args = ' '.join(args)
        cmd = f"docker run --rm {runtime_arg} --net=host --privileged=true {volumes_str} {env_args} {image_name} {args}"
        logger.info(cmd)
        self._run_or_die(cmd)

    def _generate_mounts_and_args(self) -> typing.Tuple[dict, list]:
        mounts, args = {}, [self.mlcube.invoke.task_name]

        def _create(binding_: dict, input_specs_: dict):
            # name: parameter name, path: parameter value
            for name, path in binding_.items():
                path = path.replace('$WORKSPACE', self.mlcube.workspace_path)

                path_type = input_specs_[name]
                if path_type == 'directory':
                    os.makedirs(path, exist_ok=True)
                    mounts[path] = mounts.get(
                        path,
                        '/mlcube_io{}/{}'.format(len(mounts), os.path.basename(path))
                    )
                    args.append('--{}={}'.format(name, mounts[path]))
                elif path_type == 'file':
                    file_path, file_name = os.path.split(path)
                    os.makedirs(file_path, exist_ok=True)
                    mounts[file_path] = mounts.get(
                        file_path,
                        '/mlcube_io{}/{}'.format(len(mounts), file_path)
                    )
                    args.append('--{}={}'.format(name, mounts[file_path] + '/' + file_name))
                else:
                    raise RuntimeError(f"Invalid path type: '{path_type}'")

        _create(self.mlcube.invoke.input_binding, self.mlcube.task.inputs)
        _create(self.mlcube.invoke.output_binding, self.mlcube.task.outputs)

        return mounts, args

    def _run_or_die(self, cmd: str, die_on_error: bool = True) -> int:
        """Execute shell command.
        Args:
            cmd(str): Command to execute.
            die_on_error (bool): If true and shell returns non-zero exit status, raise RuntimeError.
        Returns:
            Exit code.
        """
        print(cmd)
        return_code: int = os.system(cmd)
        if return_code != 0 and die_on_error:
            raise RuntimeError('Command failed: {}'.format(cmd))
        return return_code
