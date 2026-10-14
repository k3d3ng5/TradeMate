# Master Trading Plan, Strategy & A+ Setup Execution Manual

> **Operational rules:** This is an older strategy draft. Use [TRADE_RULES.md](TRADE_RULES.md) for the active rules and bot behavior.

## 1. Executive Framework & The Pipsology Foundation

Professional trading is not speculative gambling; it is the execution of a statistical edge with strict risk management. To achieve long-term profitability, a trader must adopt the mindset of a casino operator. Casinos do not win every single hand or spin, but because their statistical edge is hardcoded and their risk is capped, the house always wins over a large sample of events.

As established across the foundational mentorship materials and classical market guides, a trader's career relies on three core operational imperatives:
1. **Make pips**: Identify high-probability market setups aligned with institutional order flow.
2. **Keep pips**: Protect capital through strict money management and risk control.
3. **Repeat**: Execute the identical rule-based strategy consistently without emotional deviation.

```
+-----------------------------------------------------------------------+
|                       THE CASINO EXPECTANCY MATRIX                    |
+-----------------------------------------------------------------------+
|  Win Rate: 45% - 50%                                                  |
|  Target Risk-to-Reward Ratio: 1 : 2.5 Minimum                         |
|  Account Risk per Trade: 1.0% Maximum                                 |
|                                                                       |
|  Trade Expectancy = (Win % x Reward) - (Loss % x Risk)                |
|                   = (0.50 x 2.5R) - (0.50 x 1.0R) = +0.75R / Trade     |
+-----------------------------------------------------------------------+
```

### The Three-Month Demo Trading Mandate
Before risking real capital, every trader must complete at least two to three consecutive months of profitable demo trading. This period proves that you can execute your order entry platform flawlessly, adhere to risk management rules, and withstand natural losing streaks without breaking discipline.

---

## 2. Market Regime & Structure Classification

Before looking for entries, you must classify the overarching market regime. Trading strategies must match the environment; taking breakout trades in a ranging market or counter-trend trades in a strong trend leads to consistent losses.

| Market Regime | Structural Characteristics | Strategic Action |
| :--- | :--- | :--- |
| **Trending Market** | Consecutive Higher Highs and Higher Lows (Uptrend) or Lower Highs and Lower Lows (Downtrend). Price respects the 8 EMA and 21 SMA. | Trade exclusively in the direction of the dominant trend. Buy pullbacks to support/EMAs or sell rallies to resistance/EMAs. |
| **Ranging Market** | Price oscillates horizontally between a defined resistance/supply ceiling and a support/demand floor. | Trade reversals from the outer boundaries using liquidity sweeps and engulfing confirmations. Avoid trading in the middle of the range. |
| **Choppy / Erratic Market** | Price moves without clean boundaries, creating overlapping candle wicks and inconsistent direction. | **Do Not Trade.** Close the chart and preserve capital until clear structure emerges. |

---

## 3. Institutional Context: Candle Range Theory (CRT)

Candle Range Theory establishes that every price candle on any timeframe represents a time-based range with a fixed opening time, closing time, high, and low. The extreme highs and lows of a candle range act as liquidity pools containing resting buyside and sellside stop orders.

```
                       Buyside Liquidity Pool (CRT High)
                    ---------------------------------------
                    |                                     |
                    |          Candle Range Body          |
                    |            (Accumulation)           |
                    |                                     |
                    ---------------------------------------
                       Sellside Liquidity Pool (CRT Low)
```

### Multi-Timeframe (MTF) Alignment Matrix
To ensure lower-timeframe execution aligns with higher-timeframe institutional direction, adhere strictly to these timeframe pairings:

| Higher Timeframe Context (CRT) | Lower Timeframe Execution (Model 1 / TSQ) |
| :--- | :--- |
| **Monthly Chart** | **Daily Chart** |
| **Weekly Chart** | **4-Hour Chart** |
| **Daily Chart** | **1-Hour Chart** |
| **4-Hour Chart** | **15-Minute Chart** |
| **1-Hour Chart** | **5-Minute Chart** |

### Session Kill Zones (UTC-5 / EST)
Market liquidity sweeps and directional expansions cluster around high-volume institutional operating windows. All lower-timeframe execution must occur within these official Kill Zones:
* **London Kill Zone**: 02:00 AM – 05:00 AM EST (UTC-5/UTC-4)
* **New York Kill Zone**: 07:00 AM – 11:00 AM EST (UTC-5/UTC-4)

---

## 4. The Time Structure Sequence (TSQ) Delivery Phases

Following a higher-timeframe liquidity purge, price action unfolds inside a range across a sequence of delivery phases. Understanding these phases allows you to identify exactly where price is in its journey.

```
[ Phase 1: Turtle Soup ]  ──►  [ Phase 2: Model 1 ]  ──►  [ Phase 3: Breaker Block ]
   (Liquidity Sweep)             (Engulf Confirmation)           (Structure Shift)
                                                                       │
[ Draw on Liquidity ]    ◄──  [ Phase 5: Kiss of Death ] ◄── [ Phase 4: OTE Zone ]
   (Final Target)                (Final Trap / Sweep)           (60-75% Fibo Retest)
```

