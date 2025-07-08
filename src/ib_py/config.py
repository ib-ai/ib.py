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
    def from_env(cls):
        import os
        token = os.environ["TOKEN"]
        prefix = os.environ["PREFIX"]
        description = os.environ["DESCRIPTION"]
        application_id = os.environ["APPLICATION_ID"]
        db_host = os.environ["DB_HOST"]
        db_user = os.environ["DB_USER"]
        db_name = os.environ["DB_NAME"]
        db_password = os.environ["DB_PASSWORD"]

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
    return IBPyConfig.from_env()
