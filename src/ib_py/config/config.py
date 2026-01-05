import pathlib
import warnings
from importlib import resources

from .reader import EnvReader, TomlReader


class IBPyConfigError(Exception):
    """Custom exception for IBPyConfig errors."""

    pass


class IBPyConfig:
    """Main configuration class for ib.py."""

    _instances = {}

    def __new__(cls, **kwargs):
        """ "
        Implements singleton-inspired pattern to ensure only one instance exists for each env/toml file pair.
        """
        env_file = kwargs.get("env_file", pathlib.Path(".env"))
        toml_file = kwargs.get("toml_file", pathlib.Path("config.toml"))
        key = (env_file, toml_file)
        if key not in cls._instances:
            instance = super(IBPyConfig, cls).__new__(cls)
            cls._instances[key] = instance
        return cls._instances[key]

    def __init__(
        self,
        *,
        env_file: pathlib.Path = pathlib.Path(".env"),
        toml_file: pathlib.Path = pathlib.Path("config.toml"),
    ) -> None:
        if not env_file.exists():
            warnings.warn(
                f"Environment file {env_file} does not exist. Proceeding without it.",
                UserWarning,
            )
        self.env_reader = EnvReader(env_file)
        try:
            self.toml_reader = TomlReader(toml_file)
        except FileNotFoundError as e:
            parent = ".".join(
                __name__.split(".")[:-1]
            )  # get parent from package structure, needed for importlib.resources
            with resources.path(parent, "config.toml") as blank_toml_file:
                with open(toml_file, "w") as f_new, open(blank_toml_file, "r") as f_blank:
                    f_new.write(f_blank.read())
            raise IBPyConfigError(
                f"TOML configuration file not found. A blank template has been created at {toml_file}. Please fill it out and restart the application."
            ) from e

    def __getattr__(self, name: str) -> str | None:
        """Get a configuration value from either the environment or the TOML file.

        Args:
            name (str): The name of the configuration key.
        Returns:
            str | None: The value of the configuration key, or None if not found.
        """
        value = self.toml_reader.get(name)
        if value is None:
            value = self.env_reader.get(name)
        return value

    def requires(self, *keys: str) -> None:
        """Ensure that all required configuration keys are present.

        Args:
            keys (list[str]): A list of required configuration keys.
        Raises:
            IBPyConfigError: If any required configuration key is missing.
        """
        missing_keys = [key for key in keys if self.__getattr__(key) is None]
        if missing_keys:
            raise IBPyConfigError(
                f"Missing required configuration keys: {', '.join(missing_keys)}"
            )
