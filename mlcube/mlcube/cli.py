import os
import typing as t
from io import StringIO
from xml.etree.ElementTree import Element

import click
from click.core import DEPRECATED_HELP_NOTICE

from markdown import Markdown


__all__ = ["parse_cli_args", "markdown2text", "MultiValueOption", "Options", "MLCubeCommand", "UsageExamples",
           "parse_cli_args"]

from omegaconf import DictConfig

from mlcube.config import MLCubeConfig
from mlcube.parser import MLCubeDirectory, CliParser
from mlcube.platform import Platform
from mlcube.runner import Runner
from mlcube.system_settings import SystemSettings
from mlcube.validate import Validate


def parse_cli_args(
    ctx: t.Optional[click.core.Context],
    mlcube: str,
    platform: t.Optional[str],
    workspace: t.Optional[str],
    network: t.Optional[str],
    security: t.Optional[str],
    gpus: t.Optional[str],
    memory: t.Optional[str],
    cpu: t.Optional[str],
    resolve: bool,
) -> t.Tuple[t.Optional[t.Type[Runner]], DictConfig]:
    """Parse command line arguments.

    Args:
        ctx: Click context. We need this to get access to extra CLI arguments.
        mlcube: Path to MLCube root directory or mlcube.yaml file.
        platform: Platform to use to run this MLCube (docker, singularity, gcp, k8s etc).
        workspace: Workspace path to use. If not specified, default workspace inside MLCube directory is used.
        network: Networking options defined during MLCube container execution.
        security: Security options defined during MLCube container execution.
        gpus: GPU usage options defined during MLCube container execution.
        memory: Memory RAM options defined during MLCube container execution.
        cpu: CPU options defined during MLCube container execution.
        resolve: if True, compute values in MLCube configuration.
    """
    if mlcube is None:
        mlcube = os.getcwd()
    mlcube_inst: MLCubeDirectory = CliParser.parse_mlcube_arg(mlcube)
    Validate.validate_type(mlcube_inst, MLCubeDirectory)
    if platform in ["docker", "singularity"] and any(
        [network, security, gpus, memory, cpu]
    ):
        mlcube_cli_args, task_cli_args = CliParser.parse_optional_arg(
            platform,
            network,
            security,
            gpus,
            memory,
            cpu,
        )
    elif ctx is not None:
        mlcube_cli_args, task_cli_args = CliParser.parse_extra_arg(*ctx.args)
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
        os.path.join(mlcube_inst.path, mlcube_inst.file),
        mlcube_cli_args,
        task_cli_args,
        runner_config,
        workspace,
        resolve=resolve,
        runner_cls=runner_cls,
    )
    return runner_cls, mlcube_config


def markdown2text(text: str) -> str:
    """Convert Markdown to plain text.

    This approach to convert Markdown text into a plain text is describe in
    this StackOverflow [thread](https://stackoverflow.com/a/54923798/575749).

    Args:
        text: Input text in Markdown format.
    Returns:
        Plain text.
    """
    _markdown: t.Optional[Markdown] = getattr(markdown2text, '_markdown', None)
    if _markdown is None:
        def unmark_element(element: Element, stream: t.Optional[StringIO] = None):
            if stream is None:
                stream = StringIO()
            if element.text:
                stream.write(element.text)
            for sub in element:
                unmark_element(sub, stream)
            if element.tail:
                stream.write(element.tail)
            return stream.getvalue()

        Markdown.output_formats['plain'] = unmark_element
        _markdown = Markdown(output_format='plain')
        _markdown.stripTopLevelTags = False

        setattr(markdown2text, '_markdown', _markdown)

    try:
        text = _markdown.convert(text)
    except (ValueError, UnicodeDecodeError):
        ...
    return text


