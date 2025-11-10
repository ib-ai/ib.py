# ib.py

[IB.ai](https://github.com/ib-ai/IB.ai), but in Python. 🐍

NOTE: 🚧 WORK IN PROGRESS! 🚧

This bot is incomplete.


## Usage

To run the bot, you must have [Docker](https://docs.docker.com/get-docker/) and [Python >=3.11](https://www.python.org/downloads/) installed.

1. Close this repository.

```
git clone https://github.com/ib-ai/ib.py.git
cd ib.py
```

2. Specify the bot configuration using `.env` and `config.toml`.

Note: As a rule of thumb, sensitive information goes in `.env` while the `config.toml` should be shareable across people that run the bot. However, the package makes no distinction for the source of the configuration fields.

If run without a `config.toml` file, a blank `config.toml` is created for you:
```toml
# sensitive info - better to define using .env
token=""
db_host=""
db_user=""
db_name=""
db_password=""

# config data
prefix=""
description=""
application_id=0
log_level=""
```

3. Run the docker container. 🚧

By some Docker magic, the bot runs. (This has not been figured out yet.)

```
docker-compose -f docker-compose.postgres.yml up --build
```

# Contributing

Please read the `CONTRIBUTING.md` file to find out more about contributing towards the project.
