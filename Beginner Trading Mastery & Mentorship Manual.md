# Beginner Trading Mastery & Mentorship Manual

*A Step-by-Step Guide to Rule-Based Trading with Candle Range Theory*

Merged draft 1 | For educational use only

> **Operational rules:** This is a teaching draft. For current bot behavior, session hours, confidence scoring, and supported data, use [TRADE_RULES.md](TRADE_RULES.md). Where they differ, TRADE_RULES.md takes precedence. The companion PDF is an older merged draft.

## Important Notice

This book is educational material. It is not financial advice and does not recommend that you buy or sell any instrument. Trading leveraged products such as forex carries a high risk of loss, up to and including your entire deposit. A large share of retail traders lose money.

Every win rate, reward-to-risk figure and dollar amount in this book is an illustration chosen to show how the maths works. None of them is a result you should expect. Hypothetical examples do not guarantee future performance.

Practise on a demo account first, never risk money you cannot afford to lose, and consider speaking with a licensed financial adviser before trading with real capital.

## How to Use This Book

This manual takes an absolute beginner from the mechanics of the forex market to executing a complete, rule-based trading plan with discipline. Read the modules in order. Each one builds on the last, and Module 8 turns everything into a daily routine, a practice roadmap and a self-test.

Professional trading is the repeated execution of a statistical edge under strict risk control. Your whole career reduces to three imperatives:

1. **Make pips**: identify high-probability setups aligned with institutional order flow.
2. **Keep pips**: protect your capital through strict money management.
3. **Repeat**: execute the same rules, consistently, without emotional deviation.

### The Four House Rules

These four standards apply everywhere in this book. They are deliberately strict.

| Rule | Standard |
| :-- | :-- |
| **Risk per trade** | 1% of account equity, maximum |
| **Reward-to-risk** | Minimum 1:2.5 on every trade |
| **A+ setups only** | All six checklist points present. Five out of six is a no-trade |
| **Demo first** | Three consecutive profitable months on demo before any real money |

---

## Module 1. Foundations of Financial Markets & Forex Mechanics

Before analysing a single chart, you must understand how the market works.

### What Is Forex?

The foreign exchange (Forex or FX) market is the global, decentralised marketplace for trading national currencies. It runs 24 hours a day, five days a week, and is the largest and most liquid financial market in the world.

Currencies are always traded in **pairs**: a **base currency** (listed first) and a **quote currency** (listed second). In EUR/USD:

- **EUR** is the base currency.
- **USD** is the quote currency.
- A quote of **1.1050** means 1 euro is worth 1.1050 US dollars.

### Pips, Lots and Order Types

**Pip (percentage in point).** The standard unit of price movement. For most pairs, 1 pip is a change of 0.0001 in the quote. For Japanese yen pairs, 1 pip is 0.01.

**Lot sizes.** The standard trade volumes, measured in units of the base currency:

| Lot Type | Units of Base Currency | Approx. Value per Pip (EUR/USD) | Rough Account Size (guide only) |
| :-- | :-- | :-- | :-- |
| **Standard lot** | 100,000 | $10.00 | $50,000+ |
| **Mini lot** | 10,000 | $1.00 | $5,000+ |
| **Micro lot** | 1,000 | $0.10 | $500+ |

**Order types.**

- **Market order:** executes immediately at the current price.
- **Limit order:** executes at a specified price or better. A buy limit sits below the current price. A sell limit sits above it.
- **Stop order:** becomes a market order when price reaches a specified level. A buy stop sits above the current price. A sell stop sits below it.

### Leverage, Margin and the Margin Call

**Leverage** lets you control a large position with a small deposit called **margin**. It is expressed as a ratio such as 50:1 or 100:1. Leverage magnifies losses exactly as much as it magnifies gains.

- **Used margin:** the collateral your broker locks to keep your trades open.
- **Usable (free) margin:** equity minus used margin. This is your remaining room to absorb price swings.
- **Margin call:** when losses consume your usable margin, the broker forcibly closes your trades to prevent a negative balance.

