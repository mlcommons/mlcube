"""This requires the MLCube 2.0 that's located somewhere in one of dev branches."""
import logging
import os
import sys
import typing as t

import click

import coloredlogs

from io import StringIO

from click.core import DEPRECATED_HELP_NOTICE
from markdown import Markdown

from mlcube.config import MLCubeConfig
from mlcube.errors import (ExecutionError, IllegalParameterValueError, MLCubeError)
from mlcube.parser import (CliParser, MLCubeDirectory)
from mlcube.platform import Platform
from mlcube.runner import Runner
from mlcube.shell import Shell
from mlcube.system_settings import SystemSettings
from mlcube.validate import Validate

from omegaconf import (DictConfig, OmegaConf)

logger = logging.getLogger(__name__)


class Markdown2Text:
    """Idea to convert Markdown text into a plain text is from here: https://stackoverflow.com/a/54923798/575749"""
    _markdown: t.Optional[Markdown] = None
    TEXT_FORMAT = 'plain'

    @staticmethod
    def unmark_element(element, stream=None):
        if stream is None:
            stream = StringIO()
        if element.text:
            stream.write(element.text)
        for sub in element:
            Markdown2Text.unmark_element(sub, stream)
        if element.tail:
            stream.write(element.tail)
        return stream.getvalue()

    @staticmethod
    def convert(text: str) -> str:
        if Markdown2Text._markdown is None:
            Markdown.output_formats[Markdown2Text.TEXT_FORMAT] = Markdown2Text.unmark_element
            Markdown2Text._markdown = Markdown(output_format=Markdown2Text.TEXT_FORMAT)
            Markdown2Text._markdown.stripTopLevelTags = False
        try:
            text = Markdown2Text._markdown.convert(text)
        except (ValueError, UnicodeDecodeError):
            ...
        return text


class MultiValueOption(click.Option):
    def __init__(self, *args, **kwargs) -> None:
        super(MultiValueOption, self).__init__(*args, **kwargs)
        self._previous_parser_process: t.Optional[t.Callable] = None
        self._eat_all_parser: t.Optional[click.parser.Option] = None

    def add_to_parser(self, parser: click.parser.OptionParser, ctx: click.core.Context):

        def parser_process(value: str, state: click.parser.ParsingState):
            values: t.List[str] = [value]
            prefixes: t.Tuple[str] = tuple(self._eat_all_parser.prefixes)
            while state.rargs:
                if state.rargs[0].startswith(prefixes):
                    break
                values.append(state.rargs.pop(0))
            self._previous_parser_process(tuple(values), state)

        super(MultiValueOption, self).add_to_parser(parser, ctx)
        for opt_name in self.opts:
            our_parser: t.Optional[click.parser.Option] = \
                parser._long_opt.get(opt_name) or parser._short_opt.get(opt_name)
            if our_parser:
                self._eat_all_parser = our_parser
                self._previous_parser_process = our_parser.process
                our_parser.process = parser_process
                break


class HelpEpilog(object):
    """Structured epilog for click command.

    This class provides multiple usage examples and is responsible for formatting the help messages. See
    `mlcube.MLCubeCommand` documentation on how to use this class.

    Args:
        examples: List of tuples. Each tuple contains two elements. First element is the example title, and the second
            element is the list of commands for this example.
    """
    class Example:
        """Context manager for helping with formatting epilogues when users invoke help on a command line."""
        def __init__(self, formatter: click.formatting.HelpFormatter, title: str) -> None:
            self.formatter = formatter
            self.title = title

        def __enter__(self) -> None:
            self.formatter.indent()
            self.formatter.write_heading('- ' + self.title)
            self.formatter.write_paragraph()
            self.formatter.current_indent += 2 * self.formatter.indent_increment

        def __exit__(self, exc_type, exc_val, exc_tb) -> None:
            self.formatter.write_paragraph()
            self.formatter.current_indent -= 3 * self.formatter.indent_increment

    def __init__(self, examples: t.List[t.Tuple[str, t.List[str]]]) -> None:
        self.examples = examples

    def format(self, formatter: click.formatting.HelpFormatter) -> None:
        if not self.examples:
            return
        formatter.write_heading('\nEXAMPLES')
        for title, commands in self.examples:
            with HelpEpilog.Example(formatter, title):
                for cmd in commands:
                    formatter.write_text('$ ' + cmd)


