"""Telegram commands and the private-user access check."""

import asyncio
import logging
import re
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_CEILING

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters

from trademate.config import Settings
from trademate.learning import LESSONS, TIER_NAMES
from trademate.market_data import (
    BinanceSpotProvider,
    MarketDataError,
    MarketSnapshot,
    MetaTrader5DemoProvider,
)
from trademate.risk import RiskCalculationError, calculate_position_risk, parse_decimal
from trademate.strategy import (
    CheckState,
    DecisionStatus,
    Direction,
    StrategyEvaluation,
    TSQMarketData,
    analyze_tsq,
    find_internal_swings,
    risk_reward_ratio,
)

logger = logging.getLogger(__name__)
MIN_EARLY_SIGNAL_CHECKS = 9
CORE_WATCHLIST = ("EURUSD", "GBPUSD", "XAUUSD", "BTCUSD")
WAT = timezone(timedelta(hours=1), name="WAT")
WAT_SCAN_WINDOWS = ((7, 11, "London"), (13, 17, "New York"))
ATR_PERIOD = 14
ATR_STOP_BUFFER_MULTIPLE = Decimal("0.2")

WELCOME_TEXT = (
    "Welcome to TradeMate AI.\n\n"
    "Check market prices, review possible trade signals, scan your watchlist, or get a risk plan for your own entry.\n\n"
    "Choose an option below to get started. Tap Learn for the beginner course. TradeMate does not place trades."
)

HELP_TEXT = (
    "Choose a button to get started:\n\n"
    "📊 Market — see the latest price for one market.\n"
    "🔎 Analyze — check one market for a possible buy or sell.\n"
    "📡 Market Scan — check EUR/USD, GBP/USD, gold, and Bitcoin once.\n"
    "▶️ Start Alerts — get messages when a possible trade appears during London (07:00–11:00 WAT) or New York (13:00–17:00 WAT).\n"
    "⏹ Stop Alerts — stop those messages.\n"
    "🛡️ Risk Manager — use your latest signal, or enter your own idea for a calculated stop, three targets, and estimated lot size.\n\n"
    "🎓 Learn the basics — a guided beginner course on markets, charts, orders, risk, planning, and practice.\n\n"
    "All times are WAT (UTC+1). TradeMate does not place trades. Signals can be wrong, so review them before acting."
)

BUTTONS = {
    "market": "📊 Market",
    "analyze": "🔎 Analyze",
    "scan": "📡 Market Scan",
    "scalp_start": "▶️ Start Alerts",
    "scalp_stop": "⏹ Stop Alerts",
    "risk": "🛡️ Risk Manager",
    "learn": "🎓 Learn",
    "help": "ℹ️ Help",
    "cancel": "Cancel",
}


def menu_keyboard() -> ReplyKeyboardMarkup:
    rows = [
        [BUTTONS["market"], BUTTONS["analyze"]],
        [BUTTONS["scan"], BUTTONS["risk"]],
        [BUTTONS["scalp_start"], BUTTONS["scalp_stop"]],
        [BUTTONS["learn"], BUTTONS["help"]],
        [BUTTONS["cancel"]],
    ]
    return ReplyKeyboardMarkup(
        rows, resize_keyboard=True, is_persistent=True,
        input_field_placeholder="Choose an option or enter the requested value",
    )


_RISK_CALLBACK_LABELS = {
    "latest": "Use latest signal",
    "own": "My personal entry",
    "long": "Long / Buy",
    "short": "Short / Sell",
    "risk025": "0.25% risk",
    "risk05": "0.5% risk",
    "risk1": "1% risk",
}


def risk_choice_keyboard(*labels: str) -> InlineKeyboardMarkup:
    """Show contextual Risk choices beneath the related chat message."""
    label_to_key = {label: key for key, label in _RISK_CALLBACK_LABELS.items()}
    buttons = [
        InlineKeyboardButton(label, callback_data=f"risk_choice:{label_to_key[label]}")
        for label in labels
    ]
    rows = [buttons[index:index + 2] for index in range(0, len(buttons), 2)]
    return InlineKeyboardMarkup(rows)

_CURRENCIES = frozenset("USD EUR GBP JPY CHF CAD AUD NZD CNY CNH SGD HKD NOK SEK DKK ZAR MXN TRY PLN HUF CZK ILS INR".split())


def strategy_asset_class(symbol: str) -> str | None:
    """Recognize FX pairs, gold, and common broker BTC/USD symbol variants."""
    normalized = re.sub(r"[^A-Z]", "", symbol.upper())
    if normalized.startswith(("XAU", "GOLD")):
        return "gold"
    if normalized.startswith("BTCUSD"):
        return "crypto"
    if len(normalized) >= 6:
        base, quote = normalized[:3], normalized[3:6]
        if base in _CURRENCIES and quote in _CURRENCIES and base != quote:
            return "forex"
    return None


def atr_stop_buffer(candles, tick_size: Decimal) -> Decimal:
    """Return a 0.2 ATR buffer, rounded up to at least one tradable tick."""
    if tick_size <= 0 or len(candles) < ATR_PERIOD + 1:
        raise RiskCalculationError("There isn’t enough completed 15-minute history to calculate an ATR buffer.")
    ranges: list[Decimal] = []
    for index in range(len(candles) - ATR_PERIOD, len(candles)):
        candle = candles[index]
        previous_close = candles[index - 1].close
        ranges.append(max(
            candle.high - candle.low,
            abs(candle.high - previous_close),
            abs(candle.low - previous_close),
        ))
    atr = sum(ranges, Decimal(0)) / Decimal(ATR_PERIOD)
    raw_buffer = max(tick_size, atr * ATR_STOP_BUFFER_MULTIPLE)
    return (raw_buffer / tick_size).to_integral_value(rounding=ROUND_CEILING) * tick_size


def resolve_core_watchlist(visible_symbols: list[str]) -> tuple[list[str], list[str]]:
    """Resolve the four preferred symbols to exact names in the broker terminal."""
    resolved: list[str] = []
    unavailable: list[str] = []
    for preferred in CORE_WATCHLIST:
        exact = [name for name in visible_symbols if re.sub(r"[^A-Z0-9]", "", name.upper()) == preferred]
        matches = exact or [
            name for name in visible_symbols
            if re.sub(r"[^A-Z0-9]", "", name.upper()).startswith(preferred)
            and len(re.sub(r"[^A-Z0-9]", "", name.upper())) <= len(preferred) + 5
        ]
        if len(matches) == 1:
            resolved.append(matches[0])
        else:
            unavailable.append(preferred)
    return resolved, unavailable


