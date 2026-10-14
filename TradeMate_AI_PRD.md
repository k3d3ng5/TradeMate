# TradeMate AI — Product Requirements Document (PRD)
**Version:** 1.0  
**Status:** Implementation-ready specification for OpenCode  
**Product type:** Private, multi-market trading intelligence and decision-support assistant  
**Primary interface:** Telegram  
**Core engine:** Python  
**Execution model:** Analysis and notifications only; the user places all trades manually

---

## 1. Product summary

TradeMate AI is a private trading companion that retrieves market data, applies the user's defined trading strategy, explains whether the strategy's conditions are met, calculates risk when the necessary instrument specifications are available, and delivers concise results through Telegram.

TradeMate is not an autonomous trading bot. It must not place, modify, or close live trades. It must not claim that a setup is guaranteed to win. Its job is to help the user analyse markets consistently, understand the evidence, control risk, and learn from recorded results.

**Product promise:** See the market. Understand the setup. Control the risk. Learn from every trade.

## 2. Confirmed product decisions

- **Markets in V1:** Forex and gold; cryptocurrency; stocks and ETFs.
- **Strategy:** Start with the user's defined multi-timeframe strategy. Do not invent a separate strategy for each market in V1. Use strategy applicability/configuration rules and clearly report when a market or instrument is not supported by the strategy.
- **Delivery:** Telegram bot.
- **Main engine:** Python script/application. n8n is not required for core functionality.
- **Execution:** Analyse and notify only. User places trades manually.
- **Initial deployment:** Local development first; deploy later to a persistent host.
- **Initial user:** One private user. Design clean interfaces so multi-user support can be added later, but do not build public SaaS complexity into V1.
- **AI role:** Explain structured analysis in natural language; do not let an LLM invent market data, levels, entries, or strategy outcomes.
- **Data and broker credentials:** Use environment variables; never commit secrets.

## 3. Goals and non-goals

### Goals
1. Accept Telegram commands to analyse supported instruments.
2. Retrieve candles/market data from a configurable provider adapter.
3. Normalize data into a common internal format across asset classes.
4. Apply deterministic, testable strategy rules.
5. Return `TRADE SETUP`, `WAIT`, `AVOID`, or `INSUFFICIENT DATA`.
6. Explain which conditions passed, failed, or are still missing.
7. Calculate risk and position size only when inputs and instrument specifications are known.
8. Save analysis snapshots and manually entered trades.
9. Provide basic trade history and performance summaries.
10. Fail safely when data is stale, unavailable, incomplete, or unsupported.

### Non-goals for V1
- Automatic order placement, broker execution, or account management.
- Guaranteed signals, profit promises, or personalised financial advice.
- A public web app or paid subscription system.
- Machine-learning price prediction.
- Unverified sentiment scores presented as facts.
- An LLM making decisions without the deterministic strategy engine.
- Supporting every exchange, broker, ticker, or market-data vendor from day one.

## 4. Users and main use cases

### Primary user
The owner of the private TradeMate AI instance, who wants structured analysis and disciplined manual trading across multiple asset classes.

### Use cases
- “Analyse XAUUSD.”
- “Analyse EURUSD.”
- “Analyse BTCUSDT.”
- “Analyse AAPL.”
- “Why are we waiting?”
- “Calculate risk for this setup.”
- “Log this trade.”
- “Show my last 20 trades.”
- “Review my performance this month.”

## 5. Markets and instrument support

V1 must be architected for these asset classes:

1. **Forex and gold:** e.g. EURUSD, GBPUSD, USDJPY, XAUUSD, subject to provider support.
2. **Cryptocurrency:** e.g. BTCUSDT, ETHUSDT, subject to exchange/provider support.
3. **Stocks and ETFs:** e.g. AAPL, MSFT, SPY, subject to provider, exchange, and subscription support.

Do not assume every provider supports all asset classes or symbols. Create an instrument registry and provider capability checks. Unknown symbols must return a helpful unsupported-instrument message rather than crash.

Each instrument record should include, where available:
- canonical symbol and provider-specific symbol
- asset class
- quote/base currency or trading currency
- exchange/provider
- supported timeframes
- trading-session/calendar information
- tick size, tick value, contract size, lot/quantity step, and minimum quantity where relevant
- whether short selling is supported/available from the selected venue
- data timestamp and source