class MLCubeCommand(click.Command):
    """Click command that supports structured epilogues with `mlcube.EpilogWithExamples` epilog class.

    In addition, it uses the `markdown` package to convert help messages to plain text when user requests help (--help).
    This does not affect web-based documentation that is generated with MKDocs plugin mkdocs-click.

    ```python
    @cli.command(name='my_cmd', cls=CommandWithEpilog,
                 epilog=EpilogWithExamples([CommandExample('Run me', ['mlcube my_cmd'])]))
    def my_cmd() -> None:
        ...
    ```
    """
    def format_help_text(self, ctx, formatter):
        """Writes the help text to the formatter if it exists."""
        if self.help:
            formatter.write_paragraph()
            with formatter.indentation():
                help_text = Markdown2Text.convert(self.help)
                if self.deprecated:
                    help_text += DEPRECATED_HELP_NOTICE
                formatter.write_text(help_text)
        elif self.deprecated:
            formatter.write_paragraph()
            with formatter.indentation():
                formatter.write_text(DEPRECATED_HELP_NOTICE)

    def format_options(self, ctx: click.core.Context, formatter: click.formatting.HelpFormatter) -> None:
        """Writes all the options into the formatter if they exist.

        This implementation removes Markdown format from the options' help messages should they exist. Any errors
        occurred during the conversion are silently ignored and original messages are used instead. This is probably
        fine since MLCube can (in the future releases) run unit tests for all help messages found in this file.
        """
        opts = []
        for param in self.get_params(ctx):
            rv = param.get_help_record(ctx)
            if rv is not None:
                opts.append((rv[0], Markdown2Text.convert(rv[1])))
        if opts:
            with formatter.section("Options"):
                formatter.write_dl(opts)

    def format_epilog(self, ctx: click.core.Context, formatter: click.formatting.HelpFormatter) -> None:
        """Format epilog if its type `mlcube.EpilogWithExamples`, else fallback to default implementation."""
        if isinstance(self.epilog, HelpEpilog):
            self.epilog.format(formatter)
        else:
            super().format_epilog(ctx, formatter)

        formatter.write_text(f"MLCube online documentation: {Docs.url()}")


def _parse_cli_args(ctx: t.Optional[t.Union[click.core.Context, t.List[str]]],
                    mlcube: t.Optional[str], platform: t.Optional[str],
                    workspace: t.Optional[str],
                    resolve: bool) -> t.Tuple[t.Optional[t.Type[Runner]], DictConfig]:
    """Parse command line arguments.

    Args:
        ctx: Click context or list of extra arguments from a command line. We need this to get access to extra
             CLI arguments.
        mlcube: Path to MLCube root directory or mlcube.yaml file.
        platform: Platform to use to run this MLCube (docker, singularity, gcp, k8s etc).
        workspace: Workspace path to use. If not specified, default workspace inside MLCube directory is used.
        resolve: if True, compute values in MLCube configuration.
    """
    if mlcube is None:
        mlcube = os.getcwd()
    mlcube_inst: MLCubeDirectory = CliParser.parse_mlcube_arg(mlcube)
    Validate.validate_type(mlcube_inst, MLCubeDirectory)
    if ctx is not None:
        _ctx = ctx
        if isinstance(_ctx, click.core.Context):
            _ctx = _ctx.args
        mlcube_cli_args, task_cli_args = CliParser.parse_extra_arg(*_ctx)
    else:
        mlcube_cli_args, task_cli_args = None, None
    if platform is not None:
        system_settings = SystemSettings()
        runner_config: t.Optional[DictConfig] = system_settings.get_platform(platform)
        runner_cls: t.Optional[t.Type[Runner]] = Platform.get_runner(
            system_settings.runners.get(runner_config.runner, None)
        )
    else:
        runner_cls, runner_config = None, None
    mlcube_config = MLCubeConfig.create_mlcube_config(
        os.path.join(mlcube_inst.path, mlcube_inst.file), mlcube_cli_args, task_cli_args, runner_config, workspace,
        resolve=resolve, runner_cls=runner_cls
    )
    return runner_cls, mlcube_config


_TERMINAL_WIDTH = click.termui.get_terminal_size()[0]
"""Width of a user terminal. MLCube overrides default (80) character width to make usage examples look better."""