def active_wat_session(now: datetime | None = None) -> str | None:
    """Return the active configured session using fixed West Africa Time."""
    local_now = (now or datetime.now(timezone.utc)).astimezone(WAT)
    for start_hour, end_hour, label in WAT_SCAN_WINDOWS:
        if start_hour <= local_now.hour < end_hour:
            return label
    return None


def setup_confidence_score(evaluation: StrategyEvaluation) -> int | None:
    """Score confirmed setup conditions; this is not a probability of profit."""
    if evaluation.status is DecisionStatus.INSUFFICIENT_DATA:
        return None
    weights = {
        "4H close bias": ("trend_close", 10),
        "4H structural order flow": ("trend_4h", 10),
        "4H order flow": ("trend_4h", 10),
        "Daily structural order flow": ("trend_daily", 10),
        "Daily order flow": ("trend_daily", 10),
        "4H alignment": ("trend_agreement", 10),
        "Kill zone": ("active_hours", 5),
        "Current 4H open": ("open_location", 5),
        "4H open location": ("open_location", 5),
        "Reference levels": ("key_levels", 10),
        "Liquidity references": ("key_levels", 10),
        "4H FVG alignment": ("key_levels", 10),
        "Turtle Soup + Model 1": ("reversal", 10),
        "M15 internal structure": ("confirmation", 10),
        "M15 MSS": ("confirmation", 10),
        "Breaker block": ("entry_area", 5),
        "Breaker + OTE": ("entry_area", 5),
        "Entry retest": ("entry_retest", 5),
        "Structural invalidation": ("stop_check", 5),
        "CRT targets": ("targets", 5),
        "Minimum reward": ("reward_risk", 10),
    }
    confirmed = {weights[check.name][0] for check in evaluation.checks
                 if check.name in weights and check.state is CheckState.PASS}
    if any(check.name == "Entry level" and check.state is not CheckState.PASS
           for check in evaluation.checks):
        confirmed.discard("entry_area")
    category_points = {
        "trend_close": 10, "trend_4h": 10, "trend_daily": 10,
        "trend_agreement": 10, "active_hours": 5, "open_location": 5,
        "key_levels": 10, "reversal": 10, "confirmation": 10,
        "entry_area": 5, "entry_retest": 5, "stop_check": 5,
        "targets": 5, "reward_risk": 10,
    }
    raw_score = sum(category_points[category] for category in confirmed)
    maximum_score = sum(category_points.values())
    return min(100, round(raw_score * 100 / maximum_score))


def preliminary_direction(evaluation: StrategyEvaluation):
    """Use a one-sided 4-hour read for an early heads-up when checks are pending."""
    if evaluation.direction.value in {"bullish", "bearish"}:
        return evaluation.direction
    directions = set()
    for check in evaluation.checks:
        if check.state is not CheckState.PASS:
            continue
        if check.name not in {"4H close bias", "4H structural order flow", "4H order flow"}:
            continue
        evidence = check.evidence.lower()
        if "bullish" in evidence:
            directions.add("bullish")
        elif "bearish" in evidence:
            directions.add("bearish")
    if len(directions) != 1:
        return None
    from trademate.strategy import Direction
    return Direction.BULLISH if "bullish" in directions else Direction.BEARISH


def setup_condition_count(evaluation: StrategyEvaluation) -> int | None:
    """Count distinct confirmed checkpoints out of the 14 in the scorecard."""
    if evaluation.status is DecisionStatus.INSUFFICIENT_DATA:
        return None
    categories = {
        "4H close bias": "trend_close",
        "4H structural order flow": "trend_4h",
        "4H order flow": "trend_4h",
        "Daily structural order flow": "trend_daily",
        "Daily order flow": "trend_daily",
        "4H alignment": "trend_agreement",
        "Kill zone": "active_hours",
        "Current 4H open": "open_location",
        "4H open location": "open_location",
        "Reference levels": "key_levels",
        "Liquidity references": "key_levels",
        "4H FVG alignment": "key_levels",
        "Turtle Soup + Model 1": "reversal",
        "M15 internal structure": "confirmation",
        "M15 MSS": "confirmation",
        "Breaker block": "entry_area",
        "Breaker + OTE": "entry_area",
        "Entry retest": "entry_retest",
        "Structural invalidation": "stop_check",
        "CRT targets": "targets",
        "Minimum reward": "reward_risk",
    }
    confirmed = {categories[check.name] for check in evaluation.checks
                 if check.name in categories and check.state is CheckState.PASS}
    if any(check.name == "Entry level" and check.state is not CheckState.PASS
           for check in evaluation.checks):
        confirmed.discard("entry_area")
    return len(confirmed)


def format_analysis(evaluation: StrategyEvaluation, *, symbol: str, source: str, analyzed_at: datetime, last_price: Decimal) -> str:
    """Show a concise result without exposing the internal decision rules."""
    wat = timezone(timedelta(hours=1), name="WAT")
    local_time = analyzed_at.astimezone(wat)
    early_direction = preliminary_direction(evaluation)
    conditions_met = setup_condition_count(evaluation)
    if evaluation.status is DecisionStatus.TRADE_SETUP:
        signal = "BUY" if evaluation.direction.value == "bullish" else "SELL"
    elif (evaluation.status is DecisionStatus.WAIT and early_direction is not None
          and conditions_met is not None and conditions_met >= MIN_EARLY_SIGNAL_CHECKS):
        direction_label = "BUY" if early_direction.value == "bullish" else "SELL"
        signal = f"Possible {direction_label}"
    elif evaluation.status is DecisionStatus.WAIT:
        signal = "WAIT"
    elif evaluation.status is DecisionStatus.AVOID:
        signal = "NO TRADE"
    else:
        signal = "NO SIGNAL"
    status_labels = {
        DecisionStatus.TRADE_SETUP: "Ready to review",
        DecisionStatus.WAIT: "No confirmed signal yet",
        DecisionStatus.AVOID: "No suitable signal",
        DecisionStatus.INSUFFICIENT_DATA: "Unable to assess",
    }
    confidence = setup_confidence_score(evaluation)
    confidence_label = f"{confidence}%" if confidence is not None else "Not available"
    lines = [
        f"{symbol}",
        f"Signal: {signal}",
        f"Status: {status_labels[evaluation.status]}",
        f"Confidence score: {confidence_label}",
        f"Price: {last_price}",
        f"Checked: {local_time:%d %b %Y, %H:%M WAT (UTC+1)}",
    ]
    if (evaluation.status is DecisionStatus.WAIT and early_direction is not None
            and conditions_met is not None and conditions_met >= MIN_EARLY_SIGNAL_CHECKS):
        lines.append("This signal is still developing; price levels are not ready yet.")
    if evaluation.status is DecisionStatus.TRADE_SETUP:
        rr = risk_reward_ratio(
            evaluation.entry, evaluation.stop, evaluation.tp2, evaluation.direction
        )
        lines.extend([
            f"Entry price: {evaluation.entry}", f"Stop-loss price: {evaluation.stop}",
            f"First target: {evaluation.tp1}", f"Final target: {evaluation.tp2}",
            f"Potential gain-to-risk: {rr:.2f} to 1",
            "At the first target, the plan is to close half and move the stop to the entry price.",
        ])
    lines.append("TradeMate does not place trades. Signals can be wrong; you decide whether to act.")
    return "\n".join(lines).strip()

