import logging

from tortoise import Tortoise

from ..config import IBPyConfig

# setup config
config = IBPyConfig()
config.requires("db_host", "db_port", "db_name", "db_user", "db_password")

# setup logger
logger = logging.getLogger(__name__)

TORTOISE_ORM = {
    "connections": {
        "default": f"postgres://{config.db_user}:{config.db_password}@{config.db_host}:{config.db_port}/{config.db_name}"
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


async def db_init():
    # Connect to Postgres DB
    await Tortoise.init(config=TORTOISE_ORM)
    logger.info("Connected to database.")

    # Generate the tables
    await Tortoise.generate_schemas()
    logger.info("Database schemas generated.")
