# TradeMate signal rules

This file is the single source of truth for the rules used by the TradeMate signal review. The beginner manual and older strategy notes are supporting educational material; if they differ from this file, this file describes what the bot is configured to check.

## What it does

TradeMate reads market prices and candles, then reports a possible direction or a complete setup for the user to review. It does not place, manage, or close trades. A signal is decision support, not a prediction or a promise of profit.

The bot must use beginner-friendly wording. Do not show internal strategy names, model names, or engine names in welcome text, help, buttons, errors, alerts, scans, or analysis messages.

## Data and time

- Display every analysis time in West Africa Time (WAT, UTC+1). Convert timestamped data to WAT before applying session rules; do not use the computer's local timezone or assume the broker's server clock is WAT.
- Use completed candles for trend and confirmation checks. Reject future-dated or stale quotes and incomplete required history; explain that the data is not ready.
- The configured markets are supported FX pairs and gold from the connected MT5 demo terminal, plus BTC/USD where the selected provider supports the exact symbol. Do not imply that unsupported symbols or feeds were checked.
- Market Scan and automatic Alerts prioritize EURUSD, GBPUSD, XAUUSD, and BTCUSD, resolving each to a unique matching broker symbol in Market Watch. They only scan in the fixed WAT windows below. If a broker symbol is missing or ambiguous, leave it out and report that clearly.
- The London window is 07:00-11:00 WAT. The New York window is 13:00-17:00 WAT. Both are fixed WAT windows; do not shift them with US daylight saving time.
- The Asian range is 02:00-06:00 WAT. Use the configured 03:00, 07:00, 11:00, and 15:00 WAT four-hour reference candles and the documented feeder sequence when building CRT levels.

## Direction and setup conditions

A complete setup requires all blocking checks to pass. A developing direction may be shown as an early heads-up only after distinct scorecard conditions are confirmed. That early heads-up is not an entry signal and must not include unconfirmed entry, stop, or target prices.

Missing required data is unavailable, never a pass. The condition count is out of 14 categories. The confidence score applies the engine's relative weights to those categories and normalizes the result to 0-100; it is not a win probability or a measure of expected profit. A full setup still requires every blocking rule to pass.

## Beginner lessons

- The 20 in-chat lessons are organized into four levels: trading basics, reading the chart, planning and managing risk, and practice and discipline. Each lesson includes a short check-for-understanding quiz.
- Lessons are educational and do not affect signal checks, confidence scores, or Risk Manager calculations.
- Keep lesson explanations plain and avoid claiming that candle shapes prove market intent, identify specific market participants, or guarantee an outcome.
- Lesson completion is tracked only during the current bot session.

## Factors not currently connected to live data

The current price provider does not supply an integrated economic calendar, macroeconomic data, or CFTC positioning feed. Those factors are not checked, scored, or claimed as part of a bot signal. The standalone engine draft's news and positioning classes are placeholders. Add these as signal inputs only after a real, timestamped data source and explicit validation rules are implemented.

## Message contract

An analysis message should show the symbol, direction/status, confidence percentage, current price, and WAT check time. Keep the condition count internal. Show entry, stop, and targets in signal messages only for a complete setup. The latest-signal Risk Manager route requires a freshly checked complete setup; the personal-entry route is separate and must be labeled as the user's own risk plan, not a confirmed signal. If required market data is unavailable, explain that instead of inventing a level. Use plain descriptions for unavailable or pending information. Never label an early heads-up as a ready trade, and never describe the score as the probability of a win.

## Source files

- Maintained signal logic: `src/trademate/strategy.py`.
- Bot messages and button workflow: `src/trademate/bot.py`.
- Optional beginner lessons: `src/trademate/learning.py`.
- `archive/telegram_learning_bot_prototype.py` is an unconnected prototype; it is not a live bot entry point.
- Market feeds: `src/trademate/market_data.py`.
- `multi_asset_watchlist_scanner.py` is an unconnected prototype and is not a signal source. It marks unverified checklist items as passed and uses UTC as if it were WAT; do not import it into the bot.
- The root-level `crt_tsq_execution_engine_v2.py` is a retired prototype and is not connected to the bot. Do not use it to evaluate or send signals.
- The PDF manual and other strategy drafts are educational references. Their win-rate examples, checklists, terminology, and optional indicators do not override this operational specification.