> **The Godfather's Gold Rule:** Over-leverage is the top killer of beginner accounts. Treat leverage as a tool of precision, and never risk more than 1% of equity on a single trade.

---

## Module 2. The Language of Price & Candlestick Anatomy

Japanese candlesticks give a visual picture of market psychology: the ongoing battle between buyers (bulls) and sellers (bears).

### Anatomy of a Candlestick

Every candle records price over a fixed period using four data points: **Open, High, Low and Close (OHLC)**.

- **Real body:** the distance between the open and the close.
- **Wicks (shadows or tails):** the thin lines above and below the body, marking the highest and lowest prices reached in that period.

### Three Core Candlestick Patterns

**1. The Pin Bar (Hammer and Shooting Star).** A very long wick, at least twice the length of the body, with a small body near one extreme.

- *Bullish pin bar (hammer):* a long lower wick shows buyers rejected lower prices.
- *Bearish pin bar (shooting star):* a long upper wick shows sellers rejected higher prices.

**2. The Engulfing Bar.** A two-candle pattern in which the real body of the second candle completely covers the real body of the first.

- *Bullish engulfing:* a green or white body engulfs a smaller red or black body, typically at support.
- *Bearish engulfing:* a red or black body engulfs a smaller green or white body, typically at resistance.

**3. The Inside Bar (Harami).** A two-candle pattern in which the entire range of the second candle (the "baby") stays inside the range of the first (the "mother bar"). It signals indecision and energy building up before an expansion.

---

## Module 3. Candle Range Theory (CRT) & Institutional Mechanics

Candle Range Theory teaches that every candle on every timeframe is a **time-based range** with a fixed opening time, closing time, high and low. The extreme high and low of each range act as **liquidity pools**: clusters of resting stop orders that large participants can trade against.

### The Three Pillars: Liquidity, Time and Price

1. **Liquidity.** Price moves constantly from one liquidity pool to another.
   - *Buyside liquidity (BSL):* stop-losses from short sellers and buy-stop entries resting above candle highs.
   - *Sellside liquidity (SSL):* stop-losses from long buyers and sell-stop entries resting below candle lows.
2. **Time.** Ranges open and close within strict calendar and clock boundaries.
3. **Price.** The candle range is the structural container in which value is discovered.

Liquidity + Time + Price = Time-based ranges (CRT)

### The CRT Market Cycle

Every complete range moves through three phases:

**Accumulation (range formation) → Manipulation (liquidity purge) → Distribution (expansion)**

1. **Accumulation:** price forms an initial range with clear high and low boundaries.
2. **Manipulation:** price is driven beyond a boundary, a false breakout known as a *Turtle Soup*, to tap the resting orders there.
3. **Distribution:** price reverses forcefully back through the range toward the opposite boundary.

### Structural Variations of CRT

| CRT Type | Structure | Typical Behaviour |
| :-- | :-- | :-- |
| **3-candle CRT** | Candle 1 = range. Candle 2 = manipulation. Candle 3 = distribution. | The standard textbook cycle |
| **2-candle CRT** | Candle 1 = range. Candle 2 does both manipulation and expansion. | Common around high-impact news |
| **Inside bar CRT** | Candle 1 = mother range. Candles 2 onward consolidate inside it. | Prolonged liquidity build-up |

---

## Module 4. Time Structure Sequence (TSQ) & Multi-Timeframe Alignment

The Time Structure Sequence maps the internal journey of price inside a CRT range, across several timeframes at once.

### Multi-Timeframe (MTF) Alignment Matrix

Keep your higher-timeframe (HTF) context chart and your lower-timeframe (LTF) execution chart strictly paired:

| Higher Timeframe Context (CRT) | Intermediate Narrative | Lower Timeframe Execution |
| :-- | :-- | :-- |
| **Monthly** | Weekly | **Daily** |
| **Weekly** | Daily | **4-Hour** |
| **Daily** | 4-Hour | **1-Hour** |
| **4-Hour** | 1-Hour | **15-Minute** |
| **1-Hour** | 15-Minute | **5-Minute** |

