import json
import os
from pathlib import Path

_path = Path(__file__).parent / "../config.json"
_config = json.load(open(_path, 'r'))

# Create global config (override with environment variables)
token          = os.getenv("TOKEN")          if "TOKEN"          in os.environ else _config['token']
prefix         = os.getenv("PREFIX")         if "PREFIX"         in os.environ else _config['prefix']
description    = os.getenv("DESCRIPTION")    if "DESCRIPTION"    in os.environ else _config['description']
application_id = os.getenv("APPLICATION_ID") if "APPLICATION_ID" in os.environ else _config['application_id']
db_host        = os.getenv("DB_HOST")        if "DB_HOST"        in os.environ else _config['db_host']
db_user        = os.getenv("DB_USER")        if "DB_USER"        in os.environ else _config['db_user']
db_name        = os.getenv("DB_NAME")        if "DB_NAME"        in os.environ else _config['db_name']
db_password    = os.getenv("DB_PASSWORD")    if "DB_PASSWORD"    in os.environ else _config['db_password']