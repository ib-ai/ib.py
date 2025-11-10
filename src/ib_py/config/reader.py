import os
import pathlib

import dotenv
import toml


class EnvReader:
    """Reads environment variables from a .env file."""

    def __init__(self, env_file: pathlib.Path = pathlib.Path(".env")) -> None:
        dotenv.load_dotenv(env_file)

    def get(self, key: str, default: str | None = None) -> str | None:
        """Get the value of an environment variable.

        Args:
            key (str): The key of the environment variable.
            default (str | None): The default value to return if the key is not found.

        Returns:
            str | None: The value of the environment variable or the default value.
        """
        return os.getenv(key.upper(), default)


class TomlReader:
    """Reads configuration from a TOML file."""

    def __init__(self, toml_file: pathlib.Path = pathlib.Path("config.toml")) -> None:
        with toml_file.open("r") as f:
            self.config = toml.load(f)

    def get(self, key: str, default: str | None = None) -> str | None:
        """Get the value of a configuration key.

        Args:
            key (str): The key of the configuration.
            default (str | None): The default value to return if the key is not found.

        Returns:
            str | None: The value of the configuration or the default value.
        """
        return self.config.get(key, default)
