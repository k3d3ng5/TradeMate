"""Small, read-only connection to Binance public spot market data."""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
import threading
from typing import Any

import httpx

from trademate.risk import InstrumentRiskSpecification


class MarketDataError(RuntimeError):
    """A safe, user-facing market data failure."""


@dataclass(frozen=True)
class Candle:
    opened_at: datetime
    closed_at: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal


@dataclass(frozen=True)
class MarketSnapshot:
    symbol: str
    last_price: Decimal
    price_at: datetime
    candles: dict[str, Candle]
    checked_at: datetime
    source: str = "Binance spot"
    price_label: str = "Latest price"
    quote_currency: str = "USDT"
    tick_size: Decimal | None = None
    candle_history: dict[str, tuple[Candle, ...]] = field(default_factory=dict)
    current_candles: dict[str, Candle] = field(default_factory=dict)
    risk_specification: InstrumentRiskSpecification | None = None
    time_note: str | None = None


class BinanceSpotProvider:
    """Fetch public spot trades and candles; no Binance account is needed."""

    BASE_URL = "https://data-api.binance.vision"
    SUPPORTED_SYMBOLS = {"BTCUSDT": "BTC/USDT"}
    TIMEFRAMES = {
        "1m": 60_000,
        "15m": 900_000,
        "1h": 3_600_000,
        "4h": 14_400_000,
    }
    HISTORY_LIMITS = {"1m": 3000, "15m": 300, "1h": 500, "4h": 100}

    def __init__(self, timeout_seconds: float = 6.0) -> None:
        self._client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            timeout=httpx.Timeout(timeout_seconds),
            headers={"User-Agent": "TradeMate-AI/0.1"},
        )

    async def __aenter__(self) -> "BinanceSpotProvider":
        return self

    async def __aexit__(self, *_: object) -> None:
        await self._client.aclose()

    @staticmethod
    def normalize_symbol(symbol: str) -> str:
        return symbol.upper().replace("/", "").replace("-", "").strip()

    async def fetch_snapshot(self, symbol: str) -> MarketSnapshot:
        """Fetch the latest trade and most recent completed candles per timeframe."""
        canonical = self.normalize_symbol(symbol)
        if canonical not in self.SUPPORTED_SYMBOLS:
            raise MarketDataError("For now, TradeMate can show Binance spot data for BTC/USDT only.")

        try:
            async def fetch_candles(timeframe: str) -> tuple[str, list[Candle]]:
                wanted = self.HISTORY_LIMITS[timeframe]
                page_limit = 1000
                interval_ms = self.TIMEFRAMES[timeframe]
                start_ms = int(datetime.now(timezone.utc).timestamp() * 1000) - (wanted - 1) * interval_ms
                rows: list[Any] = []
                while len(rows) < wanted:
                    response = await self._client.get(
                        "/api/v3/klines",
                        params={
                            "symbol": canonical,
                            "interval": timeframe,
                            "startTime": start_ms,
                            "limit": min(page_limit, wanted - len(rows)),
                        },
                    )
                    response.raise_for_status()
                    page = response.json()
                    if not isinstance(page, list) or not page:
                        break
                    rows.extend(page)
                    start_ms = int(page[-1][0]) + interval_ms
                    if len(page) < page_limit:
                        break
                return timeframe, self._validate_candles(rows, timeframe)

            trade_task = self._client.get(
                "/api/v3/aggTrades", params={"symbol": canonical, "limit": 1}
            )
            instrument_task = self._client.get(
                "/api/v3/exchangeInfo", params={"symbol": canonical}
            )
            results = await asyncio.gather(
                trade_task,
                instrument_task,
                *(fetch_candles(timeframe) for timeframe in self.TIMEFRAMES),
            )
            trade_response = results[0]
            trade_response.raise_for_status()
            trade_data = trade_response.json()
            instrument_response = results[1]
            instrument_response.raise_for_status()
            instrument_data = instrument_response.json()

            now = datetime.now(timezone.utc)
            candles_by_timeframe: dict[str, Candle] = {}
            candle_history: dict[str, tuple[Candle, ...]] = {}
            current_candles: dict[str, Candle] = {}
            for timeframe, candles in results[2:]:
                closed = [candle for candle in candles if candle.closed_at <= now]
                if not closed:
                    raise MarketDataError("Completed candle data is not available yet. Try again shortly.")
                candles_by_timeframe[timeframe] = closed[-1]
                candle_history[timeframe] = tuple(closed)
                if candles[-1].closed_at > now:
                    current_candles[timeframe] = candles[-1]

            if not isinstance(trade_data, list) or not trade_data:
                raise MarketDataError("The latest trade is not available right now. Try again shortly.")
            symbols = instrument_data.get("symbols", []) if isinstance(instrument_data, dict) else []
            filters = symbols[0].get("filters", []) if symbols else []
            price_filter = next((item for item in filters if item.get("filterType") == "PRICE_FILTER"), None)
            tick_size = self._decimal(price_filter["tickSize"]) if price_filter else None
            lot_filter = next((item for item in filters if item.get("filterType") == "LOT_SIZE"), None)
            risk_specification = None
            if tick_size and lot_filter and symbols:
                risk_specification = InstrumentRiskSpecification(
                    tick_size=tick_size,
                    # For spot, one unit of base asset loses one price tick
                    # (quoted in the symbol's quote currency) per tick move.
                    tick_value_loss=tick_size,
                    quantity_step=self._decimal(lot_filter["stepSize"]),
                    minimum_quantity=self._decimal(lot_filter["minQty"]),
                    maximum_quantity=self._decimal(lot_filter["maxQty"]),
                    currency=str(symbols[0].get("quoteAsset", "")).upper(),
                    quantity_unit="units",
                )

            latest = trade_data[-1]
            price = self._decimal(latest[1])
            trade_at = datetime.fromtimestamp(int(latest[4]) / 1000, timezone.utc)
            checked_at = datetime.now(timezone.utc)
            return MarketSnapshot(
                symbol=self.SUPPORTED_SYMBOLS[canonical],
                last_price=price,
                price_at=trade_at,
                candles=candles_by_timeframe,
                checked_at=checked_at,
                tick_size=tick_size,
                candle_history=candle_history,
                current_candles=current_candles,
                risk_specification=risk_specification,
            )
        except MarketDataError:
            raise
        except (httpx.HTTPError, ValueError, TypeError, IndexError, KeyError, InvalidOperation) as exc:
            raise MarketDataError(
                "Binance prices could not be reached or checked. Please try again shortly."
            ) from exc

    @classmethod
    def _validate_candles(cls, rows: Any, timeframe: str) -> list[Candle]:
        if not isinstance(rows, list) or not rows:
            raise MarketDataError("Candle data is incomplete. Please try again shortly.")

        candles: list[Candle] = []
        previous_open_ms: int | None = None
        interval_ms = cls.TIMEFRAMES[timeframe]

        try:
            for row in rows:
                if not isinstance(row, list) or len(row) < 7:
                    raise ValueError("Unexpected candle format")
                open_ms = int(row[0])
                close_ms = int(row[6])
                if previous_open_ms is not None and open_ms - previous_open_ms != interval_ms:
                    raise ValueError("Candle times are not continuous")

                candle = Candle(
                    opened_at=datetime.fromtimestamp(open_ms / 1000, timezone.utc),
                    closed_at=datetime.fromtimestamp(close_ms / 1000, timezone.utc),
                    open=cls._decimal(row[1]),
                    high=cls._decimal(row[2]),
                    low=cls._decimal(row[3]),
                    close=cls._decimal(row[4]),
                    volume=cls._decimal(row[5]),
                )
                if (
                    candle.low > min(candle.open, candle.close)
                    or candle.high < max(candle.open, candle.close)
                    or candle.high < candle.low
                    or candle.volume < 0
                ):
                    raise ValueError("Candle values are inconsistent")
                candles.append(candle)
                previous_open_ms = open_ms
        except (ValueError, TypeError, IndexError, InvalidOperation, OverflowError) as exc:
            raise MarketDataError("Binance returned incomplete or inconsistent candle data.") from exc

        return candles

    @staticmethod
    def _decimal(value: Any) -> Decimal:
        number = Decimal(str(value))
        if not number.is_finite():
            raise ValueError("Price value is not finite")
        return number


