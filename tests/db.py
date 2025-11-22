import inspect
from functools import wraps

from ib_py.config import IBPyConfig

# load config for test database connection parameters
config = IBPyConfig()
config.requires(
    "test_db_host",
    "test_db_port",
    "test_db_name",
    "test_db_user",
    "test_db_password",
)

TORTOISE_ORM = {
    "connections": {
        "default": f"postgres://{config.test_db_user}:{config.test_db_password}@{config.test_db_host}:{config.test_db_port}/{config.test_db_name}"
    },
    "apps": {
        "models": {
            "models": ["ib_py.db.models"],
            "default_connection": "default",
        },
    },
    "use_tz": True,
    "timezone": "UTC",
}


class ensure_table_cleanup:
    def __init__(self, *models):
        self.models = models
        if len(self.models) == 0:
            raise ValueError(
                "ensure_table_cleanup context manager requires at least one model."
            )

    async def __aenter__(self):
        pass

    async def __aexit__(self, exc_type, exc_val, traceback):
        for model in self.models:
            await model.all().delete()
        return False


def cleanup_tables(*models):
    def decorator(target):
        if inspect.isclass(target):
            for attr_name in dir(target):
                if attr_name.startswith("test_"):
                    attr = getattr(target, attr_name)
                    if callable(attr):
                        decorated_method = cleanup_tables(*models)(attr)
                        setattr(target, attr_name, decorated_method)
            return target

        @wraps(target)
        async def wrapper(*args, **kwargs):
            async with ensure_table_cleanup(*models):
                return await target(*args, **kwargs)

        return wrapper

    return decorator
