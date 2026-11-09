# ib.py

The moderation and utility bot for the International Baccalaureate Discord server, written in Python with [discord.py](https://github.com/Rapptz/discord.py). It is the successor to [IB.ai](https://github.com/ib-ai/IB.ai), the original Java bot.

## Features

| Area | What it does |
| --- | --- |
| **Moderation** | Warns, kicks, bans and mutes with numbered cases, a public and a staff mod log, `history` and `lookup`, scheduled expiry for bans and mutes, staff notes, bulk purge |
| **Sticky roles** | Configured roles are restored when a member leaves and rejoins |
| **Message logs** | Edited and deleted messages are logged to a configured channel |
| **Filters and monitors** | Word filters, plus user and message monitoring with grouped patterns |
| **Tags and replies** | Custom tags and automatic replies |
| **Reminders** | Per-user reminders |
| **Voting** | Vote ladders and votes with configurable thresholds |
| **Helper messages** | Helper-role messages and pins |
| **Tickets** | A button panel for bug reports and feature requests, forwarded to a dev channel |
| **Server tools** | Per-server configuration, channel-order snapshots and rollback, role giving, bot messages and embeds, updates |
| **Public commands** | `avatar`, `banner`, `userinfo`, `serverinfo`, `ping` |

Most commands work as both prefix commands and slash commands.

## Requirements

- [Python](https://www.python.org/downloads/) 3.11 or newer
- [uv](https://docs.astral.sh/uv/) for dependency management
- A PostgreSQL database
- A bot application from the [Discord Developer Portal](https://discord.com/developers/applications)

### Discord application setup

1. Create an application and add a bot user.
2. On the **Bot** page, enable the **Server Members Intent** and the **Message Content Intent**. The bot requests all intents.
3. Invite the bot with the `bot` and `applications.commands` scopes. It needs at least these permissions: Manage Roles, Kick Members, Ban Members, Moderate Members, Manage Messages, Read Message History, View Audit Log, Send Messages and Embed Links. The mod logs are driven by audit log events, so without View Audit Log they will not fire.
4. Place the bot's role above any role it needs to manage or moderate, including the mute role and any sticky roles.

## Setup

1. Clone the repository.

```
git clone https://github.com/ib-ai/ib.py.git
cd ib.py
```

2. Install dependencies.

```
uv sync
```

3. Configure the bot with `.env` and `config.toml`.

   Sensitive values (the bot token and database credentials) belong in `.env`. Everything else belongs in `config.toml`. Both files are read through the same configuration layer, so a key can live in either, but `config.toml` takes precedence if a key appears in both. `.env` keys are uppercase (`TOKEN`, `DB_HOST`, and so on).

   If `config.toml` does not exist, the first run creates a blank one and exits so you can fill it in:

```toml
# sensitive info - better to define using .env
token=""
db_host=""
db_port=5432
db_user=""
db_name=""
db_password=""

# config data
prefix=""
description=""
application_id=0
log_level=""
# role IDs that are restored when a member leaves and rejoins
sticky_roles=[]
```

   | Key | Description |
   | --- | --- |
   | `token` | Bot token from the Developer Portal |
   | `application_id` | Application ID from the Developer Portal |
   | `db_host`, `db_port`, `db_user`, `db_name`, `db_password` | PostgreSQL connection details |
   | `prefix` | Default command prefix |
   | `description` | Bot description shown in help |
   | `log_level` | Python logging level, for example `INFO` |
   | `sticky_roles` | List of role IDs to restore on rejoin. Use `[]` for none |

   Per-server settings (mod log channels, mute role, and so on) are stored in the database and set with the `guildconfig` commands.

4. Run the bot.

```
uv run python -m ib_py
```

   Database tables are created automatically on startup.

## Development database

`docker-compose.postgres.yml` starts a local PostgreSQL instance and pgAdmin for development:

```
docker compose -f docker-compose.postgres.yml up -d
```

The credentials in that file are placeholders for local development only. Do not use them for a deployed bot.

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request. Code contributed to this project must be distributed under the GNU GPL v3.

## License

ib.py is free software, licensed under the [GNU General Public License v3.0](LICENSE).

## Contributors

Thanks to everyone who has contributed to ib.py:

- [archivehaze](https://github.com/archivehaze)
- [ilikecubesnstuff](https://github.com/ilikecubesnstuff)
- [NathanealV](https://github.com/NathanealV)
- [Max Gurbanli](https://github.com/MaxGurbanli)
- [Tharun (Indiance)](https://github.com/Indiance)
- [lowee1](https://github.com/lowee1)
- [EdwardTheLegend](https://github.com/EdwardTheLegend)

The full list is on the [contributors graph](https://github.com/ib-ai/ib.py/graphs/contributors).

## Acknowledgements

ib.py builds on the design and the years of work behind [IB.ai](https://github.com/ib-ai/IB.ai), also released under the GPL v3. Thank you to its contributors: Arraying, Jarred Vardy, Ray Clark, Nathaneal Varghese, pants, LenartBucar, xxre0sxx and ilikecubesnstuff.