1. **Phase 1: Turtle Soup**: The initial liquidity sweep beyond a key CRT High/Low, trapping breakout traders before price sharply reverses back inside the range.
2. **Phase 2: Model 1 Engulfment**: The structural confirmation phase where a candle body closes above or below the purge candle, validating institutional control and creating the entry level.
3. **Phase 3: Breaker Block**: A Market Structure Shift (MSS) where price retests the failed order block candle that caused the trap.
4. **Phase 4: Optimal Trade Entry (OTE)**: A retracement into the 60% to 75% Fibonacci zone (overlapping with a Breaker or Fair Value Gap) providing a low-risk continuation entry.
5. **Phase 5: Kiss of Death**: The final liquidity sweep or false move occurring right before price accelerates into the main Draw on Liquidity target.

---

## 5. Technical Confluence & Pattern Integration

High-probability setups occur when classical candlestick patterns, moving averages, and institutional liquidity concepts align at the exact same price level.

### Visual Footprints of Institutional Mechanics
* **Pin Bar = Turtle Soup Sweep**: A Pin Bar featuring a long wick and small real body is the visual representation of a Turtle Soup liquidity sweep. The long wick shows retail breakout orders getting trapped and rejected by institutional counter-orders.
* **Engulfing Bar = Model 1 Confirmation**: An Engulfing pattern where the second candle body completely covers the purge candle body is the visual representation of Model 1 structural confirmation.
* **Inside Bar = Inside Bar CRT**: A small candle contained within a mother bar represents liquidity buildup on both sides, preparing the market for an explosive purge and expansion.

### Confluence Overlay Factors
* **Dynamic Support/Resistance**: Combining the 8 EMA and 21 SMA on 4-Hour and Daily charts to identify dynamic trend alignment.
* **Fibonacci Retracement Zones**: Aligning entries with the 50%, 61.8%, or 70.7% Fibonacci levels.
* **Horizontal Structure & Supply/Demand**: Verifying that sweeps occur at major support-turned-resistance or rejection blocks.

---

## 6. The Anatomy of an A+ Setup (6-Point Checklist)

An **A+ Setup** represents the highest statistical edge in trading. Do not execute a trade unless all six conditions are satisfied:

```
+-----------------------------------------------------------------------------------+
|                            A+ SETUP CONFLUENCE CHECKLIST                          |
+-----------------------------------------------------------------------------------+
|  [ ] 1. HTF Bias Alignment  : Higher timeframe order flow (Daily/4H) is clear.   |
|  [ ] 2. Session Kill Zone   : Current time is inside London or NY Kill Zone.      |
|  [ ] 3. Liquidity Sweep     : Price purged PDH/PDL or CRT boundary level.         |
|  [ ] 4. Candlestick Trigger : Pin Bar sweep + Model 1 Engulfing Bar close.        |
|  [ ] 5. Confluence Overlap  : Level aligns with 8/21 EMA or 50-61.8% Fibo zone.   |
|  [ ] 6. Asymmetric R:R      : Minimum 1:2.5 Risk-to-Reward ratio with 1% risk.   |
+-----------------------------------------------------------------------------------+
```

### Detailed Step-by-Step A+ Setup Execution Workflow:

1. **Identify Macro Direction (HTF)**: Open the Daily or 4-Hour chart. Confirm that the last candle closed in your trade direction (e.g., Daily bullish closed body = bullish bias targeting the opposing Daily high).
2. **Mark Key Liquidity Targets**: Mark the Previous Day High (PDH), Previous Day Low (PDL), or HTF Rejection Blocks.
3. **Wait for Kill Zone Window**: Do not monitor or place orders outside 02:00–05:00 EST or 07:00–11:00 EST.
4. **Observe the Liquidity Purge (Turtle Soup / Pin Bar)**: Wait for lower-timeframe price action to sweep beyond PDH or PDL and reject, forming a long-wick Pin Bar.
5. **Confirm Structural Shift (Model 1 / Engulfing Bar)**: Wait for the candle following the purge to close cleanly back inside or engulf the purge candle body.
6. **Calculate Position Size & Set Orders**:
   * **Entry**: Limit order set at the Purge Candle Opening Body (or 50% wick level if the wick is long).
   * **Stop-Loss**: Placed strictly beyond the protected swing extreme created by the purge candle.
   * **Take Profit**: Target 1 at 50% CRT range; Target 2 at the opposing HTF CRT boundary (minimum 1:2.5 R:R).

---

## 7. Trade Management & Position Sizing Engine

To survive losing streaks and compound gains, calculate position size mathematically using the exact stop-loss distance in pips/ticks.

### Position Sizing Formula
$$	ext{Position Size (Lots)} = rac{	ext{Account Capital} 	imes 	ext{Risk Percentage}}{	ext{Stop Loss Distance (Pips)} 	imes 	ext{Pip Value}}$$

### Execution Rules of Discipline
* **Never Use Mental Stops**: Place a hard stop-loss on the broker terminal immediately upon order entry.
* **Set and Forget**: Once the limit entry, stop-loss, and take-profit targets are placed, step away from the terminal. Do not manually adjust stops out of fear.
* **No Chasing Missed Trades**: If price expands aggressively without retesting your limit entry, cancel the order and wait for the next setup.
* **Journal Every Trade**: Record screenshots of HTF bias, Kill Zone timing, Model 1 confirmation, R:R ratio, and trade outcome. Review weekly to refine execution.