def is_authorized(user_id: int | None, settings: Settings) -> bool:
    """Return whether a Telegram user is allowed to use this private bot."""
    if user_id is None:
        return False
    if settings.allowed_user_ids:
        return user_id in settings.allowed_user_ids
    return settings.development_mode


async def _allow_or_reply(update: Update, settings: Settings) -> bool:
    user = update.effective_user
    if is_authorized(user.id if user else None, settings):
        return True

    logger.warning("Blocked a message from a user outside the allowlist.")
    if update.effective_message:
        await update.effective_message.reply_text(
            "This is a private bot, and this account isn’t on its access list."
        )
    return False


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.application.bot_data["settings"]
    if await _allow_or_reply(update, settings) and update.effective_message:
        context.user_data.pop("guided_flow", None)
        await update.effective_message.reply_text(WELCOME_TEXT, reply_markup=menu_keyboard())


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.application.bot_data["settings"]
    if await _allow_or_reply(update, settings) and update.effective_message:
        await update.effective_message.reply_text(HELP_TEXT, reply_markup=learning_entry_keyboard())


def learning_entry_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("🎓 Learn the basics", callback_data="learn:home")]])


def learning_tier_unlocked(tier: int, completed: set[str]) -> bool:
    if tier == 1:
        return True
    prior_ids = {lesson["id"] for lesson in LESSONS if lesson["tier"] == tier - 1}
    return prior_ids.issubset(completed)


def learning_home_markup(completed: set[str]) -> InlineKeyboardMarkup:
    rows = []
    for tier, name in TIER_NAMES.items():
        unlocked = learning_tier_unlocked(tier, completed)
        label = f"{'📘' if unlocked else '🔒'} {name}"
        rows.append([InlineKeyboardButton(label, callback_data=f"learn:tier:{tier}" if unlocked else "learn:locked")])
    rows.append([InlineKeyboardButton("Back to Help", callback_data="learn:help")])
    return InlineKeyboardMarkup(rows)


async def learning_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.application.bot_data["settings"]
    if not await _allow_or_reply(update, settings) or not update.effective_message:
        return
    completed = set(context.user_data.get("learning_completed", []))
    await update.effective_message.reply_text(
        f"Choose a lesson and work through each section in order. You’ve completed {len(completed)} of {len(LESSONS)} lessons in this chat session.",
        reply_markup=learning_home_markup(completed),
    )


async def learning_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None or not query.data:
        return
    settings: Settings = context.application.bot_data["settings"]
    if not await _allow_or_reply(update, settings):
        await query.answer()
        return
    await query.answer()
    completed = set(context.user_data.get("learning_completed", []))
    data = query.data
    if data == "learn:home":
        await query.edit_message_text(
            f"Choose a lesson and work through each section in order. You’ve completed {len(completed)} of {len(LESSONS)} lessons in this chat session.",
            reply_markup=learning_home_markup(completed),
        )
        return
    if data == "learn:help":
        await query.edit_message_text(HELP_TEXT, reply_markup=learning_entry_keyboard())
        return
    if data == "learn:locked":
        await query.edit_message_text(
            "Finish the lessons in the earlier section to unlock this one.",
            reply_markup=learning_home_markup(completed),
        )
        return
    if data.startswith("learn:tier:"):
        tier = int(data.rsplit(":", 1)[1])
        if not learning_tier_unlocked(tier, completed):
            await query.edit_message_text(
                "Finish the lessons in the earlier section to unlock this one.",
                reply_markup=learning_home_markup(completed),
            )
            return
        lessons = [lesson for lesson in LESSONS if lesson["tier"] == tier]
        rows = [[InlineKeyboardButton(
            f"{'✅' if lesson['id'] in completed else '📖'} {lesson['title']}",
            callback_data=f"learn:lesson:{lesson['id']}",
        )] for lesson in lessons]
        rows.append([InlineKeyboardButton("Back", callback_data="learn:home")])
        await query.edit_message_text(TIER_NAMES[tier], reply_markup=InlineKeyboardMarkup(rows))
        return
    if data.startswith("learn:lesson:"):
        lesson_id = data.rsplit(":", 1)[1]
        lesson = next((item for item in LESSONS if item["id"] == lesson_id), None)
        if lesson is None:
            return
        buttons = [
            [InlineKeyboardButton("Quick check", callback_data=f"learn:quiz:{lesson_id}")],
            [InlineKeyboardButton("Back to lessons", callback_data=f"learn:tier:{lesson['tier']}")],
        ]
        await query.edit_message_text(
            f"{lesson['title']}\n\n{lesson['content']}",
            reply_markup=InlineKeyboardMarkup(buttons),
        )
        return
    if data.startswith("learn:quiz:"):
        lesson_id = data.rsplit(":", 1)[1]
        lesson = next((item for item in LESSONS if item["id"] == lesson_id), None)
        if lesson is None:
            return
        rows = [[InlineKeyboardButton(option, callback_data=f"learn:answer:{lesson_id}:{index}")] for index, option in enumerate(lesson["options"])]
        rows.append([InlineKeyboardButton("Review lesson", callback_data=f"learn:lesson:{lesson_id}")])
        await query.edit_message_text(f"Quick check\n\n{lesson['question']}", reply_markup=InlineKeyboardMarkup(rows))
        return
    if data.startswith("learn:answer:"):
        _, _, lesson_id, raw_answer = data.split(":")
        lesson = next((item for item in LESSONS if item["id"] == lesson_id), None)
        if lesson is None or not raw_answer.isdigit() or int(raw_answer) >= len(lesson["options"]):
            return
        correct = int(raw_answer) == lesson["answer"]
        if correct and lesson_id not in completed:
            completed.add(lesson_id)
            context.user_data["learning_completed"] = sorted(completed)
        message = "Correct." if correct else "Not quite. Review the lesson and try again."
        rows = [[InlineKeyboardButton("Review lesson", callback_data=f"learn:lesson:{lesson_id}")]]
        rows.append([InlineKeyboardButton("Continue learning", callback_data="learn:home")])
        await query.edit_message_text(
            f"{message}\n\n{lesson['explanation']}",
            reply_markup=InlineKeyboardMarkup(rows),
        )


