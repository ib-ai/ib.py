# ib.py

IB.ai, but in Python

## Running the bot

To run this project, you need to have [Docker](https://docs.docker.com/get-docker/) and [Python >=3.11](https://www.python.org/downloads/) installed.

1. Clone this repository

```
git clone https://github.com/ib-ai/ib.py.git
```

and navigate to the root directory.

```
cd ib.py
```

2. Copy the `config.example.json`, rename to `config.json`, and replace the relevant values.
The `token` and `application_id` of your application can be found inside your [Discord developer portal](https://discord.com/app).
Example `config.json`:

```
{
  "token": "a long string of random characters",
  "prefix": "&",
  "description": "Discord bot for the r/IBO server. Join here: discord.gg/ibo",
  "application_id": 18-19 digit number, 
  "db_host": "localhost",
  "db_user": "postgres",
  "db_name": "postgres",
  "db_password": "password"
}
```

If you want to inject the config at runtime using environment variables, you need not replace the values in `config.json`.

3. Run the docker container.

```
docker-compose -f docker-compose.postgres.yml up --build
```

# Contributing

Please read the `CONTRIBUTING.md` file to find out more about contributing towards the project.

## Development
We use [PDM](https://pdm-project.org/en/stable/) to manage dependencies for this project and [Ruff](https://docs.astral.sh/ruff/) to handle linting and code formatting.

### 1. Clone this repository

```
git clone https://github.com/ib-ai/ib.py.git
```

and navigate to the root directory.

```
cd ib.py
```

### 2. [Install pdm](https://pdm-project.org/en/stable/#recommended-installation-method)


### 3. Create virtual environment and install dependencies 
(requires either virtualenv, venv, or conda to be installed)

```
pdm install
```

### 4. Using the virtual environment

Either [activate virtual environment](https://pdm-project.org/en/stable/usage/venv/#activate-a-virtualenv) if you are running commands in the terminal

Or

Choose `.venv\Scripts\python.exe` as the interpreter in your IDE.