class Docs:
    _ROOT_URL = "https://mlcommons.github.io/mlcube"
    """Root URL for documentation. It is used to build valid references for help messages."""

    @staticmethod
    def url(rel_url: t.Optional[str] = None) -> str:
        return f"{Docs._ROOT_URL}/{rel_url}" if rel_url else Docs._ROOT_URL

    @staticmethod
    def concept_url(concept: str) -> str:
        return f"{Docs._ROOT_URL}/getting-started/concepts/#{concept}"

    @staticmethod
    def runner_url(runner: str) -> str:
        return f"{Docs._ROOT_URL}/runners/{runner}"


help_option = click.help_option(
    '--help', '-h', help='Show help message and exit.'
)

log_level_option_help = \
    "Logging level is a lower-case string value for Python's logging library (see [Logging Levels](%s) for more "\
    "details). Only messages with this logging level or higher are logged." % (
        "https://docs.python.org/3/library/logging.html#logging-levels"
    )
log_level_option = click.option(
    '--log-level', '--log_level', required=False, type=click.Choice(['critical', 'error', 'warning', 'info', 'debug']),
    default='warning', help=log_level_option_help
)

mlcube_option_help = \
    "Path to an MLCube project. It can be a [directory path](%s), or a path to an MLCube [configuration file](%s). "\
    "When it is a directory path, MLCube runtime assumes this directory is the MLCube root directory containing "\
    "`mlcube.yaml` file. When it is a file path, this file is assumed to be the MLCube configuration file "\
    "(`mlcube.yaml`), and a parent directory of this file is considered to be the MLCube root directory. Default "\
    "value is current directory." % (
        Docs.concept_url("mlcube-root-directory"), Docs.concept_url("mlcube-configuration")
    )
mlcube_option = click.option(
    '--mlcube', required=False, type=str, default=None, metavar='PATH', help=mlcube_option_help
)

platform_option_help = \
    "[Platform](%s) name to run MLCube on (a platform is a configured instance of an MLCube runner). Multiple "\
    "platforms are supported, including `docker` ([Docker and Podman](%s)), `singularity` ([Singularity](%s)). Other "\
    "runners are in experimental stage: `gcp` ([Google Cloud Platform](%s)), `k8s` ([Kubernetes](%s)), `kubeflow` "\
    "([KubeFlow](%s)), ssh ([SSH runner](%s)). Default is `docker`. Platforms are defined and configured in MLCube "\
    "[system settings file](%s)." % (
        Docs.concept_url("platform"), Docs.runner_url("docker-runner"), Docs.runner_url("singularity-runner"),
        Docs.runner_url("gcp-runner"), Docs.runner_url("kubernetes"), Docs.runner_url("kubeflow"),
        Docs.runner_url("ssh-runner"), Docs.url("getting-started/system-settings/")
    )
platform_option = click.option(
    '--platform', required=False, type=str, default='docker', metavar='NAME', help=platform_option_help
)

task_option_help = \
    "MLCube [task](%s) name(s) to run, default is `main`. This parameter can take a list of values, in which case "\
    "task names are separated with comma (,)." % (Docs.concept_url('task'))
task_option = click.option(
    '--task', required=False, type=str, default=None, help=task_option_help
)

workspace_option_help = \
    "Location of a [workspace](%s) to store input and output artifacts of MLCube [tasks](%s). If not specified "\
    "(None), `${MLCUBE_ROOT}/workspace/` is used." % (
        Docs.concept_url("workspace"), Docs.concept_url("task")
    )
workspace_option = click.option(
    '--workspace', required=False, type=str, default=None, metavar='PATH', help=workspace_option_help
)

parameter_option_help = \
    "MLCube [configuration parameter](%s) is a key-value pair. Must start with `-P` or '-p'. The dot (.) is used to "\
    "refer to nested parameters, for instance, `-Pdocker.build_strategy=always`. These parameters have the highest "\
    "priority and override any other parameters in [system settings](%s) and [MLCube configuration](%s). " % (
        Docs.concept_url("mlcube-configuration-parameter"), Docs.concept_url("system-settings"),
        Docs.concept_url("mlcube-configuration")
    )
parameter_option = click.option(
    '-P', '-p', required=False, type=str, default=None, metavar='PARAMS', multiple=True, help=parameter_option_help
)

