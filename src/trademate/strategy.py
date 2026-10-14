"""Deterministic rules and evidence models for the TSQ Phase 3 strategy."""

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from enum import Enum
from typing import Iterable

from trademate.market_data import Candle


class Direction(str, Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


class DecisionStatus(str, Enum):
    TRADE_SETUP = "TRADE SETUP"
    WAIT = "WAIT"
    AVOID = "AVOID"
    INSUFFICIENT_DATA = "INSUFFICIENT DATA"


class CheckState(str, Enum):
    PASS = "pass"
    PENDING = "pending"
    FAIL = "fail"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True)
class RuleCheck:
    """One auditable condition from a strategy evaluation."""

    name: str
    state: CheckState
    evidence: str
    blocks_setup: bool = True


@dataclass(frozen=True)
class StrategyEvaluation:
    status: DecisionStatus
    direction: Direction
    checks: tuple[RuleCheck, ...]
    entry: Decimal | None = None
    stop: Decimal | None = None
    tp1: Decimal | None = None
    tp2: Decimal | None = None
    invalidation: Decimal | None = None


@dataclass(frozen=True)
class TSQMarketData:
    symbol: str
    asset_class: str
    last_price: Decimal
    price_at: datetime
    analyzed_at: datetime
    candle_history: dict[str, tuple[Candle, ...]]
    current_candles: dict[str, Candle]
    tick_size: Decimal | None


@dataclass(frozen=True)
class SwingPoint:
    index: int
    price: Decimal


@dataclass(frozen=True)
class LiquidityLevel:
    name: str
    price: Decimal
    source: str
    side: str


@dataclass(frozen=True)
class PriceZone:
    lower: Decimal
    upper: Decimal

    def contains(self, price: Decimal) -> bool:
        return self.lower <= price <= self.upper

    def overlaps(self, other: "PriceZone") -> bool:
        return max(self.lower, other.lower) <= min(self.upper, other.upper)


@dataclass(frozen=True)
class SweepEvent:
    level: LiquidityLevel
    purge_index: int
    confirmation_index: int


@dataclass(frozen=True)
class ReferenceLevels:
    levels: tuple[LiquidityLevel, ...]
    unavailable: tuple[str, ...]


WAT = timezone(timedelta(hours=1), name="WAT")
KILL_ZONES = ((time(7), time(11)), (time(13), time(17)))


def evaluate_checks(direction: Direction, checks: Iterable[RuleCheck]) -> StrategyEvaluation:
    """Return a fail-closed status from the condition evidence available."""
    recorded = tuple(checks)
    if any(check.state is CheckState.UNAVAILABLE and check.blocks_setup for check in recorded):
        status = DecisionStatus.INSUFFICIENT_DATA
    elif any(check.state is CheckState.FAIL and check.blocks_setup for check in recorded):
        status = DecisionStatus.AVOID
    elif direction is Direction.NEUTRAL or any(
        check.state is CheckState.PENDING and check.blocks_setup for check in recorded
    ):
        status = DecisionStatus.WAIT
    elif not recorded or any(
        check.state is not CheckState.PASS and check.blocks_setup for check in recorded
    ):
        status = DecisionStatus.INSUFFICIENT_DATA
    else:
        status = DecisionStatus.TRADE_SETUP
    return StrategyEvaluation(status=status, direction=direction, checks=recorded)


def four_hour_bias(current: Candle, previous: Candle) -> Direction:
    """Apply the configured close beyond the prior 4H range rule."""
    if current.close > previous.high:
        return Direction.BULLISH
    if current.close < previous.low:
        return Direction.BEARISH
    return Direction.NEUTRAL


def price_is_on_entry_side_of_open(
    price: Decimal,
    current_four_hour_open: Decimal,
    direction: Direction,
) -> bool:
    """For longs require price below the 4H open; for shorts, above it."""
    if direction is Direction.BULLISH:
        return price < current_four_hour_open
    if direction is Direction.BEARISH:
        return price > current_four_hour_open
    return False


def is_in_kill_zone(value: datetime) -> bool:
    """Use the user-specified fixed WAT London and New York windows."""
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("Strategy timestamps must include a timezone.")
    local_time = value.astimezone(WAT).time().replace(tzinfo=None)
    return any(start <= local_time < end for start, end in KILL_ZONES)


