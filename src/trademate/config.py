"""Read and validate the small set of settings needed to start the bot."""

from dataclasses import dataclass
import os

from dotenv import load_dotenv


class ConfigurationError(ValueError):
    """Raised when a required setting is missing or invalid."""


@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str
    allowed_user_ids: frozenset[int]
    development_mode: bool
    market_data_source: str


def load_settings() -> Settings:
    """Load settings from a local .env file or the computer's environment."""
    load_dotenv()

    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token or token == "replace_with_your_bot_token":
        raise ConfigurationError(
            "Telegram bot token is missing. Copy .env.example to .env and add "
            "the token from BotFather."
        )

    raw_ids = os.getenv("TELEGRAM_ALLOWED_USER_IDS", "").strip()
    development_mode = os.getenv("TRADEMATE_DEV_MODE", "false").strip().lower() == "true"
    market_data_source = os.getenv("TRADEMATE_MARKET_SOURCE", "mt5").strip().lower()
    if market_data_source not in {"mt5", "binance"}:
        raise ConfigurationError("TRADEMATE_MARKET_SOURCE must be mt5 or binance.")
    allowed_ids: set[int] = set()

    if raw_ids and raw_ids != "replace_with_your_telegram_user_id":
        try:
            allowed_ids = {int(value.strip()) for value in raw_ids.split(",") if value.strip()}
        except ValueError as exc:
            raise ConfigurationError(
                "Allowed user IDs must be numbers separated by commas."
            ) from exc

    if not allowed_ids and not development_mode:
        raise ConfigurationError(
            "No allowed Telegram user ID is set. Add your numeric ID to "
            "TELEGRAM_ALLOWED_USER_IDS in .env. For temporary local setup only, "
            "you can explicitly set TRADEMATE_DEV_MODE=true."
        )

    return Settings(
        telegram_bot_token=token,
        allowed_user_ids=frozenset(allowed_ids),
        development_mode=development_mode,
        market_data_source=market_data_source,
    )