resolve_option_help = \
    "Resolve [MLCube parameters](%s). The `mlcube` uses [OmegaConf](%s) library to manage its configuration, "\
    "including [configuration files](%s), [system settings](%s) files and configuration parameters provided by "\
    "users on command lines. OmegaConf supports variable interpolation (when one variables depend on other variables, "\
    "e.g., `{'docker.image': 'mlcommons/{name}:${version}'}`). When this flag is set to true, the `mlcube` "\
    "computes actual values of all variables." % (
        Docs.concept_url("mlcube-configuration-parameter"), "https://omegaconf.readthedocs.io/",
        Docs.concept_url("mlcube-configuration"), Docs.concept_url("system-settings")
    )
resolve_option = click.option('--resolve', is_flag=True, help=resolve_option_help)


def _mnist_example(steps: t.List[str]) -> t.List[str]:
    return [
        'git clone https://github.com/mlcommons/mlcube_examples',
        'cd ./mlcube_examples',
    ] + steps


_show_config_help_epilog = HelpEpilog([
    (
        'Show effective MLCube configuration',
        _mnist_example(['mlcube show_config --mlcube=mnist'])
    ),
    (
        'Show effective MLCube configuration overriding parameters on a command line',
        _mnist_example(['mlcube show_config --mlcube=mnist -Pdocker.build_strategy=auto'])
    )
])
"""Usage examples for `mlcube show_config` command."""


_configure_help_epilog = HelpEpilog([
    (
        'Configure MNIST MLCube project',
        _mnist_example(['mlcube configure --mlcube=mnist --platform=docker'])
    )
])
"""Usage examples for `mlcube configure` command."""

_run_help_epilog = HelpEpilog([
    (
        'Run MNIST MLCube project',
        _mnist_example(['mlcube run --mlcube=mnist --platform=docker --task=download,train'])
    )
])
"""Usage examples for `mlcube run` command."""

_describe_help_epilog = HelpEpilog([
    (
        'Run MNIST MLCube project',
        _mnist_example(['mlcube describe --mlcube=mnist'])
    )
])
"""Usage examples for `mlcube describe` command."""

_create_help_epilog = HelpEpilog([
    (
        'Create a new empty MLCube project',
        ['mlcube create']
    )
])
"""Usage examples for `mlcube create` command."""

_config_help_epilog = HelpEpilog([
    (
        'Print the content of MLCube system settings file',
        ['mlcube config --list']
    ),
    (
        'Get default environmental variables for mlcube run command with docker platform',
        ['mlcube config --get platforms.docker.env_args']
    ),
    (
        'Create, rename and remove a custom docker platform by copying existing configuration',
        [
            'mlcube config --create-platform docker docker_v01',
            'mlcube config --get platforms.docker_v01',
            'mlcube config --rename-platform docker_v01 docker_v02',
            'mlcube config --get platforms.docker_v02',
            'mlcube config --remove-platform docker_v02'
        ]
    )
])
"""Usage examples for `mlcube config` command."""


@click.group(name='mlcube', add_help_option=False)
@log_level_option
@help_option
def cli(log_level: t.Optional[str]):
    """MLCube 📦 is a tool for packaging, distributing and running Machine Learning (ML) projects and models.

    \b
    GitHub: https://github.com/mlcommons/mlcube
    Documentation: https://mlcommons.github.io/mlcube/
    """

    if log_level:
        log_level = log_level.upper()
        logging.basicConfig(level=log_level)
        coloredlogs.install(level=log_level)
        logging.info("Setting Log Level from CLI argument to '%s'.", log_level)
    _ = SystemSettings().update_installed_runners()


@cli.command(
    name='show_config', cls=MLCubeCommand, add_help_option=False, epilog=_show_config_help_epilog,
    context_settings={'ignore_unknown_options': True, 'allow_extra_args': True, 'max_content_width': _TERMINAL_WIDTH}
)
@mlcube_option
@platform_option
@workspace_option
@resolve_option
@parameter_option
@help_option
@click.pass_context
def show_config(ctx: click.core.Context, mlcube: t.Optional[str], platform: str, workspace: str,
                resolve: bool, p: t.Tuple[str]) -> None:
    """Show effective MLCube configuration.

    Effective MLCube configuration is the one used by one of MLCube runners to run this MLCube. This configuration is
    built by merging (1) default runner configuration retrieved from system settings, (2) MLCube project configuration
    and (3) configuration parameters passed by a user on a command line (CONFIG_PARAM).

    \f
    Args:
        ctx: Click context for unknown options
        mlcube: Path to MLCube root directory or mlcube.yaml file.
        platform: Platform to use to run this MLCube (docker, singularity, gcp, k8s etc).
        workspace: Workspace path to use. If not specified, default workspace inside MLCube directory is used.
        resolve: if True, compute values in MLCube configuration.
        p: Additional configuration parameters.
    """
    if mlcube is None:
        mlcube = os.getcwd()
    _, mlcube_config = _parse_cli_args(
        ctx.args + ['-P' + param for param in p], mlcube, platform, workspace, resolve
    )
    print(OmegaConf.to_yaml(mlcube_config))