The engine must not use forex lot-size assumptions for crypto or stocks. Position sizing must be asset-aware and should be unavailable when specifications cannot be verified.

## 6. Strategy requirements

### 6.1 Strategy philosophy
Implement the user's defined strategy as a deterministic rules engine. Keep the strategy configurable and separated from Telegram handlers, data providers, and AI explanation.

### 6.2 Initial multi-timeframe framework
- **4H:** directional bias — bullish, bearish, or neutral, using the configured candle/structure rule.
- **1H:** market structure and important levels.
- **15M:** setup development, including relevant liquidity levels, sweep, rejection, and confirmation.
- **1M:** entry trigger, if supported by the provider and enabled for the instrument.

Relevant levels may include:
- Previous Day High (PDH)
- Previous Day Low (PDL)
- Asian Session High
- Asian Session Low
- configured higher-timeframe swing highs/lows and areas of interest

The Asian session window and timezone must be configurable. The system must not silently assume the machine's local timezone. Default timezone should be configurable and initially set to `Africa/Lagos` for user-facing time; strategy session boundaries must be explicit in configuration.

### 6.3 Rules and conditions
The initial strategy module should support configurable checks such as:
- higher-timeframe bias
- level proximity
- liquidity sweep beyond a defined level
- close back inside/beyond the level as configured
- rejection candle criteria
- lower-timeframe trigger, such as engulfing confirmation
- minimum risk/reward requirement, initially configurable with a default of 1:2
- maximum risk per trade, configurable
- news/event block, only when a reliable calendar integration is configured

Do not hard-code a universal numeric confidence score unless it is derived from documented, tested rules. If a score is shown, label it as a rule-completion score, not a probability of winning.

### 6.4 Cross-market applicability
The user's strategy originates in multi-timeframe price action and liquidity concepts. Do not assume that session liquidity or 1M/15M patterns have equal meaning across stocks, ETFs, crypto, forex, and gold.

For each asset class/instrument configuration:
- declare applicable rules and timeframes
- identify unavailable or inapplicable checks
- return `INSUFFICIENT DATA` or `UNSUPPORTED STRATEGY CONFIGURATION` if critical checks cannot be evaluated
- never silently skip a critical condition and still produce a trade setup

V1 uses the same core strategy philosophy, but the implementation must be honest about where it can be applied. Backtesting and paper-trading validation are required before trusting results.

### 6.5 Status outputs
- **TRADE SETUP:** All mandatory configured conditions are met. This means a setup meets the rule checklist, not that a trade is guaranteed to win.
- **WAIT:** The market can be analysed, but one or more required setup/entry conditions are missing.
- **AVOID:** A configured risk rule, conflicting condition, or explicit filter blocks the setup.
- **INSUFFICIENT DATA:** Data is missing, stale, inconsistent, or the instrument/configuration cannot be evaluated safely.

Every response must include:
- instrument and asset class
- analysis timestamp and timezone
- data source and freshness
- directional bias (if determinable)
- status
- conditions passed
- conditions missing/failed
- relevant levels (only if calculated from data)
- entry/stop/target only when valid and all required inputs exist
- invalidation condition when available
- a concise plain-language explanation
- a clear note that the user places any trade manually

## 7. Risk engine

The risk engine is separate from strategy generation.

### Inputs
- account equity/balance
- account currency
- risk percentage or fixed monetary risk
- entry price
- stop-loss price
- instrument specification
- currency conversion rate where required and available
- quantity/lot increments and minimums

### Outputs
- maximum planned monetary loss
- risk percentage
- position size/quantity when safely calculable
- target price and potential reward if supplied/calculated
- risk/reward ratio
- warnings for missing specifications or unsupported conversions

### Requirements
- Validate that entry and stop are different and directionally sensible.
- Do not calculate a position size if tick/contract/quantity specifications are missing.
- Clearly distinguish theoretical risk from actual realised risk; slippage, spread, commissions, funding, gaps, and execution differences can alter results.
- Respect configured daily and total drawdown thresholds if account tracking is enabled.
- Never encourage increasing risk to recover losses.
- Do not infer a user's live account balance or broker data.
- No ATR-based stops by default. Use the user's defined structural invalidation/stop method; ATR can only be added later if explicitly requested.

