import json
import os
from pathlib import Path
from dataclasses import dataclass

path = Path(__file__).parent / "../config.json"

@dataclass
class Config:
    token: str
    prefix: str
    description: str
    application_id: int
    db_host: str
    db_user: str
    db_name: str
    db_password: str

def init():
    global config

    config_json= json.load(open(path, 'r'))
    config = Config(**config_json)
    
    # Load from environment variable overrides
    if "TOKEN" in os.environ:
        config['token'] = os.getenv("TOKEN")
    if "PREFIX" in os.environ:
        config['prefix'] = os.getenv("PREFIX")
    if "DESCRIPTION" in os.environ:
        config['description'] = os.getenv("DESCRIPTION")
    if "APPLICATION_ID" in os.environ:
        config['application_id'] = os.getenv("APPLICATION_ID")
    if "DB_HOST" in os.environ:
        config['db_host'] = os.getenv("DB_HOST")
    if "DB_USER" in os.environ:
        config['db_user'] = os.getenv("DB_USER")
    if "DB_NAME" in os.environ:
        config['db_database'] = os.getenv("DB_NAME")
    if "DB_PASSWORD" in os.environ:
        config['db_password'] = os.getenv("DB_PASSWORD")