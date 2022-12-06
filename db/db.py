from tortoise import Tortoise
import logging
from utils import settings

logger = logging.getLogger()

async def db_init():
    # Connect to Postgres DB
    await Tortoise.init(
        db_url=f'postgres://{settings.config.db_user}:{settings.config.db_password}@{settings.config.db_host}:5432/{settings.config.db_name}',
        modules={'models': ['db.models']}
    )
    logger.info("Connected to database.")

    # Generate the tables
    await Tortoise.generate_schemas()