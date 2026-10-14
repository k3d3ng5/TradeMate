import json
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Optional, List

class WebhookNotifier:
    """
    Handles real-time alert notifications to Discord and Telegram webhooks
    across the complete lifecycle of a trade (Signal, Fill, Breakeven, TP1, TP2, Stop Loss).
    """
    def __init__(self, discord_url: Optional[str] = None, telegram_token: Optional[str] = None, telegram_chat_id: Optional[str] = None):
        self.discord_url = discord_url
        self.telegram_token = telegram_token
        self.telegram_chat_id = telegram_chat_id

    def send_discord_alert(self, title: str, message: str, color: int = 3066993) -> bool:
        """Logs or sends a formatted alert for Discord Webhooks."""
        if not self.discord_url:
            print(f"[DISCORD NOTIFICATION]\n{title}\n{message}\n" + "-"*40)
            return True

        # Custom integration block for Discord webhook API
        payload = {
            "embeds": [
                {
                    "title": title,
                    "description": message,
                    "color": color,
                    "timestamp": datetime.utcnow().isoformat()
                }
            ]
        }
        # In live production, dispatch payload using requests/urllib to self.discord_url
        return True

    def send_telegram_alert(self, message: str) -> bool:
        """Logs or sends a Markdown alert for Telegram Channels."""
        if not self.telegram_token or not self.telegram_chat_id:
            print(f"[TELEGRAM NOTIFICATION]\n{message}\n" + "-"*40)
            return True

        # Custom integration block for Telegram Bot API
        payload = {
            "chat_id": self.telegram_chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }
        # In live production, dispatch payload to Telegram Bot endpoint
        return True


class CandlestickPatternAnalyzer:
    """
    Integrates Candlestick Trading Bible pattern recognition (Pin Bars, Engulfing Bars)
    and Forex Godfather Elite confluence indicators (8/21 EMA, Fibonacci OTE).
    """
    @staticmethod
    def is_pin_bar(open_p: float, high_p: float, low_p: float, close_p: float, bias: str) -> bool:
        """
        Detects if a candle is a Pin Bar / Shooting Star / Hammer.
        A valid Pin Bar has a tail at least 2x the body length.
        """
        body_size = abs(close_p - open_p)
        total_range = high_p - low_p
        if total_range == 0:
            return False

        if bias == 'BULLISH':  # Lower tail purge (Hammer / Bullish Pin Bar)
            lower_wick = min(open_p, close_p) - low_p
            return lower_wick >= (body_size * 2.0) and lower_wick >= (total_range * 0.5)
        elif bias == 'BEARISH':  # Upper tail purge (Shooting Star / Bearish Pin Bar)
            upper_wick = high_p - max(open_p, close_p)
            return upper_wick >= (body_size * 2.0) and upper_wick >= (total_range * 0.5)
        return False

    @staticmethod
    def is_engulfing(prev_open: float, prev_close: float, curr_open: float, curr_close: float, bias: str) -> bool:
        """
        Detects an Engulfing Bar pattern confirming Model 1 structural shift.
        """
        if bias == 'BULLISH':
            return (curr_close > curr_open) and (curr_close > max(prev_open, prev_close))
        elif bias == 'BEARISH':
            return (curr_close < curr_open) and (curr_close < min(prev_open, prev_close))
        return False

    @staticmethod
    def calculate_emas(df: pd.DataFrame, fast_period: int = 8, slow_period: int = 21) -> pd.DataFrame:
        """Calculates 8 EMA and 21 EMA for dynamic trend confluence."""
        df[f'ema_{fast_period}'] = df['close'].ewm(span=fast_period, adjust=False).mean()
        df[f'ema_{slow_period}'] = df['close'].ewm(span=slow_period, adjust=False).mean()
        return df

    @staticmethod
    def calculate_ote_range(low_p: float, high_p: float) -> Dict[str, float]:
        """Calculates 61.8% and 70.5% Fibonacci Optimal Trade Entry (OTE) levels."""
        diff = high_p - low_p
        return {
            'fib_500': high_p - (diff * 0.50),
            'fib_618': high_p - (diff * 0.618),
            'fib_705': high_p - (diff * 0.705),
            'fib_786': high_p - (diff * 0.786)
        }


