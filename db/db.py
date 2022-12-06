from tortoise import Tortoise
import logging
from utils import config

logger = logging.getLogger()

async def db_init():
    # Connect to Postgres DB
    await Tortoise.init(
        db_url=f'postgres://{config.db_user}:{config.db_password}@{config.db_host}:5432/{config.db_name}',
        modules={'models': ['db.models']}
    )
    logger.info("Connected to database.")

    # Generate the tables
    await Tortoise.generate_schemas()