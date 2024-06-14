import base64
import json
import logging
import os
import platform
import typing as t
from enum import Enum
from pathlib import Path
from shlex import shlex

import omegaconf
import requests
import semver

from mlcube.errors import ExecutionError, MLCubeError
from mlcube.shell import Shell
from mlcube.system_settings import SystemSettings

__all__ = [
    "DockerImage",
    "Runtime",
    "Version",
    "ImageSpec",
    "Client",
    "DockerHubClient",
    "parse_key_value_string",
]

logger = logging.getLogger(__name__)


class DockerImage:
    """Working with docker image names.

    https://stackoverflow.com/questions/42115777/parsing-docker-image-tag-into-component-parts

    Args:
        host: Host name, e.g., "docker.synapse.org".
        port: Port number.
        path: Path component of a docker image name (excluding host). It's repository-specific, and can be
            ["USERNAME", "REPOSITORY"], ["PROJECT", "REPOSITORY", "NAME"] etc. This is the only mandatory parameter.
        tag: Image tag. When tag is present, digest must be none.
        digest: Image digest. When present, tag must be none.
    """

    def __init__(
        self,
        host: t.Optional[str] = None,
        port: t.Optional[int] = None,
        path: t.Optional[t.List[str]] = None,
        tag: t.Optional[str] = None,
        digest: t.Optional[str] = None,
    ) -> None:
        _args = {"host": host, "port": port, "path": path, "tag": tag, "digest": digest}
        if isinstance(path, str):
            path = path.split("/")
        if not path:
            raise ValueError(f"Docker image can't have empty path ({_args}).")
        if tag and digest:
            raise ValueError(
                f"Only one of tag/digest can be specified for docker image name ({_args})."
            )

        self.host: t.Optional[str] = host
        self.port: t.Optional[int] = port
        self.path: t.Optional[t.List[str]] = path
        self.tag: t.Optional[str] = tag
        self.digest: t.Optional[str] = digest

    def resolve_host(self) -> str:
        """Return `canonical` host (registry URL without protocol).
        Returns:
            Canonical registry URL, examples are `docker.io`, `nvcr.io`, `docker.synapse.org`.
        """
        if not self.host or self.host == "docker.io":
            return "docker.io"
        host: str = self.host[8:] if self.host.startswith("https://") else self.host
        return host

    def resolve_registry_url(self) -> str:
        """Return registry URL.

        Return `https://registry-1.docker.io` for docker hub or https for canonical host name.
        """
        host: str = self.resolve_host()
        return (
            "https://registry-1.docker.io" if host == "docker.io" else f"https://{host}"
        )

    def resolve_auths_url(self) -> str:
        """Return possible key in `auths` section of docker's JSON config file."""
        host: str = self.resolve_host()
        return "https://index.docker.io/v1/" if host == "docker.io" else host

    def __str__(self) -> str:
        name: str = ""
        if self.host:
            name = self.host
            if self.port:
                name += f":{self.port}"
            name += "/"
        name += "/".join(self.path)
        if self.tag:
            name += f":{self.tag}"
        if self.digest:
            name += f"@{self.digest}"
        return name

    @classmethod
    def from_string(cls, name: str) -> "DockerImage":
        """Construct docker image name from string value.

        Args:
            name: string representation of a docker image, e.g., "mlcommons/hello_world:0.0.1 ".
        Returns:
            DockerImage instance with parsed components.
        """
        # Remove protocol if present
        if name.startswith("docker:"):
            name = name[7:].lstrip("/")

        # Split into parts that are separated by "/".
        parts: t.List[str] = name.strip().split("/")

        # Determine if first part is a host/port pair
        host: t.Optional[str] = None
        port: t.Optional[int] = None
        if len(parts) > 1:
            if parts[0] == "localhost":
                host = parts[0]
            elif "." in parts[0]:
                host_port: t.List[str] = parts[0].split(":")
                host = host_port[0]
                if len(host_port) > 1:
                    port = int(host_port[1])
            if host is not None:
                del parts[0]

        # See of digest is present (must be checked first since it can include ":", e.g., @sha256:dt3...)
        digest: t.Optional[str] = None
        if "@" in parts[-1]:
            image_digest: t.List[str] = parts[-1].split("@")
            parts[-1] = image_digest[0]
            digest = image_digest[1]

        # See if tag is present
        tag: t.Optional[str] = None
        if ":" in parts[-1]:
            image_tag: t.List[str] = parts[-1].split(":")
            parts[-1] = image_tag[0]
            tag = image_tag[1]

        return DockerImage(host, port, parts, tag, digest)