class TSQExecutionEngine:
    """
    Master Execution Engine implementing Candle Range Theory (CRT),
    Time Structure Sequence (TSQ) Model 1, and Trade Lifecycle Management.
    """
    def __init__(
        self,
        htf_df: pd.DataFrame,
        ltf_df: pd.DataFrame,
        account_capital: float = 10000.0,
        risk_per_trade: float = 0.01,
        target_rr: float = 2.5,
        notifier: Optional[WebhookNotifier] = None
    ):
        self.htf_df = htf_df.copy()
        self.ltf_df = ltf_df.copy()
        self.capital = account_capital
        self.risk_per_trade = risk_per_trade
        self.target_rr = target_rr
        self.notifier = notifier or WebhookNotifier()
        self.active_trades: List[Dict] = []
        
        self._prepare_data()

    def _prepare_data(self):
        """Prepares timestamps, sorts chronologically, and computes indicators."""
        self.htf_df['timestamp'] = pd.to_datetime(self.htf_df['timestamp'])
        self.ltf_df['timestamp'] = pd.to_datetime(self.ltf_df['timestamp'])
        
        self.htf_df.sort_values('timestamp', inplace=True)
        self.ltf_df.sort_values('timestamp', inplace=True)
        
        # Calculate HTF Directional Order Flow Bias
        self.htf_df['htf_bias'] = np.where(self.htf_df['close'] > self.htf_df['open'], 'BULLISH', 'BEARISH')
        
        # Calculate EMAs for LTF confluence
        self.ltf_df = CandlestickPatternAnalyzer.calculate_emas(self.ltf_df)

    def is_in_killzone(self, timestamp: datetime) -> bool:
        """Checks if time falls within London (02:00-05:00) or NY (07:00-11:00) Kill Zones."""
        hour = timestamp.hour
        is_london = (2 <= hour < 5)
        is_ny = (7 <= hour < 11)
        return is_london or is_ny

    def scan_for_setups(self) -> Optional[Dict]:
        """
        Scans the latest candle sequence for an A+ Model 1 Setup.
        Combines Turtle Soup Purge, Model 1 Engulfment, Pin Bar Pattern, and EMA Confluence.
        """
        if len(self.ltf_df) < 5:
            return None

        latest_candle = self.ltf_df.iloc[-1]
        confirm_candle = self.ltf_df.iloc[-2]
        purge_candle = self.ltf_df.iloc[-3]
        
        timestamp = latest_candle['timestamp']
        if not self.is_in_killzone(timestamp):
            return None

        # Match HTF Order Flow
        htf_match = self.htf_df[self.htf_df['timestamp'] <= timestamp]
        if htf_match.empty:
            return None
        htf_bias = htf_match.iloc[-1]['htf_bias']

        # Determine Liquidity Boundaries (Previous 50 LTF bars extreme)
        bsl = self.ltf_df['high'].tail(50).max()  # Buyside Liquidity
        ssl = self.ltf_df['low'].tail(50).min()   # Sellside Liquidity

        signal = None

        # 1. BULLISH MODEL 1 SETUP (SSL Purge -> Engulf -> Long)
        if htf_bias == 'BULLISH':
            purged_ssl = purge_candle['low'] < ssl
            is_pin = CandlestickPatternAnalyzer.is_pin_bar(
                purge_candle['open'], purge_candle['high'], purge_candle['low'], purge_candle['close'], 'BULLISH'
            )
            is_engulfed = CandlestickPatternAnalyzer.is_engulfing(
                purge_candle['open'], purge_candle['close'], confirm_candle['open'], confirm_candle['close'], 'BULLISH'
            )
            
            # EMA Confluence Filter (Price above 8 or 21 EMA)
            ema_confluence = confirm_candle['close'] >= confirm_candle['ema_8'] or confirm_candle['close'] >= confirm_candle['ema_21']

            if (purged_ssl or is_pin) and is_engulfed and ema_confluence:
                # Determine entry level (Open body or 50% wick if long lower shadow)
                wick_length = min(purge_candle['open'], purge_candle['close']) - purge_candle['low']
                body_length = abs(purge_candle['close'] - purge_candle['open'])
                
                if wick_length > (body_length * 1.5):
                    entry_price = purge_candle['low'] + (wick_length * 0.5)  # 50% Wick Retest
                else:
                    entry_price = purge_candle['open']  # Open Body Entry

                stop_loss = purge_candle['low']
                risk_per_unit = entry_price - stop_loss

                if risk_per_unit > 0:
                    tp1 = entry_price + (risk_per_unit * 1.5)  # Partial 50% TP
                    tp2 = entry_price + (risk_per_unit * self.target_rr)  # Full Target
                    position_size = (self.capital * self.risk_per_trade) / risk_per_unit

                    signal = {
                        'id': f"BUY_{int(timestamp.timestamp())}",
                        'type': 'BUY',
                        'symbol': 'XAUUSD_EURUSD',
                        'timestamp': str(timestamp),
                        'entry_price': round(entry_price, 5),
                        'stop_loss': round(stop_loss, 5),
                        'tp1': round(tp1, 5),
                        'tp2': round(tp2, 5),
                        'position_size': round(position_size, 2),
                        'risk_amount': round(self.capital * self.risk_per_trade, 2),
                        'risk_reward': f"1:{self.target_rr}",
                        'status': 'PENDING',
                        'breakeven_active': False
                    }

        # 2. BEARISH MODEL 1 SETUP (BSL Purge -> Engulf -> Short)
        elif htf_bias == 'BEARISH':
            purged_bsl = purge_candle['high'] > bsl
            is_pin = CandlestickPatternAnalyzer.is_pin_bar(
                purge_candle['open'], purge_candle['high'], purge_candle['low'], purge_candle['close'], 'BEARISH'
            )
            is_engulfed = CandlestickPatternAnalyzer.is_engulfing(
                purge_candle['open'], purge_candle['close'], confirm_candle['open'], confirm_candle['close'], 'BEARISH'
            )
            
            ema_confluence = confirm_candle['close'] <= confirm_candle['ema_8'] or confirm_candle['close'] <= confirm_candle['ema_21']

            if (purged_bsl or is_pin) and is_engulfed and ema_confluence:
                wick_length = purge_candle['high'] - max(purge_candle['open'], purge_candle['close'])
                body_length = abs(purge_candle['close'] - purge_candle['open'])

                if wick_length > (body_length * 1.5):
                    entry_price = purge_candle['high'] - (wick_length * 0.5)
                else:
                    entry_price = purge_candle['open']

                stop_loss = purge_candle['high']
                risk_per_unit = stop_loss - entry_price

                if risk_per_unit > 0:
                    tp1 = entry_price - (risk_per_unit * 1.5)
                    tp2 = entry_price - (risk_per_unit * self.target_rr)
                    position_size = (self.capital * self.risk_per_trade) / risk_per_unit

                    signal = {
                        'id': f"SELL_{int(timestamp.timestamp())}",
                        'type': 'SELL',
                        'symbol': 'XAUUSD_EURUSD',
                        'timestamp': str(timestamp),
                        'entry_price': round(entry_price, 5),
                        'stop_loss': round(stop_loss, 5),
                        'tp1': round(tp1, 5),
                        'tp2': round(tp2, 5),
                        'position_size': round(position_size, 2),
                        'risk_amount': round(self.capital * self.risk_per_trade, 2),
                        'risk_reward': f"1:{self.target_rr}",
                        'status': 'PENDING',
                        'breakeven_active': False
                    }

        if signal:
            self._dispatch_signal_alert(signal)
            self.active_trades.append(signal)

        return signal

    def update_trade_lifecycle(self, current_price: float):
        """
        Manages live trade states: PENDING -> FILLED -> BREAKEVEN -> TP1 -> TP2 / STOP LOSS.
        """
        for trade in self.active_trades:
            if trade['status'] in ('CLOSED_WIN', 'CLOSED_LOSS'):
                continue

            # 1. Check Entry Fill for Pending Orders
            if trade['status'] == 'PENDING':
                if trade['type'] == 'BUY' and current_price <= trade['entry_price']:
                    trade['status'] = 'FILLED'
                    self._dispatch_lifecycle_alert(trade, "🟢 ENTRY ORDER FILLED", f"Buy Position Active at ${trade['entry_price']}")
                elif trade['type'] == 'SELL' and current_price >= trade['entry_price']:
                    trade['status'] = 'FILLED'
                    self._dispatch_lifecycle_alert(trade, "🔴 ENTRY ORDER FILLED", f"Sell Position Active at ${trade['entry_price']}")

            # 2. Lifecycle Management for Active Trades
            elif trade['status'] in ('FILLED', 'TP1_HIT'):
                if trade['type'] == 'BUY':
                    # Stop Loss Hit
                    if current_price <= trade['stop_loss']:
                        trade['status'] = 'CLOSED_LOSS'
                        self._dispatch_lifecycle_alert(trade, "🛑 STOP LOSS HIT", f"Trade closed at SL (${trade['stop_loss']})")
                    # TP1 Hit
                    elif current_price >= trade['tp1'] and trade['status'] != 'TP1_HIT':
                        trade['status'] = 'TP1_HIT'
                        trade['stop_loss'] = trade['entry_price']  # Move to Breakeven
                        trade['breakeven_active'] = True
                        self._dispatch_lifecycle_alert(trade, "🎯 TP1 HIT (+1.5R)", f"Secured 50% profits. Stop Loss moved to BREAKEVEN (${trade['entry_price']})")
                    # TP2 Hit
                    elif current_price >= trade['tp2']:
                        trade['status'] = 'CLOSED_WIN'
                        self._dispatch_lifecycle_alert(trade, "🎉 FULL TAKE PROFIT (TP2) HIT", f"Trade closed at Full Target (${trade['tp2']}) | +{trade['risk_reward']}")

                elif trade['type'] == 'SELL':
                    # Stop Loss Hit
                    if current_price >= trade['stop_loss']:
                        trade['status'] = 'CLOSED_LOSS'
                        self._dispatch_lifecycle_alert(trade, "🛑 STOP LOSS HIT", f"Trade closed at SL (${trade['stop_loss']})")
                    # TP1 Hit
                    elif current_price <= trade['tp1'] and trade['status'] != 'TP1_HIT':
                        trade['status'] = 'TP1_HIT'
                        trade['stop_loss'] = trade['entry_price']  # Move to Breakeven
                        trade['breakeven_active'] = True
                        self._dispatch_lifecycle_alert(trade, "🎯 TP1 HIT (+1.5R)", f"Secured 50% profits. Stop Loss moved to BREAKEVEN (${trade['entry_price']})")
                    # TP2 Hit
                    elif current_price <= trade['tp2']:
                        trade['status'] = 'CLOSED_WIN'
                        self._dispatch_lifecycle_alert(trade, "🎉 FULL TAKE PROFIT (TP2) HIT", f"Trade closed at Full Target (${trade['tp2']}) | +{trade['risk_reward']}")

    def _dispatch_signal_alert(self, signal: Dict):
        color = 3066993 if signal['type'] == 'BUY' else 15158332
        title = f"🚨 NEW TSQ MODEL 1 {signal['type']} SIGNAL DETECTED"
        msg = (
            f"**Symbol**: {signal['symbol']}\n"
            f"**Timestamp**: {signal['timestamp']}\n"
            f"**Direction**: {signal['type']}\n\n"
            f"📍 **Entry Price**: ${signal['entry_price']}\n"
            f"🛡️ **Stop Loss**: ${signal['stop_loss']}\n"
            f"🎯 **Target TP1 (50% Profit)**: ${signal['tp1']}\n"
            f"🎯 **Target TP2 (Full Target)**: ${signal['tp2']}\n\n"
            f"💰 **Risk Amount (1%)**: ${signal['risk_amount']}\n"
            f"⚖️ **Risk-Reward Ratio**: {signal['risk_reward']}\n"
            f"📦 **Suggested Size**: {signal['position_size']} units"
        )
        self.notifier.send_discord_alert(title, msg, color=color)
        self.notifier.send_telegram_alert(f"{title}\n\n{msg}")

    def _dispatch_lifecycle_alert(self, trade: Dict, title: str, details: str):
        msg = (
            f"**Trade ID**: `{trade['id']}`\n"
            f"**Symbol**: {trade['symbol']} ({trade['type']})\n"
            f"**Update**: {details}\n"
            f"**Current SL**: ${trade['stop_loss']}"
        )
        self.notifier.send_discord_alert(f"UPDATE: {title}", msg, color=3447003)
        self.notifier.send_telegram_alert(f"UPDATE: {title}\n\n{msg}")