### Session Kill Zones

Liquidity sweeps and directional expansions cluster in high-volume windows. Execute only inside these Kill Zones:

| Kill Zone | Time (New York time) | Why It Matters |
| :-- | :-- | :-- |
| **London** | 02:00 AM to 05:00 AM | Interbank liquidity injection |
| **New York** | 07:00 AM to 11:00 AM | US open and commodities volume |

*Set your chart timezone to New York time so the windows stay fixed on your screen. New York time shifts by an hour with daylight saving (EST in winter, EDT in summer), so check your platform's clock whenever the clocks change.*

### The Five Delivery Phases of TSQ

After a higher-timeframe liquidity purge, price typically unfolds in five phases:

1. **Phase 1, Turtle Soup:** the initial sweep beyond a key CRT high or low, trapping breakout traders before price snaps back inside the range.
2. **Phase 2, Model 1:** a candle body closes above or below the purge candle, confirming that institutional participants have taken control. This creates the entry level.
3. **Phase 3, Breaker Block:** a market structure shift (MSS) in which price retests the failed order block that caused the trap.
4. **Phase 4, Optimal Trade Entry (OTE):** a retracement into the 60% to 75% Fibonacci zone, ideally overlapping a breaker block or fair value gap, offering a low-risk continuation entry.
5. **Phase 5, Kiss of Death:** the final sweep or false move immediately before price accelerates into the main draw on liquidity, the target it has been heading for.

---

## Module 5. The Model 1 Execution Engine

Model 1 is the core trigger of the CRT/TSQ framework. It turns market confirmation into a precise entry, stop and target.

### Step 1. Identify the Setup

During an active Kill Zone, wait for a candle to do one or both of the following:

- **Purge liquidity:** sweep beyond a Previous Day High or Low (PDH/PDL) or a CRT boundary.
- **Fill liquidity:** rebalance an open fair value gap (FVG) or test an order block.

### Step 2. Wait for the Engulf Confirmation

The next candle must close back inside, or engulf, the purge candle.

- **Bullish setup:** a candle closes above the high or open of the purge candle.
- **Bearish setup:** a candle closes below the low or open of the purge candle.

### Step 3. Choose the Entry Price

- **Open body price:** use when the purge candle is thick, or closes just beyond its open.
- **Wick level (50% of the wick):** use when the purge candle has a long wick and a small body.

Place the entry as a **limit order**. If price expands away without retesting your level, you have missed the trade. Do not chase.

### Step 4. Set the Stop and the Targets

- **Stop-loss:** strictly beyond the extreme high or low of the purge candle, the swing extreme your idea depends on.
- **Take-profit 1 (partial):** the 50% midpoint of the active CRT range.
- **Take-profit 2 (full target):** the opposing CRT high or low, or the higher-timeframe draw on liquidity.
- **Minimum reward-to-risk:** 1:2.5. If the target does not offer it, skip the trade.

### Worked Example (illustrative numbers only)

EUR/USD, bearish setup inside the London Kill Zone:

1. The daily bias is bearish. The previous day's high sits at 1.1060.
2. A 15-minute candle sweeps above that high, reaching 1.1068, then closes back below it. Its body opens at 1.1058.
3. The next candle closes below the purge candle's low. Model 1 is confirmed.
4. **Entry:** sell limit at 1.1058, the open of the purge candle body.
5. **Stop-loss:** 1.1068, the extreme of the purge candle. Risk is 10 pips.
6. **Take-profit 2:** 1.1033, the opposing range boundary. Reward is 25 pips.
7. **Reward-to-risk:** 25 ÷ 10 = 1:2.5, which meets the minimum.

If price had never retraced to 1.1058, there would be no trade.

---

## Module 6. Confluence & Market Regime Strategy

High-probability setups appear when institutional liquidity mechanics and classical technical factors line up at the same price.

### Step 1. Classify the Market Regime

Strategies must match the environment. Breakout trades in a ranging market, or counter-trend trades in a strong trend, produce consistent losses.