def format_market_snapshot(snapshot: MarketSnapshot) -> str:
    """Format a short market view in the product's configured display timezone."""
    # Nigeria uses West Africa Time year-round (UTC+1). A fixed offset keeps
    # Windows installs from needing an external IANA time-zone database.
    display_timezone = timezone(timedelta(hours=1), name="WAT")
    price_at = snapshot.price_at.astimezone(display_timezone)
    checked_at = snapshot.checked_at.astimezone(display_timezone)
    age_seconds = max(0, int((snapshot.checked_at - snapshot.price_at).total_seconds()))
    def display_price(value: object) -> str:
        rendered = f"{value:,.8f}".rstrip("0").rstrip(".")
        if "." in rendered:
            rendered = rendered.ljust(rendered.index(".") + 3, "0")
        return rendered

    price_text = display_price(snapshot.last_price)
    lines = [
        f"{snapshot.symbol}",
        f"{'Approximate current price' if snapshot.price_label == 'Bid/ask midpoint' else snapshot.price_label}: {price_text} {snapshot.quote_currency}",
        f"{'Checked at' if snapshot.time_note else 'Price time'}: {price_at:%d %b, %H:%M:%S WAT (UTC+1)}",
        *(["The price feed clock differs; this is when TradeMate checked the price."] if snapshot.time_note else []),
        "",
        "Recent prices (at opening / highest / lowest / at closing):",
    ]
    timeframe_labels = {
        "4h": "4 hours",
        "1h": "1 hour",
        "15m": "15 minutes",
        "1m": "1 minute",
    }
    for timeframe, label in timeframe_labels.items():
        candle = snapshot.candles[timeframe]
        closed_at = candle.closed_at.astimezone(display_timezone)
        lines.append(
            f"{label}: {display_price(candle.open)} / {display_price(candle.high)} / "
            f"{display_price(candle.low)} / {display_price(candle.close)} · closed {closed_at:%H:%M WAT}"
        )
    if age_seconds > 120:
        lines.extend(["", f"Heads up: the latest trade is about {age_seconds // 60} minutes old."])
    lines.extend([
        "",
        f"Checked: {checked_at:%d %b %Y, %H:%M:%S WAT (UTC+1)}",
        "This is a market snapshot, not a trade signal.",
    ])
    return "\n".join(lines)


async def market_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.application.bot_data["settings"]
    if not await _allow_or_reply(update, settings) or not update.effective_message:
        return
    if not context.args:
        await update.effective_message.reply_text("Choose 📊 Market below, then enter the symbol.", reply_markup=menu_keyboard())
        return

    await show_market(update, settings, context.args[0])


async def show_market(update: Update, settings: Settings, symbol: str) -> None:
    try:
        if settings.market_data_source == "binance":
            async with BinanceSpotProvider() as provider:
                snapshot = await provider.fetch_snapshot(symbol)
        else:
            snapshot = await MetaTrader5DemoProvider().fetch_snapshot(symbol)
        await update.effective_message.reply_text(format_market_snapshot(snapshot), reply_markup=menu_keyboard())
    except MarketDataError as exc:
        logger.warning("Market request could not be completed: %s", exc)
        await update.effective_message.reply_text(str(exc), reply_markup=menu_keyboard())


async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.application.bot_data["settings"]
    if not await _allow_or_reply(update, settings) or not update.effective_message:
        return
    if not context.args:
        await update.effective_message.reply_text("Choose 🔎 Analyze below, then enter the symbol.", reply_markup=menu_keyboard())
        return
    await show_analysis(update, settings, context.args[0].strip(), context)


async def show_analysis(
    update: Update,
    settings: Settings,
    symbol: str,
    context: ContextTypes.DEFAULT_TYPE | None = None,
) -> None:
    asset_class = strategy_asset_class(symbol)
    if asset_class is None:
        await update.effective_message.reply_text(
        "I can check signals for currency pairs, gold, and BTC/USD. I don’t recognize that symbol, so no signal was checked."
            , reply_markup=menu_keyboard()
        )
        return
    if settings.market_data_source == "binance":
        await update.effective_message.reply_text(
            "The selected price source only provides Bitcoin data. Choose the demo price source to check currency pairs or gold."
            , reply_markup=menu_keyboard()
        )
        return
    try:
        snapshot = await MetaTrader5DemoProvider().fetch_snapshot(symbol)
        evaluation, analyzed_at = evaluate_snapshot(snapshot, asset_class)
        if context is not None:
            if evaluation.status is DecisionStatus.TRADE_SETUP:
                context.user_data["latest_exit_signal"] = {
                    "symbol": snapshot.symbol,
                    "direction": evaluation.direction.value,
                }
            else:
                context.user_data.pop("latest_exit_signal", None)
        await update.effective_message.reply_text(format_analysis(
            evaluation, symbol=snapshot.symbol, source=snapshot.source,
            analyzed_at=analyzed_at, last_price=snapshot.last_price,
        ), reply_markup=menu_keyboard())
    except MarketDataError as exc:
        logger.warning("Analysis request could not be completed: %s", exc)
        await update.effective_message.reply_text(str(exc), reply_markup=menu_keyboard())
    except Exception as exc:
        # Strategy/data edge cases must never leave a Telegram command silent.
        logger.error("Analysis processing failed (%s).", type(exc).__name__)
        await update.effective_message.reply_text(
            "I couldn’t check the signal because some price information failed to load. "
            "Please try again. If it happens again, tell me what the bot showed.", reply_markup=menu_keyboard()
        )


def evaluate_snapshot(snapshot: MarketSnapshot, asset_class: str) -> tuple[StrategyEvaluation, datetime]:
    analyzed_at = datetime.now(timezone.utc)
    evaluation = analyze_tsq(TSQMarketData(
        symbol=snapshot.symbol,
        asset_class=asset_class,
        last_price=snapshot.last_price,
        price_at=snapshot.price_at,
        analyzed_at=analyzed_at,
        candle_history=snapshot.candle_history,
        current_candles=snapshot.current_candles,
        tick_size=snapshot.tick_size,
    ))
    return evaluation, analyzed_at