def build_wat_four_hour_candles(
    minute_candles: tuple[Candle, ...] | list[Candle],
    *,
    as_of: datetime,
    provider_four_hour: tuple[Candle, ...] | list[Candle] = (),
) -> tuple[Candle, ...]:
    """Aggregate complete M1 bars into 4H candles aligned to WAT 03/07/11/15.

    A bucket is returned only when all 240 minute bars are present. This avoids
    treating an incomplete history slice as a valid 4H structure candle.
    """
    if as_of.tzinfo is None or as_of.utcoffset() is None:
        raise ValueError("The analysis timestamp must include a timezone.")
    buckets: dict[datetime, list[Candle]] = {}
    for candle in minute_candles:
        local_open = candle.opened_at.astimezone(WAT)
        hour_offset = (local_open.hour - 3) % 24
        bucket_hour = (3 + (hour_offset // 4) * 4) % 24
        bucket_date = local_open.date()
        if bucket_hour > local_open.hour:
            bucket_date -= timedelta(days=1)
        start = datetime.combine(bucket_date, time(bucket_hour), WAT)
        if start + timedelta(hours=4) <= as_of.astimezone(WAT):
            buckets.setdefault(start, []).append(candle)

    completed: list[Candle] = []
    for start, members in sorted(buckets.items()):
        members.sort(key=lambda item: item.opened_at)
        if len(members) != 240:
            continue
        if any(
            right.opened_at - left.opened_at != timedelta(minutes=1)
            for left, right in zip(members, members[1:])
        ):
            continue
        completed.append(Candle(
            opened_at=start.astimezone(timezone.utc),
            closed_at=(start + timedelta(hours=4)).astimezone(timezone.utc),
            open=members[0].open,
            high=max(item.high for item in members),
            low=min(item.low for item in members),
            close=members[-1].close,
            volume=sum((item.volume for item in members), Decimal(0)),
        ))
    aligned_provider_bars = tuple(
        candle for candle in provider_four_hour
        if candle.opened_at.astimezone(WAT).minute == 0
        and candle.opened_at.astimezone(WAT).hour in {3, 7, 11, 15, 19, 23}
        and candle.closed_at <= as_of.astimezone(timezone.utc)
    )
    if len(aligned_provider_bars) >= 10:
        return aligned_provider_bars
    return tuple(completed)


def current_wat_four_hour_open(
    minute_candles: tuple[Candle, ...] | list[Candle],
    current_minute: Candle | None,
    *,
    as_of: datetime,
    provider_current_four_hour: Candle | None = None,
) -> Decimal | None:
    """Find the open of the active WAT-aligned 4H candle."""
    if as_of.tzinfo is None or as_of.utcoffset() is None:
        raise ValueError("The analysis timestamp must include a timezone.")
    local = as_of.astimezone(WAT)
    hour_offset = (local.hour - 3) % 24
    bucket_hour = (3 + (hour_offset // 4) * 4) % 24
    bucket_date = local.date()
    if bucket_hour > local.hour:
        bucket_date -= timedelta(days=1)
    bucket_start = datetime.combine(bucket_date, time(bucket_hour), WAT)
    if (
        provider_current_four_hour is not None
        and provider_current_four_hour.opened_at.astimezone(WAT) == bucket_start
    ):
        return provider_current_four_hour.open
    members = [candle for candle in minute_candles if (
        candle.opened_at.astimezone(WAT) >= bucket_start
        and candle.opened_at.astimezone(WAT) < local
    )]
    if current_minute is not None and current_minute.opened_at.astimezone(WAT) >= bucket_start:
        members.append(current_minute)
    if not members:
        return None
    return min(members, key=lambda candle: candle.opened_at).open


def four_hour_order_flow(candles: tuple[Candle, ...] | list[Candle]) -> Direction:
    """Use the latest pair of confirmed swing highs/lows to establish order flow."""
    highs, lows = find_internal_swings(candles)
    if len(highs) < 2 or len(lows) < 2:
        return Direction.NEUTRAL
    previous_high, latest_high = highs[-2:]
    previous_low, latest_low = lows[-2:]
    if latest_high.price > previous_high.price and latest_low.price > previous_low.price:
        return Direction.BULLISH
    if latest_high.price < previous_high.price and latest_low.price < previous_low.price:
        return Direction.BEARISH
    return Direction.NEUTRAL


def build_wat_daily_candles(
    hourly_candles: tuple[Candle, ...] | list[Candle],
) -> tuple[Candle, ...]:
    """Aggregate complete 00:00–00:00 WAT daily candles from H1 history."""
    buckets: dict[date, list[Candle]] = {}
    for candle in hourly_candles:
        local_open = candle.opened_at.astimezone(WAT)
        buckets.setdefault(local_open.date(), []).append(candle)
    result: list[Candle] = []
    for day, members in sorted(buckets.items()):
        members.sort(key=lambda item: item.opened_at)
        if len(members) != 24:
            continue
        starts = [item.opened_at.astimezone(WAT) for item in members]
        if starts[0].time().replace(tzinfo=None) != time(0):
            continue
        if any(right - left != timedelta(hours=1) for left, right in zip(starts, starts[1:])):
            continue
        result.append(Candle(
            opened_at=datetime.combine(day, time(0), WAT).astimezone(timezone.utc),
            closed_at=datetime.combine(day + timedelta(days=1), time(0), WAT).astimezone(timezone.utc),
            open=members[0].open,
            high=max(item.high for item in members),
            low=min(item.low for item in members),
            close=members[-1].close,
            volume=sum((item.volume for item in members), Decimal(0)),
        ))
    return tuple(result)


def aligned_four_hour_bias(
    current: Candle,
    previous: Candle,
    order_flow_candles: tuple[Candle, ...] | list[Candle],
) -> Direction:
    """Require close-based bias and structural order flow to agree."""
    close_bias = four_hour_bias(current, previous)
    flow_bias = four_hour_order_flow(order_flow_candles)
    if close_bias is flow_bias:
        return close_bias
    return Direction.NEUTRAL


def previous_trading_day_levels(
    hourly_candles: tuple[Candle, ...] | list[Candle],
    *,
    as_of: datetime,
) -> tuple[LiquidityLevel, LiquidityLevel] | None:
    """Return PDH/PDL only when a complete prior WAT calendar day is present."""
    if as_of.tzinfo is None or as_of.utcoffset() is None:
        raise ValueError("The analysis timestamp must include a timezone.")
    today = as_of.astimezone(WAT).date()
    by_day: dict[date, list[Candle]] = {}
    for candle in hourly_candles:
        local_open = candle.opened_at.astimezone(WAT)
        if local_open.date() < today:
            by_day.setdefault(local_open.date(), []).append(candle)
    for day in sorted(by_day, reverse=True):
        bars = by_day[day]
        if len(bars) != 24 or len({bar.opened_at for bar in bars}) != 24:
            continue
        high = max(bar.high for bar in bars)
        low = min(bar.low for bar in bars)
        return (
            LiquidityLevel("PDH", high, "previous WAT trading day", "high"),
            LiquidityLevel("PDL", low, "previous WAT trading day", "low"),
        )
    return None


def build_reference_levels(
    hourly_candles: tuple[Candle, ...] | list[Candle],
    minute_candles: tuple[Candle, ...] | list[Candle],
    wat_four_hour_candles: tuple[Candle, ...] | list[Candle],
    *,
    as_of: datetime,
) -> ReferenceLevels:
    """Collect PDH/PDL, Asian, and active time-based CRT levels fail-closed."""
    levels: list[LiquidityLevel] = []
    unavailable: list[str] = []
    prior_day = previous_trading_day_levels(hourly_candles, as_of=as_of)
    if prior_day is None:
        unavailable.append("Complete prior WAT trading-day candles are unavailable for PDH/PDL.")
    else:
        levels.extend(prior_day)

    asia = asian_range_levels(minute_candles, as_of=as_of)
    if asia is None:
        unavailable.append("A complete 02:00–06:00 WAT minute history is unavailable for Asian High/Low.")
    else:
        levels.extend(asia)

    crt = time_based_crt_levels(wat_four_hour_candles, as_of=as_of)
    if crt is None:
        unavailable.append("The active WAT CRT feeder range is unavailable or outside a kill zone.")
    else:
        levels.extend(crt)
    return ReferenceLevels(tuple(levels), tuple(unavailable))


def asian_range_levels(
    minute_candles: tuple[Candle, ...] | list[Candle],
    *,
    as_of: datetime,
) -> tuple[LiquidityLevel, LiquidityLevel] | None:
    """Return the 02:00–06:00 WAT Asian high/low from 240 complete M1 bars."""
    if as_of.tzinfo is None or as_of.utcoffset() is None:
        raise ValueError("The analysis timestamp must include a timezone.")
    local_as_of = as_of.astimezone(WAT)
    start = datetime.combine(local_as_of.date(), time(2), WAT)
    end = datetime.combine(local_as_of.date(), time(6), WAT)
    bars = [
        candle for candle in minute_candles
        if start <= candle.opened_at.astimezone(WAT) < end
        and candle.closed_at <= as_of.astimezone(timezone.utc)
    ]
    bars.sort(key=lambda item: item.opened_at)
    if len(bars) != 240 or any(
        right.opened_at - left.opened_at != timedelta(minutes=1)
        for left, right in zip(bars, bars[1:])
    ):
        return None
    return (
        LiquidityLevel("Asian High", max(candle.high for candle in bars), "02:00–06:00 WAT", "high"),
        LiquidityLevel("Asian Low", min(candle.low for candle in bars), "02:00–06:00 WAT", "low"),
    )


def time_based_crt_levels(
    wat_four_hour_candles: tuple[Candle, ...] | list[Candle],
    *,
    as_of: datetime,
) -> tuple[LiquidityLevel, LiquidityLevel] | None:
    """Build the active feeder CRT range for the configured WAT kill zone."""
    if as_of.tzinfo is None or as_of.utcoffset() is None:
        raise ValueError("The analysis timestamp must include a timezone.")
    local = as_of.astimezone(WAT)
    hour = local.hour
    if 7 <= hour < 11:
        starts = (time(3),)
        label = "03:00 WAT CRT feeder"
    elif 13 <= hour < 15:
        starts = (time(3), time(7))
        label = "03:00 + 07:00 WAT CRT feeders"
    elif 15 <= hour < 17:
        starts = (time(7), time(11))
        label = "07:00 + 11:00 WAT CRT feeders"
    else:
        return None

    selected = []
    for candle_time in starts:
        candidate = next((
            candle for candle in wat_four_hour_candles
            if candle.opened_at.astimezone(WAT).date() == local.date()
            and candle.opened_at.astimezone(WAT).time().replace(tzinfo=None) == candle_time
            and candle.closed_at <= as_of.astimezone(timezone.utc)
        ), None)
        if candidate is None:
            return None
        selected.append(candidate)
    return (
        LiquidityLevel("CRT High", max(candle.high for candle in selected), label, "high"),
        LiquidityLevel("CRT Low", min(candle.low for candle in selected), label, "low"),
    )


def find_internal_swings(candles: tuple[Candle, ...] | list[Candle]) -> tuple[list[SwingPoint], list[SwingPoint]]:
    """Find strict two-bars-each-side internal swing highs and lows."""
    highs: list[SwingPoint] = []
    lows: list[SwingPoint] = []
    for index in range(2, len(candles) - 2):
        candle = candles[index]
        neighbours = candles[index - 2:index] + candles[index + 1:index + 3]
        if all(candle.high > other.high for other in neighbours):
            highs.append(SwingPoint(index=index, price=candle.high))
        if all(candle.low < other.low for other in neighbours):
            lows.append(SwingPoint(index=index, price=candle.low))
    return highs, lows


def find_mss_index(
    candles: tuple[Candle, ...] | list[Candle],
    *,
    purge_index: int,
    swing_level: Decimal,
    direction: Direction,
) -> int | None:
    """Find the first post-purge candle body close through internal structure."""
    for index in range(purge_index + 1, len(candles)):
        candle = candles[index]
        if direction is Direction.BULLISH and candle.close > swing_level:
            return index
        if direction is Direction.BEARISH and candle.close < swing_level:
            return index
    return None


def find_breaker_index(
    candles: tuple[Candle, ...] | list[Candle],
    *,
    purge_index: int,
    expansion_index: int,
    direction: Direction,
) -> int | None:
    """Return the last counter-direction candle from purge through expansion."""
    if expansion_index <= purge_index or expansion_index >= len(candles):
        return None
    for index in range(expansion_index - 1, purge_index - 1, -1):
        candle = candles[index]
        if direction is Direction.BULLISH and candle.close < candle.open:
            return index
        if direction is Direction.BEARISH and candle.close > candle.open:
            return index
    return None


def breaker_ote_confluence(
    breaker_candle: Candle,
    retracement_zone: PriceZone,
) -> PriceZone | None:
    """Return the shared price interval between the breaker and OTE zone."""
    lower = max(breaker_candle.low, retracement_zone.lower)
    upper = min(breaker_candle.high, retracement_zone.upper)
    if lower > upper:
        return None
    return PriceZone(lower, upper)


def sweep_candle_entry(
    purge_candle: Candle,
    direction: Direction,
    *,
    long_tail_multiple: Decimal = Decimal("2"),
) -> Decimal:
    """Use the purge-body open, or the midpoint of a qualifying rejection wick."""
    body = abs(purge_candle.close - purge_candle.open)
    if body == 0 or direction is Direction.NEUTRAL:
        raise ValueError("A directional, non-doji purge candle is required.")
    if direction is Direction.BULLISH:
        wick = min(purge_candle.open, purge_candle.close) - purge_candle.low
        if wick >= body * long_tail_multiple:
            return (purge_candle.low + min(purge_candle.open, purge_candle.close)) / 2
    else:
        wick = purge_candle.high - max(purge_candle.open, purge_candle.close)
        if wick >= body * long_tail_multiple:
            return (max(purge_candle.open, purge_candle.close) + purge_candle.high) / 2
    return purge_candle.open


def ote_zone(
    protected_extreme_price: Decimal,
    expansion_extreme_price: Decimal,
    direction: Direction,
    *,
    retracement_min: Decimal = Decimal("0.60"),
    retracement_max: Decimal = Decimal("0.75"),
) -> PriceZone:
    """Build the user's 60–75% retracement zone across the displacement leg."""
    if not Decimal(0) < retracement_min < retracement_max < Decimal(1):
        raise ValueError("OTE retracement bounds must be ordered between zero and one.")
    span = abs(expansion_extreme_price - protected_extreme_price)
    if span == 0:
        raise ValueError("OTE anchors must be different prices.")
    if direction is Direction.BULLISH:
        if expansion_extreme_price <= protected_extreme_price:
            raise ValueError("A bullish expansion extreme must be above its protected low.")
        return PriceZone(
            lower=expansion_extreme_price - span * retracement_max,
            upper=expansion_extreme_price - span * retracement_min,
        )
    if direction is Direction.BEARISH:
        if expansion_extreme_price >= protected_extreme_price:
            raise ValueError("A bearish expansion extreme must be below its protected high.")
        return PriceZone(
            lower=expansion_extreme_price + span * retracement_min,
            upper=expansion_extreme_price + span * retracement_max,
        )
    raise ValueError("OTE requires a bullish or bearish direction.")


def unfilled_four_hour_fvgs(
    candles: tuple[Candle, ...] | list[Candle],
    direction: Direction,
    *,
    as_of: datetime,
) -> tuple[PriceZone, ...]:
    """Find directional 3-candle 4H gaps that have not been fully filled."""
    if direction is Direction.NEUTRAL or as_of.tzinfo is None or as_of.utcoffset() is None:
        return ()
    complete = [candle for candle in candles if candle.closed_at <= as_of.astimezone(timezone.utc)]
    zones: list[PriceZone] = []
    for index in range(len(complete) - 3, -1, -1):
        first, third = complete[index], complete[index + 2]
        if direction is Direction.BULLISH and first.high < third.low:
            zone = PriceZone(first.high, third.low)
            fully_filled = any(candle.low <= zone.lower for candle in complete[index + 3:])
        elif direction is Direction.BEARISH and first.low > third.high:
            zone = PriceZone(third.high, first.low)
            fully_filled = any(candle.high >= zone.upper for candle in complete[index + 3:])
        else:
            continue
        if not fully_filled:
            zones.append(zone)
    return tuple(zones)


def rejection_sweep(
    candle: Candle,
    level: Decimal,
    direction: Direction,
    *,
    wick_body_multiple: Decimal = Decimal("2"),
) -> bool:
    """Check a level sweep, close back inside, and the specified wick/body ratio."""
    if direction is Direction.NEUTRAL or wick_body_multiple <= 0:
        return False
    body = abs(candle.close - candle.open)
    if body == 0:
        return False
    if direction is Direction.BULLISH:
        wick = min(candle.open, candle.close) - candle.low
        return candle.low < level and candle.close > level and wick >= body * wick_body_multiple
    wick = candle.high - max(candle.open, candle.close)
    return candle.high > level and candle.close < level and wick >= body * wick_body_multiple


def model_one_confirmed(
    purge_candle: Candle,
    following_candle: Candle,
    direction: Direction,
) -> bool:
    """Require the following M15 close to clear the purge candle's full range."""
    if direction is Direction.BULLISH:
        return following_candle.close > purge_candle.high
    if direction is Direction.BEARISH:
        return following_candle.close < purge_candle.low
    return False


def find_confirmed_sweep(
    candles: tuple[Candle, ...] | list[Candle],
    levels: tuple[LiquidityLevel, ...] | list[LiquidityLevel],
    direction: Direction,
    *,
    as_of: datetime,
) -> SweepEvent | None:
    """Find the latest unpurged M15 level sweep with a kill-zone Model 1 close."""
    if direction is Direction.NEUTRAL:
        return None
    if as_of.tzinfo is None or as_of.utcoffset() is None:
        raise ValueError("The analysis timestamp must include a timezone.")
    local_day = as_of.astimezone(WAT).date()
    expected_side = "low" if direction is Direction.BULLISH else "high"
    for purge_index in range(len(candles) - 2, -1, -1):
        purge = candles[purge_index]
        if purge.closed_at > as_of.astimezone(timezone.utc):
            continue
        if purge.opened_at.astimezone(WAT).date() != local_day or not is_in_kill_zone(purge.opened_at):
            continue
        confirmation_index = purge_index + 1
        confirmation = candles[confirmation_index]
        if confirmation.closed_at > as_of.astimezone(timezone.utc):
            continue
        if not is_in_kill_zone(confirmation.opened_at):
            continue
        valid_levels = []
        for level in levels:
            if level.side != expected_side or not rejection_sweep(purge, level.price, direction):
                continue
            already_purged = any(
                (prior.high > level.price if level.side == "high" else prior.low < level.price)
                for prior in candles[:purge_index]
                if prior.opened_at.astimezone(WAT).date() == local_day
            )
            if already_purged:
                continue
            valid_levels.append(level)
        if valid_levels and model_one_confirmed(purge, confirmation, direction):
            level = (
                max(valid_levels, key=lambda candidate: candidate.price)
                if direction is Direction.BULLISH
                else min(valid_levels, key=lambda candidate: candidate.price)
            )
            return SweepEvent(level, purge_index, confirmation_index)
    return None


def protected_extreme(purge_candle: Candle, direction: Direction) -> Decimal | None:
    """Return the purge wick that anchors structural invalidation."""
    if direction is Direction.BULLISH:
        return purge_candle.low
    if direction is Direction.BEARISH:
        return purge_candle.high
    return None


def structural_stop_price(
    protected_level: Decimal,
    tick_size: Decimal,
    direction: Direction,
) -> Decimal:
    """Place the stop one verified tick beyond the protected purge extreme."""
    if tick_size <= 0:
        raise ValueError("A positive verified instrument tick size is required.")
    if direction is Direction.BULLISH:
        return protected_level - tick_size
    if direction is Direction.BEARISH:
        return protected_level + tick_size
    raise ValueError("A structural stop requires a bullish or bearish direction.")


def is_invalidated(price: Decimal, protected_level: Decimal, direction: Direction) -> bool:
    """A move beyond the protected sweep extreme invalidates the setup."""
    if direction is Direction.BULLISH:
        return price < protected_level
    if direction is Direction.BEARISH:
        return price > protected_level
    return False


def risk_reward_ratio(
    entry: Decimal,
    stop: Decimal,
    target: Decimal,
    direction: Direction,
) -> Decimal:
    """Calculate price-distance R:R after validating its direction."""
    if direction is Direction.BULLISH:
        if not stop < entry < target:
            raise ValueError("Bullish prices must satisfy stop < entry < target.")
        risk, reward = entry - stop, target - entry
    elif direction is Direction.BEARISH:
        if not target < entry < stop:
            raise ValueError("Bearish prices must satisfy target < entry < stop.")
        risk, reward = stop - entry, entry - target
    else:
        raise ValueError("A risk/reward ratio requires a bullish or bearish direction.")
    return reward / risk


def meets_minimum_risk_reward(
    entry: Decimal,
    stop: Decimal,
    target: Decimal,
    direction: Direction,
    *,
    minimum: Decimal = Decimal("2.5"),
) -> bool:
    """Apply the user's minimum 1:2.5 price-distance requirement."""
    if minimum <= 0:
        raise ValueError("Minimum risk/reward must be greater than zero.")
    return risk_reward_ratio(entry, stop, target, direction) >= minimum


def _candle_touches_zone(candle: Candle, zone: PriceZone) -> bool:
    return candle.low <= zone.upper and candle.high >= zone.lower


def _one_minute_refinement(
    candles: tuple[Candle, ...] | list[Candle],
    *,
    after: datetime,
    zone: PriceZone,
    direction: Direction,
    as_of: datetime,
    current_price: Decimal,
) -> bool:
    """Require an M1 structure break, counter-candle block, then zone retest."""
    recent = [
        candle for candle in candles
        if candle.opened_at >= after and candle.closed_at <= as_of
    ]
    if len(recent) < 7:
        return False
    highs, lows = find_internal_swings(recent)
    points = highs if direction is Direction.BULLISH else lows
    for point in reversed(points):
        expansion_index = next((
            index for index in range(point.index + 3, len(recent))
            if (recent[index].close > point.price if direction is Direction.BULLISH
                else recent[index].close < point.price)
        ), None)
        if expansion_index is None:
            continue
        breaker_index = find_breaker_index(
            recent,
            purge_index=point.index + 1,
            expansion_index=expansion_index,
            direction=direction,
        )
        if breaker_index is None:
            continue
        micro_confluence = breaker_ote_confluence(recent[breaker_index], zone)
        if micro_confluence is None:
            continue
        if micro_confluence.contains(current_price) and any(
            _candle_touches_zone(candle, micro_confluence)
            for candle in recent[expansion_index + 1:]
        ):
            return True
    return False


def analyze_tsq(data: TSQMarketData) -> StrategyEvaluation:
    """Evaluate the configured TSQ Phase 3 conditions without placing orders."""
    unavailable = lambda name, evidence: RuleCheck(name, CheckState.UNAVAILABLE, evidence)
    pending = lambda name, evidence: RuleCheck(name, CheckState.PENDING, evidence)
    passed = lambda name, evidence: RuleCheck(name, CheckState.PASS, evidence)
    if (
        data.analyzed_at.tzinfo is None
        or data.analyzed_at.utcoffset() is None
        or data.price_at.tzinfo is None
        or data.price_at.utcoffset() is None
    ):
        return evaluate_checks(Direction.NEUTRAL, [unavailable(
            "Timestamp quality", "The quote and analysis timestamps must include time zones."
        )])
    age_seconds = (data.analyzed_at - data.price_at).total_seconds()
    if age_seconds < -30 or age_seconds > 120:
        return evaluate_checks(Direction.NEUTRAL, [unavailable(
            "Quote freshness", "The market quote is future-dated or more than 2 minutes old."
        )])

    minute_history = data.candle_history.get("1m", ())
    m15_history = data.candle_history.get("15m", ())
    hourly_history = data.candle_history.get("1h", ())
    if data.asset_class.strip().lower() not in {"forex", "gold", "crypto"}:
        return evaluate_checks(Direction.NEUTRAL, [unavailable(
            "Strategy applicability", "These rules are configured for currency pairs, gold, and BTC/USD." 
        )])
    if len(minute_history) < 300 or len(m15_history) < 7 or len(hourly_history) < 240:
        return evaluate_checks(Direction.NEUTRAL, [unavailable(
            "Candle history", "More 1M, 15M, and 1H history is needed for the strategy levels and daily order flow."
        )])

    wat_four_hour = build_wat_four_hour_candles(
        minute_history,
        as_of=data.analyzed_at,
        provider_four_hour=data.candle_history.get("4h", ()),
    )
    if len(wat_four_hour) < 10:
        return evaluate_checks(Direction.NEUTRAL, [unavailable(
            "WAT 4H history", "At least 10 complete WAT-aligned 4H candles are needed for swing order flow."
        )])
    wat_daily = build_wat_daily_candles(hourly_history)
    if len(wat_daily) < 10:
        return evaluate_checks(Direction.NEUTRAL, [unavailable(
            "WAT daily history", "At least 10 complete WAT-aligned daily candles are needed for daily swing order flow."
        )])
    close_bias = four_hour_bias(wat_four_hour[-1], wat_four_hour[-2])
    highs, lows = find_internal_swings(wat_four_hour)
    if len(highs) < 2 or len(lows) < 2:
        return evaluate_checks(Direction.NEUTRAL, [unavailable(
            "4H order flow", "The available history does not contain two confirmed swing highs and lows."
        )])
    flow_bias = four_hour_order_flow(wat_four_hour)
    daily_flow_bias = four_hour_order_flow(wat_daily)
    daily_highs, daily_lows = find_internal_swings(wat_daily)
    if len(daily_highs) < 2 or len(daily_lows) < 2:
        return evaluate_checks(Direction.NEUTRAL, [unavailable(
            "Daily order flow", "The available daily history does not contain two confirmed swing highs and lows."
        )])
    checks: list[RuleCheck] = [
        (passed if close_bias is not Direction.NEUTRAL else pending)(
            "4H close bias", f"Latest completed WAT 4H close: {close_bias.value}."
        ),
        (passed if flow_bias is not Direction.NEUTRAL else pending)(
            "4H structural order flow", f"Last two confirmed swing pairs: {flow_bias.value}."
        ),
        (passed if daily_flow_bias is not Direction.NEUTRAL else pending)(
            "Daily structural order flow", f"Last two confirmed daily swing pairs: {daily_flow_bias.value}."
        ),
    ]
    if (
        close_bias is Direction.NEUTRAL
        or flow_bias is Direction.NEUTRAL
        or daily_flow_bias is Direction.NEUTRAL
        or close_bias is not flow_bias
        or close_bias is not daily_flow_bias
    ):
        checks.append(pending(
            "4H alignment", "The close-based bias and structural order flow do not agree yet."
        ))
        return evaluate_checks(Direction.NEUTRAL, checks)
    direction = close_bias
    checks.append(passed("4H alignment", f"Bias and order flow both point {direction.value}."))

    if not is_in_kill_zone(data.analyzed_at):
        checks.append(pending("Kill zone", "Wait for the London (07:00–11:00) or New York (13:00–17:00) WAT window."))
        return evaluate_checks(direction, checks)

    current_open = current_wat_four_hour_open(
        minute_history,
        data.current_candles.get("1m"),
        as_of=data.analyzed_at,
        provider_current_four_hour=data.current_candles.get("4h"),
    )
    if current_open is None:
        checks.append(unavailable("Current 4H open", "The WAT-aligned active 4H open is missing."))
        return evaluate_checks(direction, checks)
    if not price_is_on_entry_side_of_open(data.last_price, current_open, direction):
        checks.append(pending("4H open location", "Price has not moved to the required side of the active 4H open."))
        return evaluate_checks(direction, checks)
    checks.append(passed("4H open location", "Price is on the configured entry side of the active 4H open."))

    references = build_reference_levels(
        hourly_history,
        minute_history,
        wat_four_hour,
        as_of=data.analyzed_at,
    )
    if references.unavailable:
        checks.extend(unavailable("Reference levels", reason) for reason in references.unavailable)
        return evaluate_checks(direction, checks)
    checks.append(passed("Liquidity references", "PDH/PDL, Asian range, and active CRT feeder levels are available."))

    sweep = find_confirmed_sweep(m15_history, references.levels, direction, as_of=data.analyzed_at)
    if sweep is None:
        checks.append(pending("Turtle Soup + Model 1", "No unpurged level sweep with the required M15 rejection and confirmation is complete."))
        return evaluate_checks(direction, checks)
    purge = m15_history[sweep.purge_index]
    checks.append(passed(
        "Turtle Soup + Model 1",
        f"{sweep.level.name} swept and rejected; the next M15 candle closed beyond the purge range.",
    ))

    history_before_purge = m15_history[:sweep.purge_index]
    m15_highs, m15_lows = find_internal_swings(history_before_purge)
    relevant_swings = m15_highs if direction is Direction.BULLISH else m15_lows
    if not relevant_swings:
        checks.append(unavailable("M15 internal structure", "No confirmed two-bars-each-side swing exists before the purge."))
        return evaluate_checks(direction, checks)
    swing = relevant_swings[-1]
    expansion_index = next((
        index for index in range(sweep.confirmation_index, len(m15_history))
        if (m15_history[index].close > swing.price if direction is Direction.BULLISH
            else m15_history[index].close < swing.price)
        and m15_history[index].closed_at <= data.analyzed_at
        and is_in_kill_zone(m15_history[index].opened_at)
    ), None)
    if expansion_index is None:
        checks.append(pending("M15 MSS", "The M15 body has not closed through the latest internal swing during the kill zone."))
        return evaluate_checks(direction, checks)
    checks.append(passed("M15 MSS", f"M15 body closed through internal swing at {swing.price}."))

    breaker_index = find_breaker_index(
        m15_history,
        purge_index=sweep.purge_index,
        expansion_index=expansion_index,
        direction=direction,
    )
    if breaker_index is None:
        checks.append(unavailable("Breaker block", "No opposing candle was found between the purge and MSS expansion."))
        return evaluate_checks(direction, checks)
    protected = protected_extreme(purge, direction)
    if protected is None:
        checks.append(unavailable("Protected extreme", "The purge direction is not valid."))
        return evaluate_checks(direction, checks)
    expansion_slice = m15_history[sweep.purge_index:expansion_index + 1]
    expansion_extreme = (
        max(candle.high for candle in expansion_slice)
        if direction is Direction.BULLISH
        else min(candle.low for candle in expansion_slice)
    )
    try:
        retracement = ote_zone(protected, expansion_extreme, direction)
    except ValueError:
        checks.append(unavailable("OTE anchors", "The purge and expansion did not produce valid Fibonacci anchors."))
        return evaluate_checks(direction, checks)
    confluence = breaker_ote_confluence(m15_history[breaker_index], retracement)
    if confluence is None:
        checks.append(pending("Breaker + OTE", "The breaker block does not overlap the 60–75% retracement zone yet."))
        return evaluate_checks(direction, checks)
    entry = sweep_candle_entry(purge, direction)
    aligned_fvg = any(
        zone.contains(entry)
        and zone.contains(data.last_price)
        and max(zone.lower, confluence.lower) <= min(zone.upper, confluence.upper)
        for zone in unfilled_four_hour_fvgs(wat_four_hour, direction, as_of=data.analyzed_at)
    )
    if not aligned_fvg:
        checks.append(pending(
            "4H FVG alignment", "Price and the planned entry must overlap an unfilled, direction-aligned 4H gap during the kill zone."
        ))
        return evaluate_checks(direction, checks)
    checks.append(passed("4H FVG alignment", "The entry area and current price overlap an unfilled 4H gap aligned with the higher-timeframe direction."))
    if not confluence.contains(entry):
        checks.append(pending("Entry level", "The purge-candle entry is outside the breaker/OTE confluence."))
        return evaluate_checks(direction, checks)
    checks.append(passed("Breaker + OTE", "The breaker block overlaps the 60–75% retracement zone at the purge-candle entry."))

    m15_retested = any(
        candle.opened_at >= m15_history[expansion_index].closed_at
        and candle.closed_at <= data.analyzed_at
        and _candle_touches_zone(candle, confluence)
        for candle in m15_history[expansion_index + 1:]
    )
    if not m15_retested and not _one_minute_refinement(
        data.candle_history.get("1m", ()),
        after=m15_history[expansion_index].closed_at,
        zone=confluence,
        direction=direction,
        as_of=data.analyzed_at,
        current_price=data.last_price,
    ):
        checks.append(pending("Entry retest", "Wait for the M15 breaker retest or a confirmed M1 micro-model/breaker retest."))
        return evaluate_checks(direction, checks)
    if not confluence.contains(data.last_price):
        checks.append(pending("Entry location", "Price has moved away from the breaker/OTE entry zone."))
        return evaluate_checks(direction, checks)
    checks.append(passed("Entry retest", "Price returned to the breaker/OTE entry zone."))

    if data.tick_size is None or data.tick_size <= 0:
        checks.append(unavailable("Instrument tick size", "A verified positive tick size is required to place a stop strictly beyond the purge wick."))
        return evaluate_checks(direction, checks)
    stop = structural_stop_price(protected, data.tick_size, direction)
    if is_invalidated(data.last_price, protected, direction):
        checks.append(RuleCheck("Structural invalidation", CheckState.FAIL, "Price has traded beyond the protected purge extreme."))
        return evaluate_checks(direction, checks)
    checks.append(passed("Structural invalidation", f"Stop reference is one tick beyond protected extreme {protected}."))

    crt_high = next((level.price for level in references.levels if level.name == "CRT High"), None)
    crt_low = next((level.price for level in references.levels if level.name == "CRT Low"), None)
    if crt_high is None or crt_low is None:
        checks.append(unavailable("CRT targets", "The active CRT high and low are required for TP1 and TP2."))
        return evaluate_checks(direction, checks)
    tp1 = (crt_high + crt_low) / 2
    tp2 = crt_high if direction is Direction.BULLISH else crt_low
    if direction is Direction.BULLISH and not entry < tp1 < tp2:
        checks.append(RuleCheck("CRT targets", CheckState.FAIL, "The CRT midpoint and opposing boundary are not both above the entry."))
        return evaluate_checks(direction, checks)
    if direction is Direction.BEARISH and not tp2 < tp1 < entry:
        checks.append(RuleCheck("CRT targets", CheckState.FAIL, "The CRT midpoint and opposing boundary are not both below the entry."))
        return evaluate_checks(direction, checks)
    try:
        rr = risk_reward_ratio(entry, stop, tp2, direction)
    except ValueError:
        checks.append(RuleCheck("Minimum reward", CheckState.FAIL, "The CRT target is not directionally beyond the structural stop and entry."))
        return evaluate_checks(direction, checks)
    if rr < Decimal("2.5"):
        checks.append(RuleCheck("Minimum reward", CheckState.FAIL, f"TP2 provides {rr:.2f}R; the minimum is 2.5R."))
        return evaluate_checks(direction, checks)
    checks.append(passed("Minimum reward", f"TP2 provides {rr:.2f}R (minimum 2.5R)."))
    base = evaluate_checks(direction, checks)
    return StrategyEvaluation(
        status=base.status,
        direction=direction,
        checks=base.checks,
        entry=entry,
        stop=stop,
        tp1=tp1,
        tp2=tp2,
        invalidation=protected,
    )
