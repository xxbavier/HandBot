# HandBot

A Discord.py bot for Handball: The League. The default extension sends welcome
DMs and public member join/leave messages. Subscriber, market, and admin command
groups remain optional; market demand and admin verdict are existing placeholders.

## Local setup

Use Python 3.10 (the tested runtime for the existing dependency versions).

```sh
python3.10 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
export BOT_TOKEN='your-bot-token'
python main.py
```

Alternatively, copy `config.example.json` to the ignored `config.json` and set
`token`. Environment variables take precedence over local credentials.
`MONGO_ACCESS` or the `db_connection` config key is required only when enabling
the subscription extension. MongoDB is not contacted during import or by the
default member extension.

Enable **Server Members Intent** and **Message Content Intent** in the Discord
Developer Portal. The bot retains the `?` prefix and built-in `?help` command.
It does not request presence or voice events. Ensure it can send messages in the
configured member log channel.
The subscriber nickname command also needs Manage Nicknames and a suitable role
position.

## Configuration and extensions

Review the application, guild, and channel IDs in `settings.py`, and the links and
channel mentions in `Utils/member_setup.py`, before using a development guild.
Add optional modules to `EXTENSIONS` in `settings.py`, for example:

```python
EXTENSIONS = ("Utils.member_setup", "Utils.subscriptions", "Utils.market")
```

Extensions expose `async def setup(bot)`. An extension failure stops startup before
command synchronization, so a partial command list cannot overwrite the registered
list. Global slash commands synchronize once per startup, after extensions load;
reconnects only log readiness. This retains the original global sync behavior, so
use a separate bot application for development.

`main.py` is the entry point for both local runs and the `Procfile` worker.
`bot.py` owns Discord lifecycle, command errors, and database cleanup.
`database.py` provides bot-owned MongoDB access using worker threads, keeping
synchronous PyMongo calls off the Discord event loop. Existing database and field
names are retained. The subscriber command reads and writes cooldowns in
`Subscriptions.NicknameCooldown` using `DiscordId` and `SetTime`.

## Validation

```sh
python -m compileall -q main.py bot.py settings.py database.py Utils tests
python -m unittest discover -s tests -v
```

Tests mock Discord and MongoDB; they do not need tokens or a running database.
They cover startup/reconnect behavior, extension reloads, member messages, blocked
DMs, command permissions, cooldown persistence, and database cleanup. Also exercise
affected events and commands in a development guild before deployment.