@cli.command(
    name='configure', cls=MLCubeCommand, add_help_option=False, epilog=_configure_help_epilog,
    context_settings={'ignore_unknown_options': True, 'allow_extra_args': True, 'max_content_width': _TERMINAL_WIDTH}
)
@mlcube_option
@platform_option
@parameter_option
@help_option
def configure(mlcube: t.Optional[str], platform: str, p: t.Tuple[str]) -> None:
    """Configure MLCube.

    Some MLCube projects need to be configured first. For instance, docker-based MLCubes distributed via GitHub with
    source code most likely will provide a `Dockerfile` to build a docker image. In this case, the process of building
    a docker image before MLCube runner can run it, is called a configuration phase. In general, users do not need to
    run this command manually - MLCube runners should be able to figure out when they need to run it, and will run it
    as part of `mlcube run` command.

    \f
    Args:
        mlcube: Path to MLCube root directory or mlcube.yaml file.
        platform: Platform to use to configure this MLCube for (docker, singularity, gcp, k8s etc).
        p: Additional configuration parameters.
    """
    if mlcube is None:
        mlcube = os.getcwd()
    logger.info("Configuring MLCube (`%s`) for `%s` platform.", os.path.abspath(mlcube), platform)
    try:
        runner_cls, mlcube_config = _parse_cli_args([*p], mlcube, platform, workspace=None, resolve=True)
        runner = runner_cls(mlcube_config, task=None)
        runner.configure()
    except MLCubeError as err:
        exit_code = err.context.get('code', 1) if isinstance(err, ExecutionError) else 1
        logger.exception(f"Failed to configure MLCube with error code {exit_code}.")
        if isinstance(err, ExecutionError):
            print(err.describe())
        sys.exit(exit_code)
    logger.info("MLCube (%s) has been successfully configured for `%s` platform.", os.path.abspath(mlcube), platform)


@cli.command(
    name='run', cls=MLCubeCommand, add_help_option=False, epilog=_run_help_epilog,
    context_settings={'ignore_unknown_options': True, 'allow_extra_args': True, 'max_content_width': _TERMINAL_WIDTH}
)
@mlcube_option
@platform_option
@task_option
@workspace_option
@parameter_option
@help_option
@click.pass_context
def run(ctx: click.core.Context, mlcube: t.Optional[str], platform: str, task: str, workspace: str,
        p: t.Tuple[str]) -> None:
    """Run MLCube task(s).

    \f
    Args:
        ctx: Click context for unknown options
        mlcube: Path to MLCube root directory or mlcube.yaml file.
        platform: Platform to use to run this MLCube (docker, singularity, gcp, k8s etc).
        task: Comma separated list of tasks to run.
        workspace: Workspace path to use. If not specified, default workspace inside MLCube directory is used.
        p: Additional configuration parameters.
    """
    if mlcube is None:
        mlcube = os.getcwd()
    runner_cls, mlcube_config = _parse_cli_args(
        ctx.args + ['-P' + param for param in p], mlcube, platform, workspace, resolve=True
    )
    mlcube_tasks: t.List[str] = list((mlcube_config.get('tasks', None) or {}).keys())  # Tasks in this MLCube.
    tasks: t.List[str] = CliParser.parse_list_arg(task, default=None)                  # Requested tasks.

    if len(tasks) == 0:
        logger.warning("Missing required task name (--task=COMMA_SEPARATED_LIST_OF_TASK_NAMES).")
        if len(mlcube_tasks) != 1:
            logger.error("Task name could not be automatically resolved (supported tasks = %s).", str(mlcube_tasks))
            exit(1)
        logger.info("Task name has been automatically resolved to %s (supported tasks = %s).",
                    mlcube_tasks[0], str(mlcube_tasks))
        tasks = mlcube_tasks

    unknown_tasks: t.List[str] = [name for name in tasks if name not in mlcube_tasks]
    if len(unknown_tasks) > 0:
        logger.error("Unknown tasks have been requested: supported tasks = %s, requested tasks = %s, "
                     "unknown tasks = %s.", str(mlcube_tasks), str(tasks), str(unknown_tasks))
        exit(1)

    try:
        # TODO: Sergey - Can we have one instance for all tasks?
        for task in tasks:
            logger.info("Task = %s", task)
            runner = runner_cls(mlcube_config, task=task)
            runner.run()
    except MLCubeError as err:
        exit_code = err.context.get('code', 1) if isinstance(err, ExecutionError) else 1
        logger.exception(f"Failed to run MLCube with error code {exit_code}.")
        if isinstance(err, ExecutionError):
            print(err.describe())
        sys.exit(exit_code)


