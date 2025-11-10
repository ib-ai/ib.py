import logging

from .bot import IBpy
from .config import IBPyConfig

# setup config
config = IBPyConfig()
config.requires("token", "log_level")

# setup logging
package_logger = logging.getLogger("ib_py")
package_logger.setLevel(getattr(logging, config.log_level.upper()))

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
)

# run bot
bot = IBpy()
bot.run(config.token)
