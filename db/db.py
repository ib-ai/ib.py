from tortoise import Tortoise
import logging
from utils import config

logger = logging.getLogger()

TORTOISE_ORM = {
    "connections": {
        "default": f'postgres://{config.db_user}:{config.db_password}@{config.db_host}:5432/{config.db_name}'
    },
    "apps": {
        "models": {
            "models": ["db.models", "aerich.models"],
            "default_connection": "default",
        },
    },
}


async def db_init():
    # Connect to Postgres DB
    await Tortoise.init(config=TORTOISE_ORM)
    logger.info("Connected to database.")

    # Generate the tables
    await Tortoise.generate_schemas()
