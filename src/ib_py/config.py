import os
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
    def from_venv(cls):
        token = os.getenv("TOKEN")
        prefix = os.getenv("PREFIX")
        description = os.getenv("DESCRIPTION")
        application_id = os.getenv("APPLICATION_ID")
        db_host = os.getenv("DB_HOST")
        db_user = os.getenv("DB_USER")
        db_name = os.getenv("DB_NAME")
        db_password = os.getenv("DB_PASSWORD")

        if not all(
            (
                token,
                prefix,
                description,
                application_id,
                db_host,
                db_user,
                db_name,
                db_password,
            )
        ):
            raise ValueError(
                "One or more configuration values are missing. "
                "Please provide them via environment variables or a config.toml file."
            )

        return cls(
            token=token,
            prefix=prefix,
            description=description,
            application_id=int(application_id),
            db_host=db_host,
            db_user=db_user,
            db_name=db_name,
            db_password=db_password,
        )


def get_config() -> IBPyConfig:
    return IBPyConfig.from_venv()
