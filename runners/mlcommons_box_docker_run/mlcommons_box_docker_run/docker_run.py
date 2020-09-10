import os
import logging
from mlcommons_box.common import mlbox_metadata
from mlcommons_box.common.utils import Utils
from mlcommons_box_docker_run import metadata


logger = logging.getLogger(__name__)


class DockerRun(object):
    def __init__(self, mlbox: mlbox_metadata.MLBox):
        """Docker Runner.
        Args:
            mlbox (mlbox_metadata.MLBox): MLBox specification including platform configuration for Docker.
        """
        self.mlbox: mlbox_metadata.MLBox = mlbox
        if not isinstance(self.mlbox.platform, metadata.DockerPlatform):
            raise ValueError("Incorrect platform ({})".format(type(self.mlbox.platform)))

    @staticmethod
    def get_env_variables() -> dict:
        env_vars = {}
        for proxy_var in ('http_proxy', 'https_proxy'):
            if os.environ.get(proxy_var, None) is not None:
                env_vars[proxy_var] = os.environ[proxy_var]
        return env_vars

    def configure(self):
        """Build Docker Image on a current host."""
        image_name: str = self.mlbox.platform.image

        # According to MLBox specs (?), build directory is {mlbox.root}/build that contains all files to build MLBox.
        # Dockerfiles are built taking into account that {mlbox.root}/build is the context (build) directory.
        build_path: str = self.mlbox.build_path
        docker_file: str = os.path.join(build_path, 'Dockerfile')
        if not os.path.exists(docker_file):
            raise RuntimeError(f"Docker file not found: {docker_file}")

        # This is probably a workaround for now.
        env_args = ' '.join([f"--build-arg {var}={name}" for var, name in DockerRun.get_env_variables().items()])

        cmd: str = f"cd {build_path}; docker build {env_args} -t {image_name} -f Dockerfile ."
        logger.info(cmd)
        Utils.run_or_die(cmd)

    def run(self):
        """  """
        # The 'mounts' dictionary maps host path to container path
        mounts, args = Utils.container_args(self.mlbox)
        print(f"mounts={mounts}, args={args}")

        volumes_str = ' '.join(['--volume {}:{}'.format(t[0], t[1]) for t in mounts.items()])
        image_name: str = self.mlbox.platform.image
        docker_exec: str = self.mlbox.platform.runtime
        env_args = ' '.join([f"-e {var}={name}" for var, name in DockerRun.get_env_variables().items()])

        # Let's assume singularity containers provide entry point in the right way.
        args = ' '.join(args)
        cmd = f"{docker_exec} run --rm --net=host --privileged=true {volumes_str} {env_args} {image_name} {args}"
        logger.info(cmd)
        Utils.run_or_die(cmd)