if __name__ == "__main__":
    print("="*60)
    print("TSQ MODEL 1 MASTER EXECUTION ENGINE (VERSION 3.0)")
    print("Incorporates CRT, TSQ, Candlestick Bible & Godfather Elite Rules")
    print("="*60)
    
    # Generate Sample HTF (1H) and LTF (15M) Data for Verification
    dates_htf = pd.date_range(end=datetime.now(), periods=50, freq='1h')
    dates_ltf = pd.date_range(end=datetime.now(), periods=200, freq='15min')

    df_htf_sample = pd.DataFrame({
        'timestamp': dates_htf,
        'open': np.linspace(1.0800, 1.0850, 50),
        'high': np.linspace(1.0820, 1.0870, 50),
        'low': np.linspace(1.0790, 1.0840, 50),
        'close': np.linspace(1.0815, 1.0865, 50)
    })

    df_ltf_sample = pd.DataFrame({
        'timestamp': dates_ltf,
        'open': np.linspace(1.0840, 1.0860, 200),
        'high': np.linspace(1.0845, 1.0865, 200),
        'low': np.linspace(1.0835, 1.0855, 200),
        'close': np.linspace(1.0842, 1.0862, 200)
    })

    # Test Engine Initialization
    engine = TSQExecutionEngine(df_htf_sample, df_ltf_sample)
    print("✅ Execution Engine Initialized Successfully!")