class MultiValueOption(click.Option):
    """Support multi-value options for [Click](https://click.palletsprojects.com/) library.

    Multi-value options are options that accept multiple values immediately following the option name, e.g.
    `--rename-key OLD_VALUE NEW_VALUE`. This will assign a tuple `(OLD_VALUE, NEW_VALUE)` to a function's`rename_key`
    parameter.
    """
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

    def format_epilog(self, ctx: click.core.Context, formatter: click.formatting.HelpFormatter) -> None:
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
                help_text = markdown2text(self.help)
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
                opts.append((rv[0], markdown2text(rv[1])))
        if opts:
            with formatter.section("Options"):
                formatter.write_dl(opts)

    def format_epilog(self, ctx: click.core.Context, formatter: click.formatting.HelpFormatter) -> None:
        """Format epilog if its type `mlcube.EpilogWithExamples`, else fallback to default implementation."""
        if self.epilog:
            try:
                self.epilog.format_epilog(ctx, formatter)
            except AttributeError:
                super().format_epilog(ctx, formatter)
            except TypeError:
                # TODO: raise an exception or do logging or something else
                ...
        formatter.write_text(f"MLCube online documentation: {OnlineDocs.url()}")


class OnlineDocs:
    """Helper class to build URLs to various parts of MLCube online documentation.

    It is used in writing help messages and documenting options and arguments for MLCube commands.
    """

    _ROOT_URL = "https://mlcommons.github.io/mlcube"
    """Root URL for MLCube online documentation."""

    @staticmethod
    def url(rel_url: t.Optional[str] = None) -> str:
        """Return root URL (if `rel_url` is None) or full URL to a page/section."""
        return f"{OnlineDocs._ROOT_URL}/{rel_url}" if rel_url else OnlineDocs._ROOT_URL

    @staticmethod
    def concept_url(concept: str) -> str:
        """Return URL pointing to the `concept` section."""
        return f"{OnlineDocs._ROOT_URL}/getting-started/concepts/#{concept}"

    @staticmethod
    def runner_url(runner: str) -> str:
        """return URL pointing to a documentation page describing MLCube `runner` runner."""
        return f"{OnlineDocs._ROOT_URL}/runners/{runner}"


