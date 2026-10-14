"""Start TradeMate AI using Telegram's free long-polling connection."""

import logging

from trademate.bot import create_application
from trademate.config import ConfigurationError, load_settings


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)

    try:
        settings = load_settings()
    except ConfigurationError as exc:
        raise SystemExit(f"Setup needed: {exc}") from None

    logging.getLogger(__name__).info("TradeMate is starting. Use Ctrl+C to stop it.")
    create_application(settings).run_polling()


if __name__ == "__main__":
    main()

