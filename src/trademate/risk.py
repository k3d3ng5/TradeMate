"""Validated, read-only position risk calculations."""

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_DOWN


class RiskCalculationError(ValueError):
    """A risk request cannot be calculated from the supplied inputs/specs."""


@dataclass(frozen=True)
class InstrumentRiskSpecification:
    """Verified price/quantity metadata supplied by a market data provider."""

    tick_size: Decimal
    tick_value_loss: Decimal
    quantity_step: Decimal
    minimum_quantity: Decimal
    maximum_quantity: Decimal
    currency: str
    quantity_unit: str


@dataclass(frozen=True)
class RiskCalculation:
    direction: str
    entry: Decimal
    stop: Decimal
    planned_risk_amount: Decimal
    requested_risk_percent: Decimal
    quantity: Decimal
    estimated_loss: Decimal
    actual_risk_percent: Decimal
    risk_reward: Decimal | None = None


def calculate_position_risk(
    *,
    direction: str,
    entry: Decimal,
    stop: Decimal,
    equity: Decimal,
    equity_currency: str,
    risk_percent: Decimal,
    specification: InstrumentRiskSpecification | None,
    target: Decimal | None = None,
) -> RiskCalculation:
    """Calculate a rounded-down quantity only when every required input is verified.

    `tick_value_loss` is the loss in the provider's currency for one price tick
    at one quantity unit (for example, one MT5 lot). No currency conversion is
    inferred. The result excludes slippage, spread, commission, and gaps.
    """
    if not entry.is_finite() or not stop.is_finite() or (target is not None and not target.is_finite()):
        raise RiskCalculationError("Prices must be finite numbers.")
    side = direction.strip().lower()
    if side in {"buy", "long", "bullish"}:
        side = "long"
        if not stop < entry:
            raise RiskCalculationError("For a long, the stop must be below entry.")
        if target is not None and target <= entry:
            raise RiskCalculationError("For a long, the target must be above entry.")
    elif side in {"sell", "short", "bearish"}:
        side = "short"
        if not stop > entry:
            raise RiskCalculationError("For a short, the stop must be above entry.")
        if target is not None and target >= entry:
            raise RiskCalculationError("For a short, the target must be below entry.")
    else:
        raise RiskCalculationError("Direction must be long/buy or short/sell.")

    if not equity.is_finite() or equity <= 0:
        raise RiskCalculationError("Equity must be a positive number.")
    if not risk_percent.is_finite() or not Decimal(0) < risk_percent <= Decimal(1):
        raise RiskCalculationError("Risk per trade must be greater than 0 and no more than 1%.")
    if specification is None:
        raise RiskCalculationError("The provider has no verified quantity and tick-value specifications for this instrument.")
    if equity_currency.strip().upper() != specification.currency.strip().upper():
        raise RiskCalculationError(
            f"Currency mismatch: the instrument risk value is in {specification.currency}, "
            f"but equity was entered in {equity_currency.upper()}. No conversion rate is configured."
        )
    if (
        not specification.tick_size.is_finite()
        or not specification.tick_value_loss.is_finite()
        or not specification.quantity_step.is_finite()
        or not specification.minimum_quantity.is_finite()
        or not specification.maximum_quantity.is_finite()
        or min(
            specification.tick_size,
            specification.tick_value_loss,
            specification.quantity_step,
            specification.minimum_quantity,
        ) <= 0
        or specification.maximum_quantity < specification.minimum_quantity
    ):
        raise RiskCalculationError("Provider instrument specifications are missing or invalid.")

    price_risk = abs(entry - stop)
    ticks_at_risk = price_risk / specification.tick_size
    loss_per_quantity = ticks_at_risk * specification.tick_value_loss
    planned_risk = equity * risk_percent / Decimal(100)
    raw_quantity = planned_risk / loss_per_quantity
    quantity = (raw_quantity / specification.quantity_step).to_integral_value(rounding=ROUND_DOWN) * specification.quantity_step
    if quantity < specification.minimum_quantity:
        raise RiskCalculationError(
            f"The risk-based size is below the provider minimum of "
            f"{specification.minimum_quantity} {specification.quantity_unit}."
        )
    quantity = min(quantity, specification.maximum_quantity)
    estimated_loss = quantity * loss_per_quantity
    actual_risk_percent = estimated_loss / equity * Decimal(100)
    rr = None
    if target is not None:
        reward = abs(target - entry)
        rr = reward / price_risk
    return RiskCalculation(
        direction=side,
        entry=entry,
        stop=stop,
        planned_risk_amount=planned_risk,
        requested_risk_percent=risk_percent,
        quantity=quantity,
        estimated_loss=estimated_loss,
        actual_risk_percent=actual_risk_percent,
        risk_reward=rr,
    )


def parse_decimal(value: str, label: str) -> Decimal:
    """Parse a finite decimal value without accepting NaN or infinity."""
    try:
        number = Decimal(value.strip())
    except (InvalidOperation, AttributeError) as exc:
        raise RiskCalculationError(f"{label} must be a number.") from exc
    if not number.is_finite():
        raise RiskCalculationError(f"{label} must be a finite number.")
    return number
