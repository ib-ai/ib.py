# ib.py

IB.ai, but in Python

# Running the bot

1. Navigate to the root directory.

```
cd <path>/ib.py
```

2. Copy the `config.example.json`, rename to `config.json`, and replace the relevant values.
   If you want to inject the config at runtime using environment variables, don't replace the values.

3. Run the docker container.

```
docker-compose -f docker-compose.postgres.yml up --build
```

# Contributing

Please read the `CONTRIBUTING.md` file to find out more about contributing towards the project.