async def show_exit_levels(
    update: Update,
    settings: Settings,
    symbol: str,
    expected_direction: str,
) -> None:
    """Refresh and show the stop and targets for a complete matching setup."""
    message = update.effective_message
    if message is None:
        return
    asset_class = strategy_asset_class(symbol)
    if asset_class is None:
        await message.reply_text("I can’t check that market. Try a supported currency pair, gold, or BTC/USD.", reply_markup=menu_keyboard())
        return
    if settings.market_data_source == "binance":
        await message.reply_text(
            "Exit levels are available from the MT5 signal check. Switch to your MT5 price source to use this feature.",
            reply_markup=menu_keyboard(),
        )
        return
    await message.reply_text(f"Checking the latest {symbol} setup…", reply_markup=menu_keyboard())
    try:
        snapshot = await MetaTrader5DemoProvider().fetch_snapshot(symbol)
        evaluation, analyzed_at = evaluate_snapshot(snapshot, asset_class)
    except MarketDataError as exc:
        logger.warning("Exit-level check failed: %s", exc)
        await message.reply_text(str(exc), reply_markup=menu_keyboard())
        return
    except Exception as exc:
        logger.error("Exit-level check failed (%s).", type(exc).__name__)
        await message.reply_text(
            "I couldn’t calculate exit levels from the latest prices. Please try again later.",
            reply_markup=menu_keyboard(),
        )
        return
    if evaluation.status is not DecisionStatus.TRADE_SETUP or evaluation.direction.value != expected_direction:
        await message.reply_text(
        f"The latest prices don’t support a clear {'buy' if expected_direction == 'long' else 'sell'} setup for {snapshot.symbol}, so I can’t give reliable exit prices. Try Analyze again later.",
            reply_markup=menu_keyboard(),
        )
        return
    if evaluation.entry is None or evaluation.stop is None or evaluation.tp1 is None or evaluation.tp2 is None or snapshot.tick_size is None:
        await message.reply_text("The completed setup is missing a price level needed to calculate its exits safely.", reply_markup=menu_keyboard())
        return
    try:
        buffer = atr_stop_buffer(snapshot.candle_history.get("15m", ()), snapshot.tick_size)
    except RiskCalculationError as exc:
        await message.reply_text(f"I couldn’t calculate the ATR stop buffer: {exc}", reply_markup=menu_keyboard())
        return
    buffered_stop = evaluation.stop - buffer if expected_direction == "long" else evaluation.stop + buffer
    buffered_rr = risk_reward_ratio(evaluation.entry, buffered_stop, evaluation.tp2, evaluation.direction)
    if buffered_rr < Decimal("2.5"):
        await message.reply_text(
            f"The ATR buffer puts the final target at {buffered_rr:.2f}R, below the 2.5R minimum. Review or skip this setup.",
            reply_markup=menu_keyboard(),
        )
        return
    local_time = analyzed_at.astimezone(WAT)
    await message.reply_text(
        "\n".join([
            f"{snapshot.symbol} · {'Buy' if expected_direction == 'long' else 'Sell'}",
            f"Current price: {snapshot.last_price}",
            f"Entry reference: {evaluation.entry}",
            f"Stop loss: {buffered_stop} (just beyond the level that would invalidate this setup, with extra room for recent price movement)",
            f"Take profit 1: {evaluation.tp1}",
            f"Take profit 2: {evaluation.tp2}",
            "At Take profit 1, the plan is to close half and move the remaining stop to the entry price.",
            f"Checked: {local_time:%d %b %Y, %H:%M WAT (UTC+1)}",
            "The stop includes a 0.2 × 15-minute ATR buffer beyond the setup invalidation level. Targets remain at the setup’s CRT levels. TradeMate does not place trades.",
        ]),
        reply_markup=menu_keyboard(),
    )


async def show_personal_risk_plan(
    update: Update,
    settings: Settings,
    values: dict[str, str],
) -> None:
    """Set a structural stop, three R-based targets, and a risk-sized position."""
    message = update.effective_message
    if message is None:
        return
    if settings.market_data_source == "binance":
        await message.reply_text(
            "Personal lot sizing needs your connected MT5 instrument details. Switch to MT5 and try again.",
            reply_markup=menu_keyboard(),
        )
        return
    try:
        entry = parse_decimal(values["entry"], "Entry price")
        equity = parse_decimal(values["equity"], "Account balance")
        risk_percent = parse_decimal(values["risk_percent"], "Risk percentage")
        direction = values["direction"]
        snapshot = await MetaTrader5DemoProvider().fetch_snapshot(values["symbol"])
        specification = snapshot.risk_specification
        if specification is None:
            raise RiskCalculationError("MT5 did not provide verified lot-size details for this market.")
        candles = snapshot.candle_history.get("15m", ())
        swing_highs, swing_lows = find_internal_swings(candles)
        recent_start = max(0, len(candles) - 40)
        buffer = atr_stop_buffer(candles, specification.tick_size)
        multiples = (Decimal("1"), Decimal("2"), Decimal("2.5"))
        if direction == "long":
            candidates = [swing for swing in swing_lows if swing.index >= recent_start and swing.price < entry]
            if not candidates:
                raise RiskCalculationError("There is no recent confirmed 15-minute low below your entry to place a buy stop behind.")
            stop = candidates[-1].price - specification.tick_size - buffer
            targets = [entry + abs(entry - stop) * multiple for multiple in multiples]
        else:
            candidates = [swing for swing in swing_highs if swing.index >= recent_start and swing.price > entry]
            if not candidates:
                raise RiskCalculationError("There is no recent confirmed 15-minute high above your entry to place a sell stop behind.")
            stop = candidates[-1].price + specification.tick_size + buffer
            targets = [entry - abs(entry - stop) * multiple for multiple in multiples]
        calculation = calculate_position_risk(
            direction=direction,
            entry=entry,
            stop=stop,
            equity=equity,
            equity_currency=specification.currency,
            risk_percent=risk_percent,
            specification=specification,
            target=targets[2],
        )
        checked_at = datetime.now(timezone.utc).astimezone(WAT)
        await message.reply_text(
            "\n".join([
                f"{snapshot.symbol} · {'Buy' if direction == 'long' else 'Sell'}",
                f"Your entry: {entry}",
                f"Calculated stop loss: {stop} (beyond a recent 15-minute high or low, with extra room for recent price movement)",
                f"Take profit 1: {targets[0]} — one stop-distance in your favor; consider closing half and moving the remaining stop to entry.",
                f"Take profit 2: {targets[1]} — two stop-distances in your favor; consider closing another quarter.",
                f"Take profit 3: {targets[2]} — two and a half stop-distances in your favor; this is the final target for the remaining quarter.",
                f"Suggested size: {calculation.quantity} {specification.quantity_unit}",
                f"Estimated loss at stop: {calculation.estimated_loss:.2f} {specification.currency} ({calculation.actual_risk_percent:.2f}% of balance)",
                f"Your risk choice sets the maximum planned loss ({calculation.planned_risk_amount:.2f} {specification.currency}); lot size is rounded down to fit it.",
                "Targets are calculated from the entry-to-stop distance; they do not confirm market support or resistance.",
                f"Checked: {checked_at:%d %b %Y, %H:%M WAT (UTC+1)}",
                "TradeMate does not place trades. Spread, commission, slippage, and gaps can change the actual loss.",
            ]),
            reply_markup=menu_keyboard(),
        )
    except (MarketDataError, RiskCalculationError) as exc:
        await message.reply_text(
            f"I couldn’t calculate a safe plan: {exc}", reply_markup=menu_keyboard()
        )
    except Exception as exc:
        logger.error("Personal risk plan failed (%s).", type(exc).__name__)
        await message.reply_text(
            "I couldn’t load the instrument details needed for lot sizing. Check the MT5 connection and try again.",
            reply_markup=menu_keyboard(),
        )


