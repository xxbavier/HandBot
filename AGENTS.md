# Repository Guidelines

## Project Structure & Module Organization

HandBot is a Python Discord bot for a Roblox handball league.

- `main.py`: deployment entry point; `bot.py`: client lifecycle and command errors.
- `Utils/`: Discord cogs and command groups. Only `member_setup` is enabled by default; `settings.EXTENSIONS` controls loading.
- `settings.py`: defaults and explicit credential loading; `database.py`: bot-owned MongoDB access.
- `team names.txt`: market permission data; `cached_data/`: cache placeholder.
- `tests/`: offline regression tests; `README.md`: setup and operational notes.
- `requirements.txt`: pinned dependencies; `Procfile`: worker entry point.

## Build, Test, and Development Commands

Run from the repository root using Python 3.10, the tested runtime:

- `python3.10 -m venv .venv` and `source .venv/bin/activate`: create and activate the environment.
- `python -m pip install -r requirements.txt`: install dependencies.
- `python main.py`: start the bot; startup synchronizes global slash commands.
- `python -m compileall -q main.py bot.py settings.py database.py Utils tests`: check syntax.
- `python -m unittest discover -s tests -v`: run mocked regression tests.

No separate build step, formatter, or linter is configured.

## Coding Style & Naming Conventions

Use four-space indentation, focused formatting, and `snake_case` for new functions and variables. Preserve established command names, helpers such as `teamCheck`, and database fields such as `DiscordId` and `SetTime`. Keep handlers asynchronous. Extensions expose `async def setup(bot)`; manually registered command groups need teardown cleanup. Load extensions and sync commands in `setup_hook`, rather than reconnect events. Use the bot-owned database service to keep PyMongo calls off the event loop and avoid import-time connections.

## Testing Guidelines

Use standard-library `unittest` and `IsolatedAsyncioTestCase`; no coverage threshold is configured. Name tests `tests/test_<feature>.py` and mock Discord and MongoDB. Verify permissions, interaction responses, extension lifecycle, and error paths when affected. After offline checks, exercise changed commands and member events in a development guild with isolated MongoDB data.

## Commit & Pull Request Guidelines

History uses short subjects such as `Added member join msg` and `Update main.py`, without enforced prefixes. Prefer concise, descriptive subjects. Describe behavior changes, link relevant issues, list validation, and include screenshots for Discord message changes.

## Security & Configuration

Set `BOT_TOKEN`, or copy `config.example.json` to ignored `config.json`. Database-backed extensions also require `MONGO_ACCESS` or `db_connection`. Environment credentials take precedence. Enable Server Members and Message Content Intents and review IDs before development runs. Keep credentials out of commits and logs; never commit bytecode, virtual environments, or local configuration.