class MetaTrader5DemoProvider:
    """Read quotes and completed candles from the signed-in MT5 terminal."""

    TIMEFRAMES = {
        # WAT-aligned 4H candles are aggregated from M1 history. Three thousand
        # bars cover only about two trading days, too few to confirm two swings.
        "1m": ("TIMEFRAME_M1", 60, 12000),
        "15m": ("TIMEFRAME_M15", 900, 300),
        # Daily trend checks aggregate WAT calendar days from hourly bars.
        # Five hundred bars cover only a few weeks and may not contain enough
        # confirmed daily turning points, so request several months instead.
        "1h": ("TIMEFRAME_H1", 3600, 2000),
        "4h": ("TIMEFRAME_H4", 14400, 100),
    }
    _connection_lock = threading.Lock()

    async def fetch_snapshot(self, symbol: str) -> MarketSnapshot:
        import asyncio

        return await asyncio.to_thread(self._serialized_fetch, symbol.strip())

    async def list_visible_symbols(self) -> list[str]:
        """Return symbol names currently shown in the signed-in demo terminal's Market Watch."""
        import asyncio

        return await asyncio.to_thread(self._serialized_list_visible_symbols)

    @classmethod
    def _serialized_list_visible_symbols(cls) -> list[str]:
        with cls._connection_lock:
            try:
                import MetaTrader5 as mt5
            except ImportError as exc:
                raise MarketDataError(
                    "MT5 price support is not installed yet. Restart setup after installing the listed packages."
                ) from exc
            initialized = False
            try:
                if not mt5.initialize(timeout=10_000):
                    raise MarketDataError(
                        "I can’t connect to the MT5 terminal. Please open MT5, sign in to your demo account, and try again."
                    )
                initialized = True
                account = mt5.account_info()
                if account is None or account.trade_mode != mt5.ACCOUNT_TRADE_MODE_DEMO:
                    raise MarketDataError(
                        "TradeMate is set up for MT5 demo quotes only. Please sign in to an MT5 demo account and try again."
                    )
                symbols = mt5.symbols_get()
                if symbols is None:
                    raise MarketDataError("MT5 could not list the symbols in Market Watch.")
                return [str(item.name) for item in symbols if getattr(item, "visible", False)]
            finally:
                if initialized:
                    mt5.shutdown()

    @classmethod
    def _serialized_fetch(cls, symbol: str) -> MarketSnapshot:
        with cls._connection_lock:
            return cls._fetch_snapshot(symbol)

    @classmethod
    def _fetch_snapshot(cls, symbol: str) -> MarketSnapshot:
        try:
            import MetaTrader5 as mt5
        except ImportError as exc:
            raise MarketDataError(
                "MT5 price support is not installed yet. Restart setup after installing the listed packages."
            ) from exc

        initialized = False
        try:
            if not mt5.initialize(timeout=10_000):
                raise MarketDataError(
                    "I can’t connect to the MT5 terminal. Please open MT5, sign in to your demo account, and try again."
                )
            initialized = True
            account = mt5.account_info()
            if account is None or account.trade_mode != mt5.ACCOUNT_TRADE_MODE_DEMO:
                raise MarketDataError(
                    "TradeMate is set up for MT5 demo quotes only. Please sign in to an MT5 demo account and try again."
                )
            info = mt5.symbol_info(symbol)
            if info is None or not mt5.symbol_select(symbol, True):
                raise MarketDataError(
                    f"I can’t find {symbol} in this broker’s MT5 symbols. Check its exact name in Market Watch."
                )

            tick = mt5.symbol_info_tick(symbol)
            if tick is None or tick.time <= 0 or tick.bid <= 0 or tick.ask <= 0:
                raise MarketDataError(f"A usable {symbol} quote is not available from MT5 right now.")
            if tick.ask < tick.bid:
                raise MarketDataError(f"The {symbol} quote did not pass a basic price check.")

            timestamp = datetime.fromtimestamp(int(tick.time), timezone.utc)
            now_utc = datetime.now(timezone.utc)
            time_note = None
            if timestamp > now_utc + timedelta(seconds=30):
                ahead_seconds = int((timestamp - now_utc).total_seconds())
                # Some MT5 feeds expose a server-clock timestamp that cannot be
                # compared directly with the computer clock. We have just fetched
                # the terminal's latest quote, so use the retrieval instant for
                # downstream freshness checks and label it honestly in the UI.
                timestamp = now_utc
                time_note = (
                    f"MT5 feed clock is {ahead_seconds}s ahead; time shown is when TradeMate checked the quote."
                )
            bars: dict[str, Candle] = {}
            histories: dict[str, tuple[Candle, ...]] = {}
            current_bars: dict[str, Candle] = {}
            for label, (timeframe_name, seconds, count) in cls.TIMEFRAMES.items():
                timeframe = getattr(mt5, timeframe_name, None)
                rows = mt5.copy_rates_from_pos(symbol, timeframe, 0, count) if timeframe else None
                if rows is None or len(rows) < 3:
                    raise MarketDataError(f"Completed {label} candles are not available for {symbol} yet.")
                chronological: list[Candle] = []
                for row in reversed(rows):
                    opened_at = datetime.fromtimestamp(int(row["time"]), timezone.utc)
                    candle = Candle(
                        opened_at=opened_at,
                        closed_at=datetime.fromtimestamp(int(row["time"]) + seconds, timezone.utc),
                        open=BinanceSpotProvider._decimal(row["open"]),
                        high=BinanceSpotProvider._decimal(row["high"]),
                        low=BinanceSpotProvider._decimal(row["low"]),
                        close=BinanceSpotProvider._decimal(row["close"]),
                        volume=BinanceSpotProvider._decimal(row["tick_volume"]),
                    )
                    if candle.high < max(candle.open, candle.close) or candle.low > min(candle.open, candle.close) or candle.high < candle.low:
                        raise MarketDataError(f"MT5 returned inconsistent {label} candles for {symbol}.")
                    chronological.append(candle)
                now = datetime.now(timezone.utc)
                completed = tuple(candle for candle in chronological if candle.closed_at <= now)
                if len(completed) < 2:
                    raise MarketDataError(f"Completed {label} candle history is not available for {symbol} yet.")
                bars[label] = completed[-1]
                histories[label] = completed
                if chronological[-1].closed_at > now:
                    current_bars[label] = chronological[-1]

            raw_risk_tick_size = BinanceSpotProvider._decimal(getattr(info, "trade_tick_size", 0) or 0)
            price_tick_size = raw_risk_tick_size or BinanceSpotProvider._decimal(getattr(info, "point", 0)) or None
            loss_tick_value = BinanceSpotProvider._decimal(getattr(info, "trade_tick_value_loss", 0) or 0)
            volume_step = BinanceSpotProvider._decimal(getattr(info, "volume_step", 0) or 0)
            volume_min = BinanceSpotProvider._decimal(getattr(info, "volume_min", 0) or 0)
            volume_max = BinanceSpotProvider._decimal(getattr(info, "volume_max", 0) or 0)
            risk_specification = None
            if (
                raw_risk_tick_size > 0
                and loss_tick_value > 0
                and volume_step > 0
                and volume_min > 0
                and volume_max >= volume_min
                and getattr(account, "currency", "")
            ):
                risk_specification = InstrumentRiskSpecification(
                    tick_size=raw_risk_tick_size,
                    tick_value_loss=loss_tick_value,
                    quantity_step=volume_step,
                    minimum_quantity=volume_min,
                    maximum_quantity=volume_max,
                    currency=str(account.currency).upper(),
                    quantity_unit="lots",
                )

            return MarketSnapshot(
                symbol=symbol,
                last_price=(BinanceSpotProvider._decimal(tick.bid) + BinanceSpotProvider._decimal(tick.ask)) / 2,
                price_at=timestamp,
                candles=bars,
                checked_at=datetime.now(timezone.utc),
                source="MT5 demo feed",
                price_label="Bid/ask midpoint",
                quote_currency=getattr(info, "currency_profit", "") or "broker quote currency",
                tick_size=price_tick_size,
                candle_history=histories,
                current_candles=current_bars,
                risk_specification=risk_specification,
                time_note=time_note,
            )
        except MarketDataError:
            raise
        except Exception as exc:
            raise MarketDataError(
                "MT5 data could not be checked. Please make sure the terminal is open and connected, then try again."
            ) from exc
        finally:
            if initialized:
                mt5.shutdown()