| Market Regime | What It Looks Like | What You Do |
| :-- | :-- | :-- |
| **Trending** | Higher highs and higher lows (uptrend), or lower highs and lower lows (downtrend). Price respects the 8 EMA and 21 SMA. | Trade only in the direction of the trend. Buy pullbacks to support or the EMAs, or sell rallies to resistance or the EMAs. |
| **Ranging** | Price oscillates between a defined ceiling (supply or resistance) and floor (demand or support). | Trade reversals from the outer boundaries using liquidity sweeps and engulfing confirmation. Avoid the middle of the range. |
| **Choppy** | Overlapping wicks, no clean boundaries, inconsistent direction. | **Do not trade.** Close the chart and preserve your capital until clear structure returns. |

### Step 2. Read the Visual Footprints

The candlestick patterns from Module 2 are the visible signature of the institutional mechanics in Modules 3 to 5:

- **Pin bar = Turtle Soup sweep.** The long wick shows breakout orders being trapped and rejected.
- **Engulfing bar = Model 1 confirmation.** The second body fully covers the purge candle body.
- **Inside bar = Inside Bar CRT.** Liquidity builds on both sides, setting up an explosive purge and expansion.

### Step 3. Look for Confluence

- **Dynamic support and resistance:** the 8 EMA and 21 SMA on the 4-hour and daily charts show trend alignment.
- **Fibonacci retracement zones:** entries that align with the 50%, 61.8% or 70.7% levels.
- **Horizontal structure and key levels:** sweeps that occur at a fair value gap, an order block, or a major support-turned-resistance level.

### The A+ Setup: Six-Point Checklist

An **A+ setup** carries the highest edge this framework can offer. **All six conditions must be present. If one is missing, there is no trade.**

| # | Condition | What You Need to See |
| :-- | :-- | :-- |
| 1 | **Higher-timeframe bias** | The last Daily or 4-Hour candle closed in your trade direction, and its order flow is clear |
| 2 | **Kill Zone timing** | The current time is inside the London or New York Kill Zone |
| 3 | **Liquidity sweep** | Price has purged the PDH, PDL or a CRT boundary (or filled an FVG or order block) |
| 4 | **Candlestick trigger** | A pin bar sweep followed by a Model 1 engulfing close |
| 5 | **Confluence overlap** | The level lines up with the 8 EMA or 21 SMA, a 50% to 61.8% Fibonacci zone, or a key FVG, order block or support and resistance level |
| 6 | **Asymmetric reward-to-risk** | At least 1:2.5, with no more than 1% of equity at risk |

---

## Module 7. The "Be the Casino" Risk & Mindset Engine

To last in this business you must drop the gambler's mindset and think like a casino operator. A casino does not win every hand. It wins because its edge is fixed and its risk on any one bet is capped, so over thousands of hands the maths does the work.

### The Mathematics of Expectancy

Expectancy per trade = (Win rate × Reward) − (Loss rate × Risk)

Below, the risk is $100 on every trade and the reward is $250 (a 1:2.5 reward-to-risk ratio). The win rates are assumptions for illustration, not forecasts.

| Assumed Win Rate | 100 Trades | Net Result | Average per Trade |
| :-- | :-- | :-- | :-- |
| **50%** | 50 wins × $250 = $12,500. 50 losses × $100 = $5,000. | +$7,500 | +$75 (+0.75R) |
| **45%** | 45 wins × $250 = $11,250. 55 losses × $100 = $5,500. | +$5,750 | +$57.50 (+0.575R) |

Two lessons sit inside this table:

1. **Reward-to-risk lowers the win rate you need.** At 1:2.5, the break-even win rate is 1 ÷ (1 + 2.5), about 28.6%. This is a maths fact about the ratio. It is not a promise that your own results will reach any particular win rate. Your journal and your demo results are what tell you that.
2. **Losing streaks are normal.** Over a hundred trades at a 50% win rate, runs of five or six losses in a row are common. At 1% risk, five straight losses cost about 5% of the account. At 5% risk per trade, the same streak costs roughly a quarter of it. This is why the 1% rule exists.

