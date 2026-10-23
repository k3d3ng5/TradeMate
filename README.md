# TradeMate AI

TradeMate AI is a private Telegram companion for careful market analysis,
beginner-friendly trade planning, and trading education. It helps review risk
and exit plans, but it does not place, change, or manage trades in the broker.

The market feature can read a price and completed candles from the MT5 desktop
terminal using `/market SYMBOL` (for example, `/market EURUSD`). `/analyze SYMBOL`
evaluates the deterministic strategy rules for recognized currency pairs, gold, and BTC/USD
symbols. It reports a signal, a confidence score based on confirmed conditions,
and the WAT check time. It only shows entry, stop, and targets when
all required setup and risk/reward checks pass. Binance BTC/USDT is available
for snapshots. Analysis uses the connected MT5 symbol, including BTC/USD when it is listed in Market Watch. Market Scan and Alerts prioritize EURUSD, GBPUSD, XAUUSD, and BTCUSD and run during the London and New York windows. The broker’s exact symbol must be available in MT5 Market Watch. Missing,
stale, or incomplete data causes the analysis to fail closed instead of guessing.

The Risk Manager has two routes. For the latest complete signal, it refreshes the setup,
adds a small 15-minute volatility buffer beyond the stop level, and keeps the setup’s
price targets. For a personal entry, it asks for the market, direction, planned entry,
account balance, and risk limit. It uses a recent 15-minute swing plus the same buffer
for the stop, then estimates a lot size and three price targets. That personal plan is
not a confirmed signal. The bot never submits, changes, or manages orders.

The `/risk` command opens the same guided flow as the Risk Manager button. Choose **Learn**
from the main menu, use `/learn`, or open Help and tap **Learn the basics** to access a
20-lesson course with quizzes. Lessons cover trading basics, chart reading, planning and
risk, and practice habits. Progress is held for the current bot session and does not affect signals.

After sending `/start` once, use the persistent Telegram buttons for Market,
Analyze, Market Scan, Alerts, Risk Manager, Learn, and Help. Market Scan checks the
four core markets during the WAT session windows. Risk Manager offers the latest
complete signal or a separate personal-entry plan based on fresh market prices. Buy/sell
choices appear beneath the question they belong to; you do not need slash commands for
regular use.

## What you need

- A computer with Python 3.10 or newer.
- A Telegram account.
- Your numeric Telegram user ID.
- Prices terminal: A terminal, connected to a broker account, on the same Windows computer that runs this system.

No market-data subscription or AI service is needed for this phase.

## Set it up on Windows

1. Open Telegram, and follow its instructions to create a bot. Copy the token it gives you. Keep the token private.
2. Find your numeric Telegram user ID using a trusted Telegram ID lookup bot.
   Treat it like an address for the allowlist; it is not your password.
3. Open PowerShell in this project folder and run:

   ```powershell
   py -3 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install -r requirements.txt
   Copy-Item .env.example .env
   notepad .env
   ```

4. In `.env`, replace the example values with your bot token and numeric user
   ID. Leave `TRADEMATE_DEV_MODE=false` for normal private use. Save the file.
5. Start bot:

   ```powershell
   $env:PYTHONPATH = "src"
   python -m trademate
   ```

6. Open your broker account. Find the instrument name in Market
   Watch, then try `/market EURUSD` or `/analyze EURUSD` in Telegram, replacing
   `EURUSD` with the exact name shown by your broker.
   Leave the PowerShell window open while you use it. Press `Ctrl+C` to stop
   the bot.

If PowerShell blocks the activation command, you can skip activation and run
`.\.venv\Scripts\python.exe -m pip install -r requirements.txt`, then start
with `$env:PYTHONPATH = "src"; .\.venv\Scripts\python.exe -m trademate`.

## Keep your bot private

- Never share your bot token or post it in a message, screenshot, or code file.
- `.env` is excluded from version control; `.env.example` contains placeholders.
- Keep `TRADEMATE_DEV_MODE=false` outside a brief local setup session. When
  development mode is on and the allowlist is empty, anyone who finds the bot
  can message it.
- If a token is accidentally shared, revoke it.

## Current market-data limits

prices come from the selected broker's feed. Each broker chooses its
own instruments, names, trading hours, and quote details, so the same symbol may
not match another broker or exchange. The bot reads the terminal's bid and ask
and displays their midpoint. broker must be installed and connected on the same
Windows computer that runs the bot. The connector reads prices and candles; it
does not send orders.

To keep using Binance BTC/USDT instead, set `TRADEMATE_MARKET_SOURCE=binance`
in `.env` and restart the bot. Binance remains unavailable if its public API
cannot be reached from your connection.

The current strategy implementation supports currency pairs, gold, and BTC/USD on the connected MT5 terminal.
Stocks and ETFs are not connected. It requires complete WAT-aligned history,
including 1-minute candles for session ranges and order-flow checks; depending
on the broker's candle history, it may return `INSUFFICIENT DATA`. The result is
rule completion only, not a prediction or a guarantee. Backtesting and paper
trading are still required before relying on the rules.