class Runtime(Enum):
    """Container runtime"""

    UNKNOWN = 0
    APPTAINER = 1
    SINGULARITY = 2
    """Singularity / SingularityCE
    
    SingularityCE
        https://github.com/sylabs/singularity/releases/tag/v3.8.0
        This is the first release of SingularityCE 3.8.0, the Community Edition of the Singularity container runtime.
        The package name for this release is now `singularity-ce`.
    
    Singularity
        https://github.com/sylabs/singularity/releases/tag/v3.7.4
        Singularity 3.7.4 is the most recent stable release of Singularity prior to Sylabs' fork from 
        `github.com/hpcng/singularity`.
    """


class Version:
    def __init__(self, runtime: Runtime, version: semver.VersionInfo) -> None:
        self.runtime = runtime
        self.version = version

    def __str__(self) -> str:
        return f"Version(runtime={self.runtime.name}, version={self.version})"

    @classmethod
    def from_version_string(cls, version_string: str) -> "Version":
        version_string = version_string.strip()
        if version_string.startswith("singularity version "):
            runtime, version_string = (
                Runtime.SINGULARITY,
                version_string[20:].strip(),
            )
        elif version_string.startswith("singularity-ce version "):
            runtime, version_string = (
                Runtime.SINGULARITY,
                version_string[23:].strip(),
            )
        elif version_string.startswith("apptainer version "):
            runtime, version_string = Runtime.APPTAINER, version_string[18:].strip()
        elif "/" in version_string:  # Handle old stuff like "x.y.z-pull/123-0a5d"
            runtime, version_string = Runtime.SINGULARITY, version_string.replace(
                "/", "+", 1
            )
        else:
            logger.warning(
                "Version.from_version_string unrecognized container runtime (version_string: %s)",
                version_string,
            )
            runtime = Runtime.UNKNOWN
        return Version(runtime, semver.VersionInfo.parse(version_string))


class ImageSpec(Enum):
    """Build specification format for building singularity images.

    Primary purpose of this enum is to help MLCube guess how to compute the hash for MLCube-based project.
    """

    OTHER = 0
    """Other type pretty much means everything that's not covered by types defined below."""

    DOCKER = 1
    """Docker image ('docker://')."""

    DOCKER_ARCHIVE = 2
    """Local tar files ('docker-archive:')."""

    SINGULARITY = 3
    """Singularity Image File."""


