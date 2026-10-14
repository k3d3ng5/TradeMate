# Master Trading Plan, Strategy & A+ Setup Execution Manual (v2.0)

> **Operational rules:** This strategy draft describes ideas beyond the data currently connected to the bot. Use [TRADE_RULES.md](TRADE_RULES.md) for active signal rules. News, fundamental, and positioning inputs are not connected to live signal generation.

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

### Session Kill Zones (UTC-5 EST / UTC+1 WAT)
Market liquidity sweeps and directional expansions cluster around high-volume institutional operating windows. All lower-timeframe execution must occur within these official Kill Zones:
* **London Kill Zone**: 02:00 AM – 05:00 AM EST (07:00 AM – 11:00 AM WAT)
* **New York Kill Zone**: 07:00 AM – 11:00 AM EST (01:00 PM – 05:00 PM WAT)

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

## 6. Integrated Macro Protocol: News, Fundamentals & Sentiment Analysis

To trade with true institutional authority, technical CRT levels must be validated by fundamental drivers and sentiment analysis. 

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      INTEGRATED TRADING DECISION MATRIX                     │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. FUNDAMENTALS ──► Sets Macro Direction & HTF Draw on Liquidity (The WHY)   │
│ 2. SENTIMENT    ──► Identifies Trapped Retail Orders & COT Extremes (WHO)   │
│ 3. TECHNICALS   ──► CRT Ranges, Key POIs & Session Kill Zone Timing (WHERE) │
│ 4. NEWS EVENT   ──► Acts as the Volatility Catalyst for the Purge (WHEN)    │
└─────────────────────────────────────────────────────────────────────────────┘
```

### A. Fundamental Analysis (The Directional Driver)
* **Central Bank Interest Rate Differentials**: Capital flows naturally toward currencies backed by higher or rising interest rates (hawkish central banks) and away from low-yielding currencies (dovish central banks).
* **Key Macro Indicators**: Monitor high-impact tier-1 releases—Non-Farm Payrolls (NFP), Consumer Price Index (CPI/Inflation), GDP Growth, and Central Bank Policy Rate Decisions.
* **Rule**: Fundamentals dictate the **Higher Timeframe Draw on Liquidity (DOL)**. If macro data favors USD strength, restrict setup selection exclusively to Bearish CRTs on EUR/USD and GBP/USD.

### B. Sentiment Analysis (Spotting the Herd)
* **Commitment of Traders (COT) Report**: Track weekly positioning data released by the CFTC. Monitor **Large Non-Commercials (Hedge Funds / Institutional Speculators)** vs. **Small Traders (Retail)**.
* **Retail Herd Traps**: When retail sentiment shows extreme bias (>75% long or short), smart money often engineers a rapid **Turtle Soup purge** to wipe out retail stop losses before resuming the macro trend.

### C. News & High-Volatility Execution Protocol
High-impact news events create rapid liquidity purges. To manage risk during news releases:
1. **No Pre-News Gambling**: Never open new positions inside 15 minutes before a tier-1 red-folder news release (NFP, CPI, FOMC).
2. **The Post-News Reaction Workflow**:
   * **Step 1 (The News Sweep)**: Allow the initial news spike to purge liquidity at a key 4H CRT boundary or fill an FVG.
   * **Step 2 (The M15 Engulfment)**: Wait for volatility to settle and confirm that a 15M candle body closes back inside the CRT range (**Model 1 / CISD**).
   * **Step 3 (The Retest Entry)**: Place a limit order on the retest of the purge candle's open body or Breaker Block once market spreads normalize.

---

## 7. The Anatomy of an A+ Setup (7-Point Checklist)

An **A+ Setup** represents the highest statistical edge in trading. Do not execute a trade unless all seven conditions are satisfied:

```
+-----------------------------------------------------------------------------------+
|                            A+ SETUP CONFLUENCE CHECKLIST                          |
+-----------------------------------------------------------------------------------+
|  [ ] 1. Macro & Fundamental Alignment: HTF order flow & economic driver agree.    |
|  [ ] 2. Session Kill Zone   : Time falls inside London (07-11) or NY (13-17 WAT).  |
|  [ ] 3. Key POI Level       : Setup occurs at a 4H FVG, OB, Breaker, or OTE zone.  |
|  [ ] 4. Liquidity Sweep     : Price purged PDH/PDL, Asia Range, or 4H CRT boundary.  |
|  [ ] 5. Candlestick Trigger : Pin Bar sweep + Model 1 Engulfing Bar close on M15.  |
|  [ ] 6. Opening Price Rule  : Buy below session open (OLHC) / Sell above open (OHLC).|
|  [ ] 7. Asymmetric R:R      : Minimum 1:2.5 Risk-to-Reward ratio with 1% max risk.  |
+-----------------------------------------------------------------------------------+
```

---

## 8. Trade Management & Position Sizing Engine

To survive losing streaks and compound gains, calculate position size mathematically using the exact stop-loss distance in pips/ticks.

### Position Sizing Formula
$$	ext{Position Size (Lots)} = rac{	ext{Account Capital} 	imes 	ext{Risk Percentage}}{	ext{Stop Loss Distance (Pips)} 	imes 	ext{Pip Value}}$$

### Execution & Exit Protocols
* **Hard Stop-Loss Requirement**: Place a hard stop-loss behind the protected swing extreme immediately upon order placement. Never use mental stops.
* **TP1 Partial Profit & Breakeven**: Automatically exit 50% of position size at the **50% midpoint of the active CRT dealing range** (TP1) and adjust Stop Loss to **Breakeven**.
* **TP2 Full Target Exit**: Allow the remaining 50% position to run toward the **opposing CRT High/Low boundary or HTF Draw on Liquidity**.
* **Journal Every Trade**: Record screenshots of HTF bias, Kill Zone timing, Model 1 confirmation, R:R ratio, and trade outcome. Review weekly to refine execution.