## 8. Telegram interface

### Required commands
- `/start` — introduction and main menu
- `/help` — supported commands and examples
- `/markets` — supported asset classes and configured instruments
- `/analyze SYMBOL` — analyse a symbol
- `/market SYMBOL` — concise current market snapshot, if supported
- `/risk` — risk calculator instructions or interactive inputs
- `/logtrade` — start manual trade logging
- `/mytrades` — list recent logged trades
- `/performance` — basic performance summary
- `/learn TOPIC` — explain a trading concept
- `/settings` — show non-secret user configuration

Accept reasonable aliases and natural language only where unambiguous. Unknown requests should return examples, not fail silently.

### Telegram response style
- concise, calm, plain language, beginner-friendly
- no hype, urgency, or claims of certainty
- show status prominently
- distinguish observed data from calculated values and explanations
- use Telegram Markdown safely; escape user-provided values
- never reveal secrets, stack traces, API keys, or internal exception messages

### Access control
V1 is private. Configure `TELEGRAM_ALLOWED_USER_IDS` and reject messages from unapproved users. If the allowlist is missing in production mode, fail closed or require an explicit development-mode setting.

## 9. Data providers and reliability

Use provider interfaces rather than coupling the application to one vendor:
- `MarketDataProvider`
- `InstrumentMetadataProvider` (can initially be combined with market data provider)
- optional `NewsCalendarProvider` in a later phase

A provider adapter should expose normalized OHLCV candles, symbol search/validation where supported, available timeframes, data timestamp, and provider health.

### Data quality rules
- Validate timestamps, chronological ordering, missing candles, duplicate candles, OHLC consistency, and numeric values.
- Detect stale data with asset/session-aware thresholds.
- Do not treat a closed market as a data outage without checking its calendar/session.
- Cache only with explicit freshness rules.
- Record provider/source and analysis timestamp for every result.
- Apply rate limiting and retries with bounded backoff.
- If the primary provider fails, report failure; only use a fallback provider if explicitly configured and symbol mappings are verified.
- Do not scrape websites or bypass provider access controls.
- Do not put API keys in source code or logs.

The exact market-data provider should be selected during setup based on coverage, price, API limits, historical candle availability, and terms. Implement one provider adapter first; keep the interface extensible.

## 10. Trade journal and persistence

Use SQLite for the local V1 prototype, with a repository layer that can later be moved to PostgreSQL.

### Suggested entities

**AnalysisSnapshot**
- id
- symbol
- asset_class
- provider
- analysis_timestamp_utc
- timeframe data references or snapshot metadata
- bias
- status
- levels JSON
- condition results JSON
- entry/stop/target nullable
- explanation
- data freshness metadata

**Trade**
- id
- symbol
- asset_class
- direction
- entry_price
- stop_price
- target_price
- planned_risk_amount
- planned_risk_percent
- position_size nullable
- setup_name
- analysis_snapshot_id nullable
- opened_at
- closed_at nullable
- exit_price nullable
- result_amount nullable
- result_r_multiple nullable
- status (planned/open/closed/cancelled)
- notes

**Settings**
- key/value or typed configuration records for risk preferences, timezone, session times, strategy parameters, provider selection and enabled instruments. Secrets belong in environment variables, not database settings.

Store timestamps in UTC; convert to the configured timezone for display. Use database migrations or a versioned schema strategy.

## 11. Performance review

V1 summaries should include only metrics supported by the recorded data:
- number of closed trades
- wins/losses/breakeven
- win rate
- average win and loss
- average R multiple
- net recorded result, if currency-consistent
- rule adherence when rule-check data was saved
- breakdown by instrument and setup, when sample sizes allow

Explain that a small sample may not be statistically meaningful. Do not imply that historical results guarantee future outcomes. Avoid calculating aggregate monetary P/L across incompatible currencies unless converted using recorded, traceable conversion rates.

## 12. AI explanation layer

The AI layer is optional and must not be required for core deterministic analysis.

Inputs to the language model must be a structured result generated by Python. The model may:
- explain what passed and failed
- answer beginner questions
- summarise a recorded performance report
- rephrase a result in plain language

