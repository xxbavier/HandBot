"""Configuration defaults and explicit credential loading."""

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping

ROOT = Path(__file__).resolve().parent
APPLICATION_ID = 885266060796899329
MEMBER_LOG_CHANNEL_ID = 1375162934250049647
WELCOME_INVITE = "https://discord.gg/vPz6zkATev"

transactions_enabled = True
transactions_channel_id = 1375594636512465006
team_cap = 15
htl_servers = {"League": 1375158752826753084}

# Optional command groups stay disabled until explicitly enabled.
EXTENSIONS = ("Utils.member_setup",)


class ConfigurationError(ValueError):
    """An actionable configuration problem, without credential values."""


@dataclass(frozen=True)
class Settings:
    token: str = field(repr=False)
    mongo_uri: str | None = field(default=None, repr=False)
    application_id: int = APPLICATION_ID
    member_log_channel_id: int = MEMBER_LOG_CHANNEL_ID
    extensions: tuple[str, ...] = EXTENSIONS


def load_settings(
    config_path: Path = ROOT / "config.json",
    environ: Mapping[str, str] | None = None,
) -> Settings:
    """Environment credentials override the optional local config file."""
    environ = os.environ if environ is None else environ
    token = environ.get("BOT_TOKEN")
    mongo_uri = environ.get("MONGO_ACCESS")
    data = {}
    if (not token or not mongo_uri) and config_path.exists():
        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            raise ConfigurationError("Could not read config.json as valid JSON.") from None
        if not isinstance(data, dict):
            raise ConfigurationError("config.json must contain a JSON object.")

    token = token or data.get("token")
    mongo_uri = mongo_uri or data.get("db_connection")
    if not isinstance(token, str) or not token.strip():
        raise ConfigurationError("Set BOT_TOKEN or provide token in config.json.")
    if mongo_uri is not None and (
        not isinstance(mongo_uri, str) or not mongo_uri.strip()
    ):
        raise ConfigurationError("MONGO_ACCESS/db_connection must be a nonempty string.")
    return Settings(token=token, mongo_uri=mongo_uri)
