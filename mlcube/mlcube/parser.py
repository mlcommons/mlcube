import os
import typing as t
from omegaconf import (OmegaConf, DictConfig)


class CliParser(object):
    @staticmethod
    def parse_mlcube_arg(mlcube: t.Optional[t.Text]) -> t.Tuple[t.Text, t.Text]:
        """ Parse value of the `--mlcube` command line argument.
        Args:
            mlcube: Path to a MLCube directory or `mlcube.yaml` file. If it's a directory, standard name
                `mlcube.yaml` is assumed for MLCube definition file.
        Returns:
            Tuple (mlcube_root_directory, mlcube_file_name), `mlcube_file_name` is a file name inside
                `mlcube_root_directory` directory.
        """
        if mlcube is None:
            mlcube = os.getcwd()
        mlcube_root, mlcube_file = os.path.abspath(mlcube), 'mlcube.yaml'
        if os.path.isfile(mlcube_root):
            mlcube_root, mlcube_file = os.path.split(mlcube_root)
        return mlcube_root, mlcube_file

    @staticmethod
    def parse_list_arg(arg: t.Optional[t.Text], default: t.Optional[t.Text] = None) -> t.List[t.Text]:
        """ Parse a string into list of strings using `,` as a separator.
        Args:
            arg: String if elements separated with `,`.
            default: Default value for `arg` if `arg` is None or empty.
        Returns:
            List of items.
        """
        arg = arg or default
        if not arg:
            return []
        return arg.split(',')

    @staticmethod
    def parse_extra_arg(*args: t.Text) -> t.Tuple[DictConfig, t.Dict]:
        """ Parse extra arguments on a command line.
        These arguments correspond to:
            - MLCube runtime arguments. These start with `-P` prefix and are translated to a nested dictionaries
                structure using `.` as a separator. For instance, `-Pdocker.image=mlcommons/mnist:0.0.1` translates to
                python dictionary {'docker': {'image': 'mlcommons/mnist:0.0.1'}}.
            - Task arguments are all other arguments that do not star with `-P`. These arguments are input/output
                arguments of tasks.
        Args:
            args: List of arguments that have not been parsed before.
        Returns:
            Tuple of two dictionaries: (mlcube_arguments, task_arguments).
        """
        mlcube_args = OmegaConf.from_dotlist([arg for arg in args if arg.startswith('-P')])

        task_args = [arg[2:].split('=') for arg in args if not arg.startswith('-P')]
        task_args = {arg[0]: arg[1] for arg in task_args}

        return mlcube_args, task_args