### The Position Sizing Formula

Never choose a lot size by feel. Derive it from your stop-loss distance:

Position size (lots) = (Account equity × Risk %) ÷ (Stop-loss distance in pips × Pip value per lot)

**Example.** Account equity $10,000. Risk 1%, which is $100. Stop-loss 20 pips on EUR/USD, where one standard lot is worth about $10 per pip.

Position size = $100 ÷ (20 × $10) = **0.50 lots** (five mini lots).

The stop-loss comes first, from the chart. The position size then adjusts to fit the 1% budget. The stop never moves to fit a bigger position.

### The 90-Day Demo Discipline Protocol

Before risking real money, make the Godfather's Rule your personal commitment:

> *"I will demo trade for at least three consecutive months on a single asset pair, until I achieve consistent profitability and execute my rules without emotional deviation."*

The demo period proves three things: you can operate your platform flawlessly, you can follow your risk rules, and you can sit through a normal losing streak without breaking discipline.

---

## Module 8. Execution, Trade Management & Practice

This module turns knowledge into routine. It contains the A+ execution workflow, the rules of discipline, a pre-flight checklist, a practice roadmap and a self-test.

### The A+ Execution Workflow

1. **Identify the macro direction.** Open the Daily or 4-Hour chart. If the last candle closed bullish, your bias is bullish and your target is the opposing high. If it closed bearish, the reverse.
2. **Mark the liquidity targets.** Draw the Previous Day High (PDH), Previous Day Low (PDL) and any higher-timeframe rejection blocks.
3. **Wait for a Kill Zone.** Do not watch the chart or place orders outside 02:00 to 05:00 or 07:00 to 11:00 New York time.
4. **Observe the purge.** On the paired lower timeframe, wait for price to sweep beyond the PDH or PDL and reject, leaving a long-wick pin bar.
5. **Confirm the structural shift.** Wait for the next candle to close back inside, or engulf, the purge candle body (Model 1).
6. **Calculate size and place the orders.**
   - **Entry:** limit order at the purge candle's open body, or at the 50% wick level if the wick is long.
   - **Stop-loss:** beyond the purge candle's extreme.
   - **Take-profit:** target 1 at the 50% CRT midpoint, target 2 at the opposing higher-timeframe boundary, with at least 1:2.5 reward-to-risk.

### Rules of Discipline

- **No mental stops.** Place a hard stop-loss with the broker the moment you place the order.
- **Set and forget.** Once entry, stop and targets are in, step away. Do not move stops out of fear.
- **Never chase.** If price expands without retesting your limit entry, cancel the order and wait for the next setup.
- **Journal every trade.** Save screenshots of the higher-timeframe bias, the Kill Zone timing, the Model 1 confirmation, the reward-to-risk ratio and the outcome. Review them weekly. A template is in Appendix A.

### Pre-Flight Checklist

Before you click "Execute Order", confirm every item:

1. Is the time inside the London or New York Kill Zone?
2. Is the higher-timeframe bias clear and aligned with the trade?
3. Has price purged liquidity, or filled an FVG or order block?
4. Has a lower-timeframe candle closed to engulf the purge candle (Model 1)?
5. Does the level overlap with an EMA, a Fibonacci zone or a key level?
6. Is the stop-loss beyond the purge candle's extreme, and does the target give at least 1:2.5?
7. Is the position size calculated so that no more than 1% of equity is at risk?

If any answer is "no", you do not have an A+ setup. Do not place the trade.

### The 90-Day Action Roadmap

- **Days 1 to 30, Anatomy and backtesting.** Study the patterns, mark PDH and PDL levels, and find Model 1 purges across historical charts.
- **Days 31 to 60, Live demo execution.** Trade on demo only inside the London and New York Kill Zones, and log every trade.
- **Days 61 to 90, Performance audit.** Review your win rate, profit factor and rule adherence.

