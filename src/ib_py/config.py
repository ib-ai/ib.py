import tomllib
import os
from pathlib import Path
from dataclasses import dataclass


@dataclass
class IBPyConfig:
    token: str
    prefix: str
    description: str
    application_id: int
    db_host: str
    db_user: str
    db_name: str
    db_password: str

    @classmethod
    def from_toml(cls, path: Path):
        with path.open('rb') as f:
            contents = tomllib.load(f)
        
        token = os.getenv("TOKEN") if "TOKEN" in os.environ else contents["token"]
        prefix = os.getenv("PREFIX") if "PREFIX" in os.environ else contents["prefix"]
        description = (
            os.getenv("DESCRIPTION") if "DESCRIPTION" in os.environ else contents["description"]
        )
        application_id = (
            os.getenv("APPLICATION_ID")
            if "APPLICATION_ID" in os.environ
            else contents["application_id"]
        )
        db_host = os.getenv("DB_HOST") if "DB_HOST" in os.environ else contents["db_host"]
        db_user = os.getenv("DB_USER") if "DB_USER" in os.environ else contents["db_user"]
        db_name = os.getenv("DB_NAME") if "DB_NAME" in os.environ else contents["db_name"]
        db_password = (
            os.getenv("DB_PASSWORD") if "DB_PASSWORD" in os.environ else contents["db_password"]
        )
        return cls(
            token,
            prefix,
            description,
            application_id,
            db_host,
            db_user,
            db_name,
            db_password
        )


# NOTE: hardcoded location, change later
path = Path(__file__).parent / "../../config.toml"
config = IBPyConfig.from_toml(path)
