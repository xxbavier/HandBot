"""Deployment entry point; importing this module does not start the bot."""

import logging

from bot import HandBot
from settings import ConfigurationError, load_settings


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    try:
        settings = load_settings()
    except ConfigurationError as error:
        raise SystemExit(str(error)) from None

    bot = HandBot(settings)
    bot.run(settings.token, log_handler=None)


if __name__ == "__main__":
    main()
