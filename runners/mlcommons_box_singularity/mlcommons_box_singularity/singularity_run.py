import os
import logging
from mlcommons_box.common import mlbox_metadata
from mlcommons_box.common.utils import Utils
from mlcommons_box_singularity import metadata

logger = logging.getLogger(__name__)


class SingularityRun(object):
    def __init__(self, mlbox: mlbox_metadata.MLBox):
        """Singularity Runner.
        Args:
            mlbox (mlbox_metadata.MLBox): MLBox specification including platform configuration for Singularity.
        """
        self.mlbox: mlbox_metadata.MLBox = mlbox
        if not isinstance(self.mlbox.platform, metadata.SingularityPlatform):
            raise ValueError("Incorrect platform ({})".format(type(self.mlbox.platform)))

    def configure(self):
        """Build Singularity Image on a current host."""
        # Get full path to a singularity image. By design, we compute it relative to {mlbox.root}/workspace.
        image_path: str = os.path.join(self.mlbox.workspace_path, self.mlbox.platform.image)
        if os.path.exists(image_path):
            logger.info("Image found (%s).", image_path)
            return
        # Make sure directory to store s. image exists. If paths are like "/opt/...", the call may fail.
        os.makedirs(os.path.dirname(image_path), exist_ok=True)

        # According to MLBox specs (?), build directory is {mlbox.root}/build that contains all files to build MLBox.
        # Singularity recipes are built taking into account that {mlbox.root}/build is the context (build) directory.
        recipe_path: str = self.mlbox.build_path
        recipe_file: str = os.path.join(recipe_path, 'Singularity.recipe')
        if not os.path.exists(recipe_file):
            raise RuntimeError(f"Singularity recipe not found: {recipe_file}")

        cmd: str = "cd {}; singularity build --fakeroot '{}' 'Singularity.recipe'".format(recipe_path, image_path)
        logger.info(cmd)
        Utils.run_or_die(cmd)

    def run(self):
        """  """
        # The 'mounts' dictionary maps host path to container path
        mounts, args = Utils.container_args(self.mlbox)
        print(f"mounts={mounts}, args={args}")

        volumes_str = ' '.join(['--bind {}:{}'.format(t[0], t[1]) for t in mounts.items()])
        image_path: str = os.path.join(self.mlbox.workspace_path, self.mlbox.platform.image)

        # Let's assume singularity containers provide entry point in the right way.
        cmd = "singularity run {} {} {}".format(volumes_str, image_path, ' '.join(args))
        logger.info(cmd)
        Utils.run_or_die(cmd)