class Options:
    """Options for various MLCube commands"""

    help = click.help_option(
        '--help', '-h',
        help="Show help message and exit."
    )

    loglevel = click.option(
        '--log-level', '--log_level', required=False, default='warning',
        type=click.Choice(['critical', 'error', 'warning', 'info', 'debug']),
        help="Logging level is a lower-case string value for Python's logging library (see "
             "[Logging Levels]({log_level}) for more details). Only messages with this logging level or higher are "
             "logged.".format(
                log_level="https://docs.python.org/3/library/logging.html#logging-levels"
             )
    )

    mlcube = click.option(
        '--mlcube', required=False, type=str, default=None, metavar='PATH',
        help="Path to an MLCube project. It can be a [directory path]({mlcube_root_dir}), or a path to an MLCube "
             "[configuration file]({mlcube_config}). When it is a directory path, MLCube runtime assumes this "
             "directory is the MLCube root directory containing `mlcube.yaml` file. When it is a file path, this file "
             "is assumed to be the MLCube configuration file (`mlcube.yaml`), and a parent directory of this file is "
             "considered to be the MLCube root directory. Default value is current directory.".format(
                 mlcube_root_dir=OnlineDocs.concept_url("mlcube-root-directory"),
                 mlcube_config=OnlineDocs.concept_url("mlcube-configuration")
             )
    )

    platform = click.option(
        '--platform', required=False, type=str, default='docker', metavar='NAME',
        help="[Platform]({platform}) name to run MLCube on (a platform is a configured instance of an MLCube runner). "
             "Multiple platforms are supported, including `docker` ([Docker and Podman]({docker})), `singularity` "
             "([Singularity]({singularity})). Other runners are in experimental stage: `gcp` "
             "([Google Cloud Platform]({gcp})), `k8s` ([Kubernetes]({k8s})), `kubeflow` "
             "([KubeFlow]({kubeflow})), ssh ([SSH runner]({ssh})). Default is `docker`. Platforms are defined and "
             "configured in MLCube [system settings file]({sys_settings}).".format(
                 platform=OnlineDocs.concept_url("platform"),
                 docker=OnlineDocs.runner_url("docker-runner"),
                 singularity=OnlineDocs.runner_url("singularity-runner"),
                 gcp=OnlineDocs.runner_url("gcp-runner"),
                 k8s=OnlineDocs.runner_url("kubernetes"),
                 kubeflow=OnlineDocs.runner_url("kubeflow"),
                 ssh=OnlineDocs.runner_url("ssh-runner"),
                 sys_settings=OnlineDocs.url("getting-started/system-settings/")
             )
    )

    task = click.option(
        '--task', required=False, type=str, default=None,
        help="MLCube [task]({task}) name(s) to run, default is `main`. This parameter can take a list of values, in "
             "which case task names are separated with comma (,).".format(
                 task=OnlineDocs.concept_url('task')
             )
    )

    workspace = click.option(
        '--workspace', required=False, type=str, default=None, metavar='PATH',
        help="Location of a [workspace]({workspace}) to store input and output artifacts of MLCube [tasks]({task}). "
             "If not specified (None), `${{MLCUBE_ROOT}}/workspace/` is used.".format(
                 workspace=OnlineDocs.concept_url("workspace"),
                 task=OnlineDocs.concept_url("task")
             )
    )

    parameter = click.option(
        '-P', '-p', required=False, type=str, default=None, metavar='PARAMS', multiple=True,
        help="MLCube [configuration parameter]({config_param}) is a key-value pair. Must start with `-P` or '-p'. The "
             "dot (.) is used to refer to nested parameters, for instance, `-Pdocker.build_strategy=always`. These "
             "parameters have the highest priority and override any other parameters in "
             "[system settings]({sys_settings}) and [MLCube configuration]({config}). ".format(
                 config_param=OnlineDocs.concept_url("mlcube-configuration-parameter"),
                 sys_settings=OnlineDocs.concept_url("system-settings"),
                 config=OnlineDocs.concept_url("mlcube-configuration")
             )
    )

    resolve = click.option(
        '--resolve', is_flag=True,
        help="Resolve [MLCube parameters]({config_param}). The `mlcube` uses [OmegaConf]({omega_conf}) library to "
             "manage its configuration, including [configuration files]({config}), [system settings]({sys_settings}) "
             "files and configuration parameters provided by users on command lines. OmegaConf supports variable "
             "interpolation (when one variables depend on other variables, e.g., `{{'docker.image': "
             "'mlcommons/{{name}}:${{version}}'}}`). When this flag is set to true, the `mlcube` computes actual "
             "values of all variables.".format(
                 config_param=OnlineDocs.concept_url("mlcube-configuration-parameter"),
                 omega_conf="https://omegaconf.readthedocs.io/",
                 config=OnlineDocs.concept_url("mlcube-configuration"),
                 sys_settings=OnlineDocs.concept_url("system-settings")
             )
    )


def _mnist(steps: t.List[str]) -> t.List[str]:
    return [
            'git clone https://github.com/mlcommons/mlcube_examples',
            'cd ./mlcube_examples',
        ] + steps


class UsageExamples:
    show_config = HelpEpilog([
        (
            'Show effective MLCube configuration',
            _mnist(['mlcube show_config --mlcube=mnist'])
        ),
        (
            'Show effective MLCube configuration overriding parameters on a command line',
            _mnist(['mlcube show_config --mlcube=mnist -Pdocker.build_strategy=auto'])
        )
    ])
    """Usage examples for `mlcube show_config` command."""

    configure = HelpEpilog([
        (
            'Configure MNIST MLCube project',
            _mnist(['mlcube configure --mlcube=mnist --platform=docker'])
        )
    ])
    """Usage examples for `mlcube configure` command."""

    run = HelpEpilog([
        (
            'Run MNIST MLCube project',
            _mnist(['mlcube run --mlcube=mnist --platform=docker --task=download,train'])
        )
    ])
    """Usage examples for `mlcube run` command."""

    describe = HelpEpilog([
        (
            'Run MNIST MLCube project',
            _mnist(['mlcube describe --mlcube=mnist'])
        )
    ])
    """Usage examples for `mlcube describe` command."""

    create = HelpEpilog([
        (
            'Create a new empty MLCube project',
            ['mlcube create']
        )
    ])
    """Usage examples for `mlcube create` command."""

    config = HelpEpilog([
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