@cli.command(
    name='describe', cls=MLCubeCommand, add_help_option=False, epilog=_describe_help_epilog,
    context_settings={'max_content_width': _TERMINAL_WIDTH}
)
@mlcube_option
@help_option
def describe(mlcube: t.Optional[str]) -> None:
    """Describe this MLCube.

    \f
    Args:
        mlcube: Path to MLCube root directory or mlcube.yaml file.
    """
    if mlcube is None:
        mlcube = os.getcwd()
    _, mlcube_config = _parse_cli_args(None, mlcube, None, None, resolve=True)
    print("MLCube")
    print(f"  path = {mlcube_config.runtime.root}")
    print(f"  name = {mlcube_config.name}:{mlcube_config.get('version', 'latest')}")
    print()
    print(f"  workspace = {mlcube_config.runtime.workspace}")
    print(f"  system settings = {SystemSettings.system_settings_file()}")
    print()
    print("  Tasks:")
    for task_name, task_def in mlcube_config.tasks.items():
        description = f"name = {task_name}"
        if len(task_def.parameters.inputs) > 0:
            description = f"{description}, inputs = {list(task_def.parameters.inputs.keys())}"
        if len(task_def.parameters.outputs) > 0:
            description = f"{description}, outputs = {list(task_def.parameters.outputs.keys())}"
        print(f"    {description}")
    print()
    print("Run this MLCube:")
    print("  Configure MLCube:")
    print(f"    mlcube configure --mlcube={mlcube_config.runtime.root} --platform=docker")
    print("  Run MLCube tasks:")
    for task_name in mlcube_config.tasks.keys():
        print(f"    mlcube run --mlcube={mlcube_config.runtime.root} --task={task_name} --platform=docker")
    print()