async def scan_market(update: Update, settings: Settings) -> None:
    """Scan the core four-asset watchlist during configured WAT sessions."""
    message = update.effective_message
    if message is None:
        return
    session = active_wat_session()
    if session is None:
        await message.reply_text(
            "Market Scan is available during the London window (07:00–11:00 WAT) and New York window (13:00–17:00 WAT).",
            reply_markup=menu_keyboard(),
        )
        return
    if settings.market_data_source == "binance":
        await message.reply_text(
            "Market scanning needs MT5. Select the MT5 price source and try again.",
            reply_markup=menu_keyboard(),
        )
        return

    provider = MetaTrader5DemoProvider()
    try:
        visible_symbols = await provider.list_visible_symbols()
    except MarketDataError as exc:
        logger.warning("Market scan could not list symbols: %s", exc)
        await message.reply_text(str(exc), reply_markup=menu_keyboard())
        return
    except Exception as exc:
        logger.error("Market scan could not list symbols (%s).", type(exc).__name__)
        await message.reply_text(
            "I couldn’t read your MT5 watchlist. Please check that MT5 is open and try again.",
            reply_markup=menu_keyboard(),
        )
        return

    symbols, unavailable = resolve_core_watchlist(visible_symbols)
    if not symbols:
        await message.reply_text(
            "I couldn’t match any core market to one unique MT5 Market Watch symbol. Make sure the markets are visible and remove duplicate broker-name variants before scanning again.",
            reply_markup=menu_keyboard(),
        )
        return

    await message.reply_text(
        f"Checking {len(symbols)} of {len(CORE_WATCHLIST)} watchlist markets during the {session} window. This may take a little while.",
        reply_markup=menu_keyboard(),
    )
    candidates: list[dict[str, object]] = []
    checked = 0
    skipped = 0
    session_ended = False
    for symbol in symbols:
        if active_wat_session() != session:
            session_ended = True
            break
        asset_class = strategy_asset_class(symbol)
        if asset_class is None:
            continue
        try:
            snapshot = await provider.fetch_snapshot(symbol)
            evaluation, analyzed_at = evaluate_snapshot(snapshot, asset_class)
            checked += 1
            checks = setup_condition_count(evaluation)
            if checks is None:
                continue
            direction = evaluation.direction
            if direction.value == "neutral":
                direction = preliminary_direction(evaluation)
            if direction is None:
                continue
            if evaluation.status is DecisionStatus.TRADE_SETUP:
                ready = True
            elif evaluation.status is DecisionStatus.WAIT and checks >= MIN_EARLY_SIGNAL_CHECKS:
                ready = False
            else:
                continue
            candidates.append({
                "symbol": snapshot.symbol,
                "evaluation": evaluation,
                "direction": direction,
                "checks": checks,
                "score": setup_confidence_score(evaluation) or 0,
                "ready": ready,
                "analyzed_at": analyzed_at,
                "price": snapshot.last_price,
            })
        except MarketDataError as exc:
            skipped += 1
            logger.warning("Market scan skipped %s: %s", symbol, exc)
        except Exception as exc:
            skipped += 1
            logger.error("Market scan failed for %s (%s).", symbol, type(exc).__name__)

    candidates.sort(key=lambda item: (item["checks"], item["score"]), reverse=True)
    local_time = datetime.now(timezone(timedelta(hours=1), name="WAT"))
    lines = [f"Market scan · {checked} markets checked · {local_time:%H:%M WAT}", ""]
    if not candidates:
        lines.append("No matching signals were found this time.")
    else:
        lines.append("Top matches (up to 4):")
        for rank, item in enumerate(candidates[:4], start=1):
            direction = item["direction"]
            evaluation = item["evaluation"]
            signal = "BUY" if direction.value == "bullish" else "SELL"
            stage = "Ready to review" if item["ready"] else "Developing"
            lines.append(
                f"\n{rank}. {item['symbol']} · {stage}\n"
                f"{signal} · Confidence score: {item['score']}%\n"
                f"Current price: {item['price']}"
            )
            if item["ready"]:
                rr = risk_reward_ratio(
                    evaluation.entry, evaluation.stop, evaluation.tp2, direction
                )
                lines.extend([
                    f"Entry: {evaluation.entry} · Stop-loss: {evaluation.stop}",
                    f"Targets: {evaluation.tp1} and {evaluation.tp2}",
                    f"Possible gain vs. risk: {rr:.2f} to 1",
                    "At the first target, close half and move the stop to the entry price.",
                ])
            else:
                lines.append("Direction only; entry, stop-loss, and targets are not confirmed.")
    if skipped:
        lines.append(f"\n{skipped} symbols could not be checked; results may be incomplete.")
    if unavailable:
        lines.append(f"Not available as a single unambiguous MT5 symbol: {', '.join(unavailable)}. Check your broker’s Market Watch names.")
    if session_ended:
        lines.append("The WAT session ended before the full watchlist could be checked; these results are partial.")
    lines.append("Market conditions can change quickly. TradeMate does not place trades.")
    await message.reply_text("\n".join(lines), reply_markup=menu_keyboard())