class Client:
    """Singularity container platform client.

    Args:
        singularity: A shell command to run singularity. When it's string, it needs to be constructed so that splitting
        using space character resulted in correct sequence of commands and arguments.
    """

    @classmethod
    def from_env(
            cls, preferred_exec: t.Optional[str] = None, platform_name: t.Optional[str] = None
    ) -> "Client":
        """Create Singularity client trying different commands to run it, return first that succeeds.

        Args:
            preferred_exec: First executable to try (e.g., the one from system settings file or MLCube config).
            platform_name: Try executable in system settings file for this platform. Has lower priority than
                `preferred_exec` if both specified.
        Return:
            Instance of singularity client that this system can run.
        """
        # TODO sergey: what if there are multiple different ways to run singularity (like different wrapper scripts
        #      with pre/post actions, and user wants to use this particular runner) - think about adding `platform` -
        #      the one that user specified on a command line.
        # TODO sergey: what if by trying to run it below we trigger these unwanted pre/post condition actions?
        # Check if system settings file contains information about singularity.
        executables = ["singularity", "sudo singularity", "apptainer", "sudo apptainer"]

        def _add(_exec: str) -> None:
            if _exec in executables:
                executables.remove(_exec)
            executables.insert(0, _exec)

        # Check if preferred executable is provided, and is not one of those above.
        if preferred_exec is not None:
            logger.debug("Client.from_env adding preferred singularity executable '%s'.", preferred_exec)
            _add(preferred_exec)

        if platform_name:
            system_settings = SystemSettings()
            # TODO sergey: we can have other `singularity` and `apptainer` platforms named differently. Need probably to
            #      look at `value -> runner` that contains actual runner type.
            if platform_name in system_settings.platforms:
                preconfigured_platform: omegaconf.DictConfig = system_settings.platforms[platform_name]
                if "singularity" in preconfigured_platform:
                    _add(preconfigured_platform["singularity"])
                    logger.info(
                        "Client.from_env found singularity platform config in MLCube system settings file "
                        "(file=%s, platform=%s). Will try it first or second for detecting singularity CLI client.",
                        system_settings.path.as_posix(),
                        preconfigured_platform["singularity"],
                    )

        logger.debug(
            "Client.from_env will try candidate executables in the following order "
            "(first available will be selected): %s",
            executables,
        )

        for executable in executables:
            try:
                client = Client(executable)
                logger.info(
                    "Client.from_env found singularity (exec=%s, version=%s)",
                    client.singularity,
                    client.version,
                )
                return client
            except ExecutionError:
                logger.warning(
                    "Client.from_env failed to run singularity as: %s", executable
                )
                continue

        raise ExecutionError(
            f"Failed to identify proper singularity client. I tried the following: {executables}."
        )

    def supports_fakeroot(self) -> bool:
        singularity_35 = (
            self.version.runtime == Runtime.SINGULARITY
            and self.version.version >= semver.VersionInfo(major=3, minor=5)
        )
        apptainer = self.version.runtime == Runtime.APPTAINER
        return singularity_35 or apptainer

    def __init__(
        self, singularity: t.Union[str, t.List], version: t.Optional[Version] = None
    ) -> None:
        if isinstance(singularity, str):
            singularity = singularity.split(" ")
        self.singularity: t.List[str] = [c.strip() for c in singularity if c.strip()]
        self.version: t.Optional[Version] = version
        self.init()
        logger.debug(
            "Client.__init__ executable=%s, version=%s", self.singularity, self.version
        )

    def init(self, force: bool = False) -> None:
        if force:
            self.version = None
        if self.version is None:
            version_cmd = self.singularity + ["--version"]
            exit_code, version_string = Shell.run_and_capture_output(version_cmd)
            if exit_code != 0:
                raise ExecutionError(
                    f"Singularity client failed to initialize. The following command ({version_cmd}) returned non-zero"
                    f"exit code ({exit_code}). MLCube cannot run singularity images unless this check passes.",
                    function=f"{self.__class__}.init",
                    args={
                        "force": force,
                        "singularity": self.singularity,
                        "version_cmd": version_cmd,
                    },
                )
            self.version = Version.from_version_string(version_string)
            logger.debug("Client.init version=%s", self.version)

    def build(
        self,
        build_dir: str,
        recipe: str,
        image_dir: str,
        image_name: str,
        build_args: str,
    ) -> None:
        # Get full path to a singularity image. By design, we compute it relative to {mlcube.root}/workspace.
        image_file = Path(image_dir, image_name)
        if image_file.exists():
            logger.info(
                "Client.build won't build SIF image (file exists: %s).",
                image_file,
            )
            return

        # Make sure a directory to store image exists. If paths are like "/opt/...", the call may fail.
        image_file.parent.mkdir(parents=True, exist_ok=True)

        build_dir = Path(
            build_dir
        )  # Let's assume that build context is the root MLCube directory
        if recipe.startswith("docker://") or recipe.startswith("docker-archive:"):
            # https://sylabs.io/guides/3.0/user-guide/build_a_container.html
            # URI beginning with docker:// to build from Docker Hub
            logger.info(
                "Client.build will build SIF image from docker image (image=%s).",
                recipe,
            )
        else:
            # This must be a recipe file. Make sure it exists.
            if not Path(build_dir, recipe).exists():
                raise IOError(
                    f"SIF recipe file does not exist (path={build_dir}, file={recipe})"
                )
            logger.info(
                "Client.build will build SIF image from recipe file (path=%s, file=%s).",
                build_dir,
                recipe,
            )
        try:
            Shell.run(
                ["cd", str(build_dir), ";"]
                + self.singularity
                + ["build", build_args, str(image_file), recipe]
            )
        except ExecutionError as err:
            raise ExecutionError.mlcube_configure_error(
                self.__class__.__name__,
                "Error occurred while building SIF image. See context for more details.",
                **err.context,
            )

    def run(
        self,
        run_args: str,
        volumes: str,
        image_file: str,
        args: t.List,
        entrypoint: t.Optional[str] = None,
    ) -> None:
        try:
            if entrypoint:
                Shell.run(
                    self.singularity
                    + [
                        "exec",
                        run_args,
                        volumes,
                        image_file,
                        entrypoint,
                        " ".join(args),
                    ]
                )
            else:
                Shell.run(
                    self.singularity
                    + ["run", run_args, volumes, image_file, " ".join(args)]
                )
        except ExecutionError as err:
            raise ExecutionError.mlcube_run_error(
                self.__class__.__name__,
                f"Error occurred while running MLCube task. See context for more details.",
                **err.context,
            )

    def image_spec(self, uri: str) -> ImageSpec:
        if uri.startswith("docker://"):
            return ImageSpec.DOCKER

        if uri.startswith("docker-archive:"):
            return ImageSpec.DOCKER_ARCHIVE

        if not Path(uri).is_file():
            logger.warning(
                "Client.image_spec URI (%s) not a file. Can't identify image spec.", uri
            )
            return ImageSpec.OTHER

        exit_code, _ = Shell.run_and_capture_output(
            self.singularity + ["sif", "header", uri]
        )
        if exit_code == 0:
            return ImageSpec.SINGULARITY