@cli.command(
    name='config', cls=MLCubeCommand, add_help_option=False, epilog=_config_help_epilog,
    context_settings={'ignore_unknown_options': True, 'allow_extra_args': True, 'max_content_width': _TERMINAL_WIDTH}
)
@click.option(
    '--list', 'list_all', is_flag=True,
    help="Print out the content of system settings file."
)
@click.option(
    '--get', required=False, type=str, default=None,
    help="Return value of the key (use OmegaConf notation, e.g. `mlcube config --get runners.docker`)."
)
@click.option(
    '--create_platform', '--create-platform', required=False, cls=MultiValueOption, type=tuple, default=None,
    help="Create a new platform instance for this runner. Default runner parameters are used to initialize this new "
         "platform."
)
@click.option(
    '--remove_platform', '--remove-platform', required=False, type=str, default=None,
    help="Remove this platform. If this is one of the default platforms (e.g., `docker`), it will be recreated (with "
         "default values) next time `mlcube` runs."
)
@click.option(
    '--rename_platform', '--rename-platform', required=False, cls=MultiValueOption, type=tuple, default=None,
    help="Rename existing platform. If default platform is to be renamed (e.g., `docker`), it will be recreated "
         "(with default values) next time `mlcube` runs."
)
@click.option(
    '--copy_platform', '--copy-platform', required=False, cls=MultiValueOption, type=tuple, default=None,
    help="Copy existing platform. This can be useful for creating new platforms off existing platforms, for instance,"
         "creating a new SSH runner configuration that runs MLCubes on a new remote server."
)
@click.option(
    '--rename_runner', '--rename-runner', required=False, cls=MultiValueOption, type=tuple, default=None,
    help="Rename existing MLCube runner. If platforms exist that reference this runner, users must explicitly provide "
         "`--update-platforms` flag to confirm they want to update platforms' description too."
)
@click.option(
    '--remove_runner', '--remove-runner', required=False, type=str, default=None,
    help="Remove existing runner. If platforms exist that reference this runner, users must explicitly provide "
         "`--remove-platforms` flag to confirm they want to remove platforms too."
)
@help_option
@click.pass_context
def config(ctx: click.core.Context,
           list_all: bool,                          # mlcube config --list
           get: t.Optional[str],                    # mlcube config --get KEY
           create_platform: t.Optional[t.Tuple],    # mlcube config --create-platform RUNNER PLATFORM
           remove_platform: t.Optional[str],        # mlcube config --remove-platform NAME
           rename_platform: t.Optional[t.Tuple],    # mlcube config --rename-platform OLD_NAME NEW_NAME
           copy_platform: t.Optional[t.Tuple],      # mlcube config --copy-platform EXISTING_PLATFORM NEW_PLATFORM
           rename_runner: t.Optional[t.Tuple],      # mlcube config --rename-runner OLD_NAME NEW_NAME
           remove_runner: t.Optional[str]           # mlcube config --remove-runner NAME
           ) -> None:
    """Work with MLCube system settings (similar to `git config`).

    Manage MLCube system settings (these settings define global configuration common for all MLCube runners and
    platforms). When this command runs without arguments, a path to system settings file is printed out. This is useful
    to automate certain operations with system settings. Alternatively, it may be easier to manipulate system settings
    file directly (it is a yaml file).
    """
    print(f"System settings file path = {SystemSettings.system_settings_file()}")
    settings = SystemSettings()

    def _check_tuple(_tuple: t.Tuple, _name: str, _expected_size: int, _expected_value: str) -> None:
        if len(_tuple) != _expected_size:
            raise IllegalParameterValueError(f'--{_name}', ' '.join(_tuple), f"\"{_expected_value}\"")

    try:
        if list_all:
            print(OmegaConf.to_yaml(settings.settings))
        elif get:
            print(OmegaConf.to_yaml(OmegaConf.select(settings.settings, get)))
        elif create_platform:
            _check_tuple(create_platform, 'create_platform', 2, 'RUNNER_NAME PLATFORM_NAME')
            settings.create_platform(create_platform)
        elif remove_platform:
            settings.remove_platform(remove_platform)
        elif rename_platform:
            _check_tuple(rename_platform, 'rename_platform', 2, 'OLD_NAME NEW_NAME')
            settings.copy_platform(rename_platform, delete_source=True)
        elif copy_platform:
            _check_tuple(copy_platform, 'copy_platform', 2, 'EXISTING_PLATFORM NEW_PLATFORM')
            settings.copy_platform(rename_platform, delete_source=False)
        elif rename_runner:
            _check_tuple(rename_runner, 'rename_runner', 2, 'OLD_NAME NEW_NAME')
            update_platforms: bool = '--update-platforms' in ctx.args or '--update_platforms' in ctx.args
            settings.rename_runner(rename_runner, update_platforms=update_platforms)
        elif remove_runner:
            remove_platforms: bool = '--remove-platforms' in ctx.args or '--remove_platforms' in ctx.args
            settings.remove_runner(remove_runner, remove_platforms=remove_platforms)
    except MLCubeError as e:
        logger.error("Command failed, command = '%s' error = '%s'", ' '.join(sys.argv), str(e))


@cli.command(
    name='create', add_help_option=False, cls=MLCubeCommand, epilog=_create_help_epilog,
    context_settings={'max_content_width': _TERMINAL_WIDTH}
)
@help_option
def create() -> None:
    """Create a new Python project from the MLCube cookiecutter template.

    MLCube uses the [cookiecutter](https://cookiecutter.readthedocs.io/) library with the
    [mlcube_cookiecutter](https://github.com/mlcommons/mlcube_cookiecutter) template. The library is not installed
    automatically: install it with `pip install cookiecutter`.
    """
    mlcube_cookiecutter_url = 'https://github.com/mlcommons/mlcube_cookiecutter'
    try:
        from cookiecutter.main import cookiecutter
        proj_dir: str = cookiecutter(mlcube_cookiecutter_url)
        if proj_dir and os.path.isfile(os.path.join(proj_dir, 'mlcube.yaml')):
            Shell.run(['mlcube', 'describe', '--mlcube', proj_dir], on_error='die')
    except ImportError:
        print("Cookiecutter library not found.")
        print("\tInstall it: pip install cookiecutter")
        print(f"\tMore details: {mlcube_cookiecutter_url}")


if __name__ == "__main__":
    cli()