**The go-live gate.** Live demo trading starts around Day 31, so three full demo months finish around Day 120. Do not move to real money at Day 90 just because the calendar says so. Go live only after three consecutive profitable demo months with your rules followed, and then start with a micro account.

### 10-Question Self-Check Quiz

1. What are the three core pillars of Candle Range Theory?
2. What are the hours of the London and New York Kill Zones?
3. If you are analysing a Daily CRT range, which chart is your lower-timeframe execution chart?
4. Which candlestick pattern is the visual signature of a Turtle Soup liquidity purge?
5. What event confirms a Model 1 entry setup?
6. Where do you place the limit order when the purge candle is thick and heavy?
7. What is the minimum reward-to-risk ratio allowed in this strategy?
8. Define usable margin, and explain what happens in a margin call.
9. Calculate the position size in mini lots for a $5,000 account risking 1% with a 25-pip stop-loss.
10. What should you do when the market is choppy and erratic?

#### Answer Key

1. **Liquidity, Time and Price.**
2. **London:** 02:00 to 05:00. **New York:** 07:00 to 11:00 (New York time).
3. The **1-Hour chart**, per the MTF Alignment Matrix.
4. The **pin bar** (hammer or shooting star).
5. A lower-timeframe candle **body close** that engulfs the purge candle.
6. At the **opening price of the purge candle body**.
7. **1:2.5.**
8. Usable margin is the equity still available to open or hold positions. In a margin call, the broker forcibly closes open trades when equity falls below the required margin.
9. Risk = $50. $50 ÷ (25 pips × $1 per pip per mini lot) = **2 mini lots (0.20 lots).**
10. **Close the charts and stay out** to preserve capital.

---

## Module 9. Master Glossary

- **A+ setup:** a trade in which all six checklist conditions are present at once.
- **Accumulation:** the first phase of a candle range, in which liquidity builds on both sides.
- **Breaker block:** a failed order block involved in a market structure shift, which then acts as support or resistance.
- **Buyside liquidity (BSL):** stop and buy-stop orders resting above key candle highs.
- **Candle Range Theory (CRT):** a framework that treats every candle as a time-based range with objective liquidity boundaries.
- **Distribution:** the expansion phase, in which price drives toward the opposing liquidity target.
- **Draw on liquidity:** the liquidity pool price is heading toward; your main profit target.
- **Expectancy:** the average result per trade, in money or in R, over many trades.
- **Fair value gap (FVG):** a three-candle imbalance showing inefficient price delivery.
- **Kill Zones:** the London and New York session windows in which institutional orders cluster.
- **Kiss of Death:** the final sweep or false move just before price accelerates into the main target.
- **Manipulation:** a false breakout or sweep designed to trigger stops before a reversal.
- **Market structure shift (MSS):** a break of structure signalling a change in direction.
- **Model 1:** a rule-based entry triggered by a liquidity purge or fill, followed by a structural engulfing close.
- **Optimal trade entry (OTE):** the 60% to 75% Fibonacci retracement zone, a high-probability continuation entry.
- **PDH / PDL:** the Previous Day High and Previous Day Low, key liquidity targets.
- **Pin bar:** a rejection candle with a long wick and a small real body.
- **R (R-multiple):** one unit of risk. A trade that makes 2.5 times what it risked is a +2.5R trade.
- **Sellside liquidity (SSL):** stop and sell-stop orders resting below key candle lows.
- **Time Structure Sequence (TSQ):** the five-phase delivery progression of price inside a CRT range.
- **Turtle Soup:** a liquidity raid that sweeps beyond a prior high or low before reversing.

---

## Appendix A. Trade Journal Template

Copy one row per trade. Review the whole table every week.

| Date | Pair | Kill Zone | HTF Bias | Entry / Stop / Target | R:R | Checklist (out of 6) | Result (R) | Rules Followed? | Notes |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- | :-- | :-- | :-- |
|  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |

**Weekly review questions:** Did I trade only inside Kill Zones? Did every trade score 6 out of 6? Did I ever move a stop or chase an entry? What did my best and worst trades have in common?

*Make pips. Keep pips. Repeat.*