The model must not:
- invent prices, candles, levels, timestamps, news, or provider results
- override deterministic risk rules
- convert uncertainty into certainty
- make up a trade setup when the strategy engine returns no setup
- place orders or claim it has placed orders

If no LLM key is configured, use deterministic response templates so the bot remains functional.

## 13. Security and safety

- Load secrets from `.env` locally and environment variables in deployment.
- Commit `.env.example`, never `.env`.
- Add `.env`, database files, logs and virtual environments to `.gitignore` as appropriate.
- Restrict Telegram access by user ID.
- Use safe logging with secret redaction.
- Validate and limit all user input.
- Use timeouts and bounded retries for network calls.
- Keep the bot read-only with respect to brokers; do not request broker trading credentials in V1.
- No order-placement endpoints, trading permissions, or live execution code in V1.
- Include clear informational wording: analysis is decision support, not a guarantee or personalised financial advice.

## 14. Error handling and observability

Provide clear user-facing messages for:
- unsupported symbol
- provider unavailable
- rate limit reached
- stale or incomplete data
- unsupported timeframe
- unsupported strategy configuration
- invalid risk inputs
- missing instrument specifications
- database unavailable
- Telegram/network failure

Log structured events including command, symbol, provider, duration, outcome, and correlation/request ID where practical. Do not log secrets or unnecessarily store private message content.

Add `/health` for local/operator diagnostics if access-controlled; do not expose sensitive diagnostic output to arbitrary Telegram users.

## 15. Suggested project structure

```text
trademate-ai/
├── README.md
├── PRD.md
├── OPENCODE_PROMPT.md
├── pyproject.toml
├── .env.example
├── .gitignore
├── src/
│   └── trademate/
│       ├── __init__.py
│       ├── main.py
│       ├── config.py
│       ├── logging_config.py
│       ├── bot/
│       │   ├── __init__.py
│       │   ├── application.py
│       │   ├── handlers.py
│       │   ├── keyboards.py
│       │   └── formatting.py
│       ├── market/
│       │   ├── __init__.py
│       │   ├── models.py
│       │   ├── registry.py
│       │   ├── providers/
│       │   │   ├── __init__.py
│       │   │   ├── base.py
│       │   │   └── selected_provider.py
│       │   └── validation.py
│       ├── strategy/
│       │   ├── __init__.py
│       │   ├── engine.py
│       │   ├── models.py
│       │   ├── rules.py
│       │   ├── levels.py
│       │   └── sessions.py
│       ├── risk/
│       │   ├── __init__.py
│       │   ├── calculator.py
│       │   └── validation.py
│       ├── journal/
│       │   ├── __init__.py
│       │   ├── repository.py
│       │   ├── models.py
│       │   └── performance.py
│       ├── ai/
│       │   ├── __init__.py
│       │   └── explainer.py
│       └── storage/
│           ├── __init__.py
│           ├── database.py
│           └── migrations/
└── tests/
    ├── unit/
    ├── integration/
    └── fixtures/
```

The implementation may adjust filenames where justified, but it must retain separation of concerns and document any material deviation.

## 16. Recommended implementation phases

### Phase 0 — Inspect and plan
- Inspect the repository and existing code before changing anything.
- Identify the Python version and environment.
- Write a concise implementation plan.
- Ask only for essential missing secrets/provider choices; do not fabricate credentials.
- Choose a maintained Telegram library and a market-data provider after checking project constraints and provider coverage.

### Phase 1 — Runnable foundation
- Package/configuration, logging, Telegram `/start` and `/help`, access allowlist, `.env.example`, tests and README.
- App starts cleanly and reports missing configuration clearly.

### Phase 2 — One provider and normalized data
- Implement one selected provider adapter.
- Fetch and validate OHLCV for one representative instrument from each supported asset class if the provider supports them.
- If the provider does not cover all asset classes, document the gap and define separate adapters without pretending coverage exists.

### Phase 3 — Strategy engine
- Implement levels and deterministic rule evaluation.
- Build unit tests with synthetic OHLCV fixtures for bullish, bearish, wait, avoid and insufficient-data cases.
- Store rule-by-rule evidence in the analysis result.
- Do not present unvalidated outputs as profitable signals.

### Phase 4 — Telegram analysis
- Add `/analyze SYMBOL`.
- Return status, bias, conditions, levels, timestamp, source and data quality.
- Ensure errors return a friendly response.

