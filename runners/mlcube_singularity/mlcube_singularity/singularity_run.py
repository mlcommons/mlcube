import os
import logging
from mlcube.common import mlcube_metadata
from mlcube.common.utils import Utils


logger = logging.getLogger(__name__)


class SingularityRun(object):

    PLATFORM_NAME = 'singularity'

    def __init__(self, mlcube: mlcube_metadata.MLCube) -> None:
        """Singularity Runner.
        Args:
            mlcube (mlcube_metadata.MLCube): MLCube specification including platform configuration for Singularity.
        """
        self.mlcube: mlcube_metadata.MLCube = mlcube
        if self.mlcube.platform.platform.name != SingularityRun.PLATFORM_NAME:
            raise ValueError(f"Invalid platform name '{self.mlcube.platform.platform.name}' ('singularity' expected)")

    def image_path(self) -> str:
        """ Return full path to Singularity images taking into account user environment variables. """
        return os.path.join(
            self.mlcube.workspace_path,
            os.path.expandvars(self.mlcube.platform.container.image)
        )

    def configure(self) -> None:
        """Build Singularity Image on a current host."""
        # Get full path to a singularity image. By design, we compute it relative to {mlcube.root}/workspace.
        image_path: str = self.image_path()
        if os.path.exists(image_path):
            logger.info("Image found (%s).", image_path)
            return
        # Make sure a directory to store image exists. If paths are like "/opt/...", the call may fail.
        os.makedirs(os.path.dirname(image_path), exist_ok=True)

        # According to MLCube specs (?), build directory is {mlcube.root}/build that contains all files to build MLCube.
        # Singularity recipes are built taking into account that {mlcube.root}/build is the context (build) directory.
        recipe_path: str = self.mlcube.build_path
        recipe_file: str = os.path.join(recipe_path, 'Singularity.recipe')
        if not os.path.exists(recipe_file):
            raise RuntimeError(f"Singularity recipe not found: {recipe_file}")

        cmd: str = "cd {}; singularity build --fakeroot '{}' 'Singularity.recipe'".format(recipe_path, image_path)
        logger.info(cmd)
        Utils.run_or_die(cmd)

    def run(self) -> None:
        """  """
        image_path: str = self.image_path()
        if not os.path.exists(image_path):
            self.configure()
        # The 'mounts' dictionary maps host path to container path
        mounts, args = Utils.container_args(self.mlcube)
        print(f"mounts={mounts}, args={args}")

        volumes_str = ' '.join(['--bind {}:{}'.format(t[0], t[1]) for t in mounts.items()])

        # Let's assume singularity containers provide entry point in the right way.
        cmd = "singularity run {} {} {}".format(volumes_str, image_path, ' '.join(args))
        logger.info(cmd)
        Utils.run_or_die(cmd)
