# ib.py

IB.ai, but in Python

## Running the bot

1. Clone this repository:

By https:
```
git clone https://github.com/ib-ai/ib.py.git 
```

By ssh:
```
git clone git@github.com:ib-ai/ib.py.git
```

Go into the cloned directory by entering:
```
cd ib.py
```

You are currently on the `main` branch, however you should be on the `rewrite` branch.

Switch to the rewrite branch:
```
git switch rewrite
```

2. To run this project, you need to have [Docker](https://docs.docker.com/get-docker/) and [Python 3.11](https://www.python.org/downloads/) installed. Click on either of those links to get Docker or Python respectively.


3. Install all requirements by creating a virtual environment and installing dependencies:

```
python -m venv venv
source venv/bin/activate

pip install -r requirements.txt
```

4. Head to the Discord Developer portal and create a new bot application. Invite the new bot
to the server by clicking the `URL Generator` tab under the `OAuth2` tab. Paste this url into 
a web window and accept the bot's invite.


5. Rename the `config.example.json` to `config.json`, and replace the relevant values.
The `token` and `application_id` of your application can be found inside your [Discord developer portal](https://discord.com/app).

Here is an example of a `config.json` file (not including the `token` and `application_id`, since that is for your eyes only):

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

6. Open the docker application on your machine. Run the docker container in the `ib.py` directory with the following command:

```
docker-compose -f docker-compose.postgres.yml up --build
```


7. Run the `bot.py` file in order to connect your bot to the server:

```
python bot.py
```

# Contributing

Please read the `CONTRIBUTING.md` file to find out more about contributing towards the project.
