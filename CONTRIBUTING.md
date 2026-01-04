Thank you so much for your interest in contributing to IB.py!

If you do contribute code, please ensure that you have read and follow the guidelines below.
Any code contributed to IB.py must be distributed with the GNU GPL v3 license.

# Contributing Code

1. Create a fork of the IB.py repository. (If you have appropriate access to this repository, you may skip this step.)
2. Create a new branch, and label it appropriately.
3. Commit and push changes to the branch.
4. When ready, create a pull request from your branch to `rewrite`.
5. Automated checks will run on your code. If they fail, you must push fixes after updating the code.
6. A maintainer will then review your PR, asking for additional changes if needed.
7. Once the review process is complete, the changes will be merged and you can delete the original branch.

# Getting Set Up

This project uses [uv](https://docs.astral.sh/uv/) to manage dependencies.
[ruff](https://docs.astral.sh/ruff/) and [isort](https://pycqa.github.io/isort/index.html) are used for code formatting.

1. Clone this repository.

```
git clone https://github.com/ib-ai/ib.py.git
cd ib.py
```

2. Get set up with [uv](https://docs.astral.sh/uv/)

If you haven't already, install [uv](https://docs.astral.sh/uv/) and make sure the command line interface is available.
Once set up, creating a virtual environment with all the project dependencies is simple:

```
uv sync
```

3. Create a bot application on Discord.

If you haven't already, create a bot application in the Discord developer portal (see the [Pycord Guide](https://guide.pycord.dev/getting-started/creating-your-first-bot)).

4. Run the bot.

The bot is run through the command:

```
uv run python -m ib_py
```

On the first run, it should throw an error that generates a `config.toml` file.
Populate the fields of this file (this requires some info from the Discord developer portal), and run it again.

5. Run the docker container. 🚧

By some Docker magic, the bot runs. (This has not been figured out yet.)

```
docker-compose -f docker-compose.postgres.yml up --build
```

Once the bot is up and running, you are ready to start developing!

6. Enforcing codestyle

This project uses [pre-commit](https://pre-commit.com/) to enforce codestyle with every commit.
Codestyle is enforced with [isort](https://pycqa.github.io/isort/index.html) and [black](https://black.readthedocs.io/en/stable/) (and checked by [ruff](https://docs.astral.sh/ruff/)), along with other usual pre-commit hooks.
See `.pre-commit-config.yaml` for all the details.

Before you push changes, ensure that you [install pre-commit](https://pre-commit.com/#install) and run the `install` command in the root directory:

```
pre-commit install
```

You can also run any of the codestyle checks or autoformatters on the codebase individually via `uv`:

```
uv run isort .
uv run black .
uv run ruff check .
```