### Phase 5 — Risk calculator
- Add validated risk calculations.
- Only calculate position size when specifications and required conversions are available.
- Add tests for direction, invalid stops, quantity rounding and missing metadata.

### Phase 6 — Journal and performance
- Add SQLite persistence, manual trade logging, history and basic summaries.
- Test persistence and calculations.

### Phase 7 — AI explanations and hardening
- Add optional LLM explanation with deterministic fallback.
- Add rate limits, retries, access controls, health checks and documentation.
- Run the complete test suite and document remaining limitations.

## 17. Acceptance criteria

The V1 is ready for private testing when:
1. The application starts from documented commands.
2. Telegram `/start` and `/help` work.
3. Unauthorized Telegram users are rejected.
4. `/analyze SYMBOL` returns a structured result for a supported instrument.
5. Unknown symbols and unavailable providers return safe, useful messages.
6. Market data is validated for staleness and integrity.
7. The same candles and configuration produce the same deterministic strategy result.
8. Each result shows passed, failed and missing conditions.
9. No setup is returned if critical strategy checks cannot be evaluated.
10. Risk calculations are tested and do not assume incorrect asset specifications.
11. Manual trades persist and can be retrieved.
12. Performance summaries use only recorded, compatible data.
13. No live order execution code or broker trading credentials are required.
14. `.env` and secrets are excluded from version control.
15. Unit and integration tests pass; README documents setup, configuration, commands, limitations and tests.

---

# OpenCode Build Prompt

You are the senior Python engineer implementing TradeMate AI. Build the application described in `PRD.md` in the current repository.

## Product constraints
- TradeMate is a private multi-market trading intelligence and decision-support assistant.
- V1 markets: forex and gold, cryptocurrency, stocks and ETFs.
- Telegram is the only user interface in V1.
- Python is the core engine. Do not make n8n a runtime dependency.
- The user manually places trades. Do not implement broker order execution.
- The user's defined multi-timeframe strategy is the starting strategy. Keep it configurable and deterministic.
- AI may explain structured analysis but must not generate or override strategy decisions.
- If data, instrument specifications, or critical conditions are missing, fail safely and report the limitation.

## Engineering instructions
1. First inspect the existing repository, README, dependencies, and tests. Do not overwrite existing work blindly.
2. Create or update `PRD.md` using the specification above if it is not already present.
3. Produce a short phased plan, then implement Phase 1 only. Do not attempt to build every feature in one unreviewed pass.
4. Use a maintained Telegram bot library compatible with the project's Python version. Pin or constrain dependencies appropriately.
5. Use type hints, small modules, clear domain models, and testable functions.
6. Keep Telegram handlers thin. Put provider calls, strategy logic, risk calculations, persistence and response formatting in separate modules.
7. Define a market-data provider interface and implement one provider adapter only after confirming the provider supports the needed symbols/timeframes. Never fake live data. Use fixtures for tests.
8. Load configuration from environment variables. Create `.env.example` with placeholders only. Never print or commit secrets.
9. Restrict the bot using `TELEGRAM_ALLOWED_USER_IDS`; fail closed outside explicit development mode if the allowlist is not configured.
10. Implement clear logs, bounded timeouts/retries, input validation, and friendly errors without leaking internal details.
11. Add unit tests as you implement each module. Do not wait until the end.
12. Add no live trading execution, no broker order placement, no automatic trade modification, and no claims of guaranteed results.
13. Do not introduce an LLM requirement in the first phase. The app must work with deterministic messages if no AI provider is configured.
14. Avoid unnecessary frameworks, overengineering, and paid services unless they are justified and explicitly configured.
15. Do not claim a command, test, integration, or feature works unless you actually ran and verified it.

## First task
Implement **Phase 1 — Runnable foundation** only:
- project/package structure
- configuration loading and validation
- Telegram bot startup
- `/start` and `/help`
- allowed-user access control
- safe logging
- `.env.example`
- `.gitignore`
- basic tests
- README with setup and run instructions

Before finishing:
- run the tests and report the actual result
- show the files created/modified
- list any setup values the user must supply
- identify the next smallest implementation step
- clearly report anything not completed

Do not ask the user for API keys before the foundation is ready. If the current repository already contains useful code, preserve and adapt it.