class DockerHubClient:
    """Ad-hoc implementation for interacting with remote docker registries."""

    def __init__(self, singularity_: Client) -> None:
        """
        self.token: t.Optional[str] = None

        if singularity.version.runtime == Runtime.APPTAINER:
            config_paths = [
                Path("~/.apptainer/docker-config.json").expanduser(),
                Path("~/.singularity/docker-config.json").expanduser(),
            ]
        else:
            config_paths = [
                Path("~/.singularity/docker-config.json").expanduser(),
                Path("~/.apptainer/docker-config.json").expanduser(),
            ]
        config_paths.append(Path("~/.docker/config.json").expanduser())

        for config_path in config_paths:
            if not config_path.is_file():
                logger.debug("DockerHubClient.__init__ no such file: %s", config_path.as_posix())
                continue
            with open(config_path, 'rt') as file:
                config = json.load(file)
            if not isinstance(config, dict) or \
                    "auths" not in config or \
                    "https://index.docker.io/v1/" not in config["auths"] or \
                    "auth" not in config["auths"]["https://index.docker.io/v1/"]:
                logger.debug("DockerHubClient.__init__: no docker.io credentials in %s", config_path.as_posix())
                continue
            self.token = config["auths"]["https://index.docker.io/v1/"]["auth"]
            logger.debug("DockerHubClient.__init__: found auth credentials in %s.", config_path.as_posix())
            break
        if not self.token:
            logger.warning(
                "DockerHubClient.__init__: could not credentials to authenticate in docker registry in %s",
                [name.as_posix() for name in config_paths]
            )
        """
        pass

    def get_manifest(self, image: t.Union[str, DockerImage]) -> t.Dict:
        """Return image manifest pulled from a remote docker registry.
        Args:
            image: Docker image name, e.g., docker://mlcommons/mnist:0.0.1
        Returns:
            Dictionary containing image manifest pulled from docker registry.
        """
        if isinstance(image, str):
            image = DockerImage.from_string(image)
        logger.debug(
            "DockerHubClient.get_manifest retrieving image manifest for %s.",
            image,
        )

        registry_url: str = image.resolve_registry_url()
        auth_key: str = image.resolve_auths_url()

        logger.debug(
            "DockerHubClient.get_manifest resolved image host (%s) to registry_url=%s and auth_key=%s.",
            image.host,
            registry_url,
            auth_key,
        )

        if len(image.path) == 1:
            logger.warning(
                "DockerHubClient.get_manifest short image name (%s) may result in `insufficient_scope` error, if "
                "this happens you may need to update the image name, e.g. `ubuntu` -> `library/ubuntu`.",
                image.path,
            )

        name: str = "/".join(image.path)
        reference: str = (image.digest or image.tag) or "latest"

        url = f"{registry_url}/v2/{name}/manifests/{reference}"
        headers = {
            "Accept": "application/vnd.docker.distribution.manifest.v2+json,"  # single-arch image
            "application/vnd.oci.image.index.v1+json,"  # multi-arch image
            "application/vnd.oci.image.manifest.v1+json"  # single-arch image
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 401:
            logger.debug(
                "DockerHubClient.get_manifest authentication requested (content=%s, headers=%s",
                response.text.replace("\n", " "),
                response.headers,
            )
            token = _get_authentication_token(
                response.headers.get("www-authenticate", None), auth_key
            )
            headers["Authorization"] = f"Bearer {token}"
            response = requests.get(url, headers=headers)

        if response.status_code != 200:
            raise MLCubeError(
                "DockerHubClient.get_manifest failed to retrieve image manifest "
                "(status_code=%d, content=%s, headers=%s)",
                response.status_code,
                response.text.replace("\n", " "),
                response.headers,
            )

        response = response.json()
        media_type = response.get("mediaType", None)
        if media_type in (
            "application/vnd.docker.distribution.manifest.v2+json",
            "application/vnd.oci.image.manifest.v1+json",
        ):
            ...
        elif media_type == "application/vnd.oci.image.index.v1+json":
            # This is a multi-arch OCI image. We need to identify the platform, and request one more time providing
            # correct image digest.
            manifests: t.List[t.Dict] = response.get("manifests", [])
            manifest, system = _select_manifest(manifests)
            if not manifest:
                raise MLCubeError(
                    f"DockerHubClient.get_manifest failed to find manifest for ({system}) in {manifests}."
                )
            image.tag = None
            image.digest = manifest["digest"]
            logger.debug(
                "DockerHubClient.get_manifest original multi-arch image resolved to %s (system=%s).",
                image,
                system,
            )
            return self.get_manifest(image)

        return response


def _get_authentication_token(www_authenticate: t.Optional[str], auth_key: str) -> str:
    """Retrieve bearer authentication token.

    Args:
        www_authenticate: A string that contains endpoint details where token must be requested. Must start with
            `Bearer`: `Bearer realm="https://nvcr.io/proxy_auth",scope="repository:nvidia/pytorch:pull,push"`.
        auth_key: Docker registry key in `auths` dictionary (for instance, in ~/.docker/config.json).

    Returns:
        Authentication token that can be used with docker registry API.
    """
    if not (www_authenticate and www_authenticate.startswith("Bearer")):
        raise MLCubeError(
            f"_get_authentication_token unsupported authentication method (www_authenticate={www_authenticate})."
        )

    parsed: t.Dict = parse_key_value_string(www_authenticate[7:])
    logger.debug(
        "_get_authentication_token www_authenticate=%s, parsed=%s",
        www_authenticate,
        parsed,
    )

    url: t.Optional[str] = parsed.pop("realm", None)
    if not url:
        raise MLCubeError(
            f"_get_authentication_token unrecognized www_authenticate format (www_authenticate={www_authenticate}, "
            f"parsed={parsed})."
        )
    loggable_url: str = url

    if url.startswith("https://"):
        url = url[8:]

    if os.environ.get("SINGULARITY_DOCKER_USERNAME", None) and os.environ.get(
        "SINGULARITY_DOCKER_PASSWORD", None
    ):
        logger.info(
            "_get_authentication_token found docker username (SINGULARITY_DOCKER_USERNAME) and "
            "password (SINGULARITY_DOCKER_PASSWORD) environment variables."
        )
        loggable_url = f"https://***:***@{url}"
        username, password = (
            os.environ["SINGULARITY_DOCKER_USERNAME"],
            os.environ["SINGULARITY_DOCKER_PASSWORD"],
        )
        url = f"{username}:{password}@{url}"
    else:
        auth_token: t.Optional[str] = _get_auth_token(auth_key)
        if auth_token:
            logger.info("_get_authentication_token using auth token from config file.")
            loggable_url = f"https://***:***@{url}"
            url = base64.b64decode(auth_token).decode() + "@" + url

    url = f"https://{url}"
    logger.debug(
        "_get_authentication_token requesting token at %s for %s.", loggable_url, parsed
    )

    response = requests.get(url, params=parsed)
    if response.status_code != 200:
        raise MLCubeError(
            f"_get_authentication_token could not retrieve authentication token (url={loggable_url}, params={parsed}, "
            f"status_code={response.status_code}, content={response.json()}, headers={response.headers})"
        )
    token = response.json()["token"]
    return token


def _select_manifest(
    manifests: t.List[t.Dict],
) -> t.Tuple[t.Optional[t.Dict], t.Tuple[str, str]]:
    """Find image manifest for the given system using multi-arch image manifest.

    Each element in `manifests` has the following structure:
    ```json
    {
        'digest': 'sha256:dca176c9663a7ba4c1f0e710986f5a25e672842963d95b960191e2d9f7185ebe',
        'mediaType': 'application/vnd.oci.image.manifest.v1+json',
        'platform': {
            'architecture': 'amd64',
            'os': 'linux'
        },
        'size': 424
    }
    ```

    Args:
        manifests: List of multi-arch image manifests.

    Returns:
        A tuple containing one item (dictionary) from the `manifests` or none and a tuple containing system and
        architecture for the given node (e.g., ("linux", "amd64")).
    """
    node = platform.uname()
    system, arch = node.system.lower(), node.machine.lower()
    if arch in ("x86_64", "amd64"):
        arch = "amd64"
    logger.debug(
        "_select_manifest system=%s, arch=%s, manifests=%s", system, arch, manifests
    )
    for manifest in manifests:
        if (
            manifest["platform"]["os"] == system
            and manifest["platform"]["architecture"] == arch
        ):
            return manifest, (system, arch)
    return None, (system, arch)


def _get_auth_token(auth_key: str) -> t.Optional[str]:
    """Return (if found) auth token for docker registry.

    In order for auth token to be present, users need to log in (e.g. `docker login nvcr.io`). It is assumed that
    these tokens (which are base64-encoded "USER:PASSWORD" strings) are stored unencrypted in one of JSON config files
    (e.g., ~/.docker/config.json).

    Args:
        auth_key: A key under which this function searches for the auth token (see `DockerImage.resolve_auths_url`).

    Returns:
         Auth token if found, else None.
    """
    config_files: t.List[Path] = [
        Path.home() / ".singularity" / "docker-config.json",
        Path.home() / ".apptainer" / "docker-config.json",
        Path.home() / ".docker" / "config.json",
    ]

    for config_file in config_files:
        config_file = config_file.expanduser().resolve().absolute()

        if not config_file.is_file():
            logger.debug("_get_auth_token %s does not exist.", config_file.as_posix())
            continue

        with open(config_file, "rt") as fp:
            config: t.Dict = json.load(fp)
        if not (
            isinstance(config, dict) and isinstance(config.get("auths", None), dict)
        ):
            logger.debug(
                "_get_auth_token % exists but content is unsupported.",
                config_file.as_posix(),
            )
            continue

        auths: t.Dict = config["auths"]

        def _get_auth(_config_file: Path, _key: str) -> t.Optional[str]:
            if _key in auths:
                if isinstance(auths[_key], dict) and "auth" in auths[_key]:
                    logger.info(
                        "%s contains auth token for %s", _config_file.as_posix(), _key
                    )
                    return auths[_key]["auth"]
            return None

        auth: t.Optional[str] = _get_auth(config_file, auth_key)
        if not auth:
            if auth_key.startswith("https://"):
                auth = _get_auth(config_file, auth_key[8:])
            else:
                auth = _get_auth(config_file, "https://" + auth_key)
        if auth:
            return auth

        logger.debug(
            "%s does not contain auth token for %s", config_file.as_posix(), auth_key
        )

    return None


def parse_key_value_string(kv_str: str) -> t.Dict:
    """Parse key-value string into dictionaries.

    Multiple key-value pairs are separated with `,` character, while keys and values are separated with `=`. Solution is
    from here: https://stackoverflow.com/questions/38737250/extracting-key-value-pairs-from-string-with-quotes

    Args:
        kv_str: Key value strings, examples are:
            'realm="https://nvcr.io/proxy_auth",scope="repository:nvidia/pytorch:pull,push"'
            'realm="https://auth.docker.io/token",service="registry.docker.io",scope="repository:mlcommons/mnist:pull"'

    Returns:
        Dictionary with parsed KV pairs.
    """
    lexer = shlex(kv_str, posix=True)
    lexer.whitespace = ","
    lexer.wordchars += "="
    return dict(word.split(sep="=", maxsplit=1) for word in lexer)