async def scalp_alert_loop(application: Application, chat_id: int, settings: Settings) -> None:
    """Check the core four markets during the configured WAT sessions."""
    provider = MetaTrader5DemoProvider()
    last_alerted: dict[tuple[str, str, str], datetime] = {}
    last_unavailable: tuple[str, ...] | None = None
    while True:
        if active_wat_session() is None:
            await asyncio.sleep(60.0)
            continue
        started = asyncio.get_running_loop().time()
        try:
            visible_symbols = await provider.list_visible_symbols()
            symbols, unavailable = resolve_core_watchlist(visible_symbols)
            unavailable_key = tuple(unavailable)
            if unavailable and unavailable_key != last_unavailable:
                await application.bot.send_message(
                    chat_id=chat_id,
                    text=f"Alerts can’t uniquely find these core markets in MT5 Market Watch: {', '.join(unavailable)}. Check your broker’s exact symbol names.",
                    reply_markup=menu_keyboard(),
                )
            last_unavailable = unavailable_key or None
            for symbol in symbols:
                if active_wat_session() is None:
                    break
                asset_class = strategy_asset_class(symbol)
                if asset_class is None:
                    continue
                try:
                    snapshot = await provider.fetch_snapshot(symbol)
                    evaluation, analyzed_at = evaluate_snapshot(snapshot, asset_class)
                    checks = setup_condition_count(evaluation)
                    if checks is None:
                        continue
                    direction = evaluation.direction
                    ready = evaluation.status is DecisionStatus.TRADE_SETUP
                    if direction.value == "neutral":
                        direction = preliminary_direction(evaluation)
                    if direction is None or not ready and not (
                        evaluation.status is DecisionStatus.WAIT and checks >= MIN_EARLY_SIGNAL_CHECKS
                    ):
                        continue

                    wat = timezone(timedelta(hours=1), name="WAT")
                    checked_at = analyzed_at.astimezone(wat)
                    key = (snapshot.symbol, direction.value, str(evaluation.entry) if ready else "early")
                    previous = last_alerted.get(key)
                    if previous and (analyzed_at - previous).total_seconds() < 3600:
                        continue
                    last_alerted[key] = analyzed_at
                    signal = "BUY" if direction.value == "bullish" else "SELL"
                    confidence = setup_confidence_score(evaluation)
                    lines = [
                        f"New signal · {snapshot.symbol}",
                        f"{signal} · Confidence score: {confidence}%",
                        f"Price: {snapshot.last_price}",
                        f"Checked: {checked_at:%d %b %Y, %H:%M WAT (UTC+1)}",
                    ]
                    if ready:
                        rr = risk_reward_ratio(evaluation.entry, evaluation.stop, evaluation.tp2, direction)
                        lines.extend([
                            f"Entry: {evaluation.entry} · Stop-loss: {evaluation.stop}",
                            f"Targets: {evaluation.tp1} and {evaluation.tp2} · Possible gain vs. risk: {rr:.2f} to 1",
                            "At the first target, close half and move the stop to the entry price.",
                        ])
                    else:
                        lines.append("Early direction only; entry, stop-loss, and targets are not confirmed.")
                    lines.append("TradeMate does not place trades; you decide whether to act.")
                    await application.bot.send_message(chat_id=chat_id, text="\n".join(lines), reply_markup=menu_keyboard())
                except MarketDataError as exc:
                    logger.warning("Scalp alert check skipped %s: %s", symbol, exc)
                except Exception as exc:
                    logger.error("Scalp alert check failed for %s (%s).", symbol, type(exc).__name__)
            # Keep the alert cache bounded during long runs.
            now = datetime.now(timezone.utc)
            last_alerted = {key: value for key, value in last_alerted.items()
                            if (now - value).total_seconds() < 86400}
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.error("Scalp alert cycle failed (%s).", type(exc).__name__)
            try:
                await application.bot.send_message(
                    chat_id=chat_id,
                    text="I couldn’t check for new signals. Check that MT5 is open and connected; I’ll try again shortly.",
                    reply_markup=menu_keyboard(),
                )
            except Exception:
                logger.exception("Could not send scalp alert status.")
        elapsed = asyncio.get_running_loop().time() - started
        await asyncio.sleep(max(1.0, 60.0 - elapsed))


async def start_scalp_alerts(update: Update, context: ContextTypes.DEFAULT_TYPE, settings: Settings) -> None:
    message = update.effective_message
    chat = update.effective_chat
    if message is None or chat is None:
        return
    if settings.market_data_source == "binance":
        await message.reply_text("Automatic signal alerts need your connected MT5 price source. Select MT5 and try again.", reply_markup=menu_keyboard())
        return
    tasks = context.application.bot_data.setdefault("scalp_alert_tasks", {})
    existing = tasks.get(chat.id)
    if existing is not None and not existing.done():
        await message.reply_text("Alerts are already running. Tap Stop Alerts to pause them.", reply_markup=menu_keyboard())
        return
    task = asyncio.create_task(scalp_alert_loop(context.application, chat.id, settings))
    tasks[chat.id] = task
    await message.reply_text(
        "Alerts are on. I’ll watch EUR/USD, GBP/USD, gold, and Bitcoin during London (07:00–11:00 WAT) and New York (13:00–17:00 WAT), and message you when a possible trade appears. I won’t place trades. Tap Stop Alerts to turn them off.",
        reply_markup=menu_keyboard(),
    )


async def stop_scalp_alerts(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    chat = update.effective_chat
    if message is None or chat is None:
        return
    tasks = context.application.bot_data.setdefault("scalp_alert_tasks", {})
    task = tasks.pop(chat.id, None)
    if task is None or task.done():
        await message.reply_text("Alerts aren’t running.", reply_markup=menu_keyboard())
        return
    task.cancel()
    await message.reply_text("Alerts stopped.", reply_markup=menu_keyboard())


async def begin_exit_flow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_message:
        return
    context.user_data["guided_flow"] = {"kind": "risk_exits", "step": "mode", "values": {}}
    await update.effective_message.reply_text(
        "Do you want to manage your latest signal, or enter your own trade idea?",
        reply_markup=risk_choice_keyboard("Use latest signal", "My personal entry"),
    )


async def risk_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.application.bot_data["settings"]
    if await _allow_or_reply(update, settings):
        await begin_exit_flow(update, context)


async def risk_choice_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Turn a contextual inline choice into the same input used by the text flow."""
    query = update.callback_query
    if query is None or not query.data:
        return
    key = query.data.removeprefix("risk_choice:")
    label = _RISK_CALLBACK_LABELS.get(key)
    await query.answer()
    if label is None:
        return
    if query.message:
        await query.message.edit_reply_markup(reply_markup=None)
    context.user_data["risk_choice_input"] = label
    await button_or_flow_text(update, context)


async def button_or_flow_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle persistent menu buttons and guided symbol/risk inputs."""
    settings: Settings = context.application.bot_data["settings"]
    if not await _allow_or_reply(update, settings) or not update.effective_message:
        return
    message = update.effective_message
    value = context.user_data.pop("risk_choice_input", (message.text or "").strip())
    flow = context.user_data.get("guided_flow")

    if value == BUTTONS["cancel"]:
        context.user_data.pop("guided_flow", None)
        await message.reply_text("Cancelled. Choose an option:", reply_markup=menu_keyboard())
        return
    if value == BUTTONS["help"]:
        context.user_data.pop("guided_flow", None)
        await message.reply_text(HELP_TEXT, reply_markup=learning_entry_keyboard())
        return
    if value == BUTTONS["market"]:
        context.user_data["guided_flow"] = {"kind": "market"}
        await message.reply_text("Enter the symbol exactly as it appears in your price source.", reply_markup=menu_keyboard())
        return
    if value == BUTTONS["analyze"]:
        context.user_data["guided_flow"] = {"kind": "analyze"}
        await message.reply_text("Enter a currency pair, gold, or BTC/USD symbol, such as EURUSD, XAUUSD, or BTCUSD.", reply_markup=menu_keyboard())
        return
    if value == BUTTONS["scan"]:
        context.user_data.pop("guided_flow", None)
        await scan_market(update, settings)
        return
    if value == BUTTONS["scalp_start"]:
        context.user_data.pop("guided_flow", None)
        await start_scalp_alerts(update, context, settings)
        return
    if value == BUTTONS["scalp_stop"]:
        context.user_data.pop("guided_flow", None)
        await stop_scalp_alerts(update, context)
        return
    if value == BUTTONS["risk"]:
        await begin_exit_flow(update, context)
        return
    if value == BUTTONS["learn"]:
        await learning_command(update, context)
        return

    if not flow:
        await message.reply_text("Choose an option using the buttons below.", reply_markup=menu_keyboard())
        return
    kind = flow["kind"]
    if kind == "market":
        context.user_data.pop("guided_flow", None)
        await show_market(update, settings, value)
        return
    if kind == "analyze":
        context.user_data.pop("guided_flow", None)
        await show_analysis(update, settings, value, context)
        return
    if kind != "risk_exits":
        context.user_data.pop("guided_flow", None)
        await message.reply_text("That flow expired. Choose an option again.", reply_markup=menu_keyboard())
        return

    values = flow["values"]
    step = flow["step"]
    if step == "mode":
        if value == "Use latest signal":
            saved = context.user_data.get("latest_exit_signal")
            if not saved:
                await message.reply_text(
                    "There isn’t a complete signal to use yet. Tap Analyze first, or choose My personal entry.",
                    reply_markup=risk_choice_keyboard("My personal entry"),
                )
                return
            context.user_data.pop("guided_flow", None)
            await show_exit_levels(update, settings, saved["symbol"], saved["direction"])
            return
        if value == "My personal entry":
            flow["step"] = "symbol"
            await message.reply_text("Which market are you considering? Enter its symbol, such as EURUSD, XAUUSD, or BTCUSD.", reply_markup=menu_keyboard())
            return
        await message.reply_text(
            "Choose whether to use your latest signal or enter your own trade idea.",
            reply_markup=risk_choice_keyboard("Use latest signal", "My personal entry"),
        )
        return
    if step == "symbol":
        if strategy_asset_class(value) is None:
            await message.reply_text(
                "I can check currency pairs, gold, and BTC/USD. Enter a supported symbol, such as EURUSD, XAUUSD, or BTCUSD.",
                reply_markup=menu_keyboard(),
            )
            return
        values["symbol"] = value.upper()
        flow["step"] = "direction"
        await message.reply_text(
            f"Are you considering a buy or sell for {values['symbol']}?",
            reply_markup=risk_choice_keyboard("Long / Buy", "Short / Sell"),
        )
    elif step == "direction":
        if value not in {"Long / Buy", "Short / Sell"}:
            await message.reply_text(
                "Choose Buy or Sell for the trade you have in mind.",
                reply_markup=risk_choice_keyboard("Long / Buy", "Short / Sell"),
            )
            return
        values["direction"] = "long" if value == "Long / Buy" else "short"
        flow["step"] = "entry"
        await message.reply_text("What price do you plan to enter at? Enter the price only.", reply_markup=menu_keyboard())
    elif step in {"entry", "equity"}:
        if step == "entry":
            try:
                values["entry"] = str(parse_decimal(value, "Entry price"))
            except RiskCalculationError as exc:
                await message.reply_text(f"{exc} Enter your planned entry price.", reply_markup=menu_keyboard())
                return
            flow["step"] = "equity"
            await message.reply_text("What is your MT5 account balance? Enter the amount shown in your MT5 account.", reply_markup=menu_keyboard())
            return
        if step == "equity":
            try:
                parsed_equity = parse_decimal(value, "Account balance")
                if parsed_equity <= 0:
                    raise RiskCalculationError("Account balance must be greater than zero.")
                values["equity"] = str(parsed_equity)
            except RiskCalculationError as exc:
                await message.reply_text(f"{exc} Enter your account balance.", reply_markup=menu_keyboard())
                return
        flow["step"] = "risk_percent"
        await message.reply_text(
            "Choose how much of your balance you are willing to risk on this trade. The maximum is 1%.",
            reply_markup=risk_choice_keyboard("0.25% risk", "0.5% risk", "1% risk"),
        )
    elif step == "risk_percent":
        risk_map = {"0.25% risk": "0.25", "0.5% risk": "0.5", "1% risk": "1"}
        if value not in risk_map:
            await message.reply_text(
                "Choose one of the risk amounts below.",
                reply_markup=risk_choice_keyboard("0.25% risk", "0.5% risk", "1% risk"),
            )
            return
        values["risk_percent"] = risk_map[value]
        context.user_data.pop("guided_flow", None)
        await show_personal_risk_plan(update, settings, values)


async def unknown_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.application.bot_data["settings"]
    if await _allow_or_reply(update, settings) and update.effective_message:
        await update.effective_message.reply_text(
            "I can help with /start, /help, /learn, /market SYMBOL, /analyze SYMBOL, and /risk. "
            "You can also use the buttons below.", reply_markup=menu_keyboard()
        )


async def report_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log only the error type so tokens and private message contents stay out of logs."""
    error = context.error
    if error is not None:
        logger.error("A bot request failed (%s): %s", type(error).__name__, error)


def create_application(settings: Settings) -> Application:
    """Build the bot application without starting its network connection."""
    async def stop_background_tasks(application: Application) -> None:
        tasks = application.bot_data.get("scalp_alert_tasks", {})
        for task in tasks.values():
            if not task.done():
                task.cancel()
        if tasks:
            await asyncio.gather(*tasks.values(), return_exceptions=True)
        tasks.clear()

    application = Application.builder().token(settings.telegram_bot_token).post_shutdown(stop_background_tasks).build()
    application.bot_data["settings"] = settings
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("learn", learning_command))
    application.add_handler(CommandHandler("market", market_command))
    application.add_handler(CommandHandler("analyze", analyze_command))
    application.add_handler(CommandHandler("risk", risk_command))
    application.add_handler(CallbackQueryHandler(risk_choice_callback, pattern=r"^risk_choice:"))
    application.add_handler(CallbackQueryHandler(learning_callback, pattern=r"^learn:"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, button_or_flow_text))
    application.add_handler(MessageHandler(filters.ALL, unknown_message))
    application.add_error_handler(report_error)
    return application

