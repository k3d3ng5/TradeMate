import os
import sys
import time
import requests
from typing import Dict, List, Any

# =====================================================================
# TRADEMATE 3-TIER INTERACTIVE TELEGRAM LEARNING BOT ENGINE
# =====================================================================

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN_HERE")

USER_PROGRESS: Dict[int, Dict[str, Any]] = {}

CURRICULUM = {
    "tier1": {
        "title": "🟢 Tier 1: Beginner - Candlestick Foundations",
        "description": "Master candlestick anatomy, core price action patterns, and level identification.",
        "modules": [
            {
                "id": "t1_m1",
                "title": "Module 1.1: Anatomy of a Candlestick",
                "content": (
                    "<b>📚 Module 1.1: Anatomy of a Candlestick</b>\n\n"
                    "Every candle on your chart records four core price points over a fixed timeframe:\n"
                    "• <b>Open</b>: Initial price when the candle opens.\n"
                    "• <b>High</b>: Peak price reached during the period.\n"
                    "• <b>Low</b>: Lowest price reached during the period.\n"
                    "• <b>Close</b>: Final price when the candle closes.\n\n"
                    "<b>Key Concepts:</b>\n"
                    "1. <b>Real Body</b>: Distance between Open and Close.\n"
                    "2. <b>Shadows / Wicks</b>: Lines extending above and below the body. Long wicks show price rejection by buyers or sellers."
                ),
                "quiz": {
                    "question": "What does a long lower shadow (wick) on a candle signify?",
                    "options": [
                        "Selling pressure holding price at the lows",
                        "Buyers stepping in and rejecting lower price levels",
                        "Market indecision with equal buyer and seller force",
                        "Imminent market consolidation"
                    ],
                    "correct": 1,
                    "explanation": "A long lower wick shows price was pushed down, but aggressive buying pressure stepped in to drive price back up, rejecting the low."
                }
            },
            {
                "id": "t1_m2",
                "title": "Module 1.2: Core Price Action Patterns",
                "content": (
                    "<b>📚 Module 1.2: Core Price Action Patterns</b>\n\n"
                    "Key reversal and continuation patterns:\n\n"
                    "• <b>Pin Bar (Hammer / Shooting Star)</b>: Small real body with a long tail (at least 2x body size).\n"
                    "• <b>Engulfing Bar</b>: A two-candle pattern where the second candle body completely covers the body of the preceding candle.\n"
                    "• <b>Inside Bar</b>: A small candle completely contained within the mother bar's range."
                ),
                "quiz": {
                    "question": "What confirms a valid Engulfing pattern?",
                    "options": [
                        "The wick exceeds the previous candle high",
                        "The second candle's body completely covers the first candle's body",
                        "The candle closes as a Doji",
                        "Volume drops by 50%"
                    ],
                    "correct": 1,
                    "explanation": "An engulfing pattern requires the real body of the second candle to fully cover the real body of the prior candle."
                }
            },
            {
                "id": "t1_m3",
                "title": "Module 1.3: Market Regimes & Levels",
                "content": (
                    "<b>📚 Module 1.3: Market Regimes & Levels</b>\n\n"
                    "Classify market environments before looking for setups:\n\n"
                    "1. <b>Trending Market</b>: Higher Highs & Higher Lows or Lower Highs & Lower Lows.\n"
                    "2. <b>Ranging Market</b>: Price oscillates between defined Support floor and Resistance ceiling.\n"
                    "3. <b>Choppy Market</b>: Erratic overlapping wicks. <b>Rule: Do NOT trade. Preserve capital.</b>"
                ),
                "quiz": {
                    "question": "How should a trader handle a Choppy / Erratic market environment?",
                    "options": [
                        "Increase leverage to capture short scalps",
                        "Trade breakouts at every minor high",
                        "Stay out of the market and preserve capital",
                        "Use counter-trend grid orders"
                    ],
                    "correct": 2,
                    "explanation": "Choppy markets lack institutional momentum. The professional rule is to stay out and preserve capital."
                }
            }
        ]
    },
    "tier2": {
        "title": "🟡 Tier 2: Intermediate - Market Mechanics & Risk Engine",
        "description": "Understand Pips, Lot Sizing, Leverage, Used vs Usable Margin, and strict Money Management.",
        "modules": [
            {
                "id": "t2_m1",
                "title": "Module 2.1: Pips, Lots & Position Sizing",
                "content": (
                    "<b>📚 Module 2.1: Pips, Lots & Position Sizing</b>\n\n"
                    "• <b>Pip</b>: Percentage in Point, usually the 4th decimal place (0.0001) in Forex pairs.\n"
                    "• <b>Lot Sizes</b>: Standard Lot (100k), Mini Lot (10k), Micro Lot (1k).\n\n"
                    "<b>Position Size Formula:</b>\n"
                    "<code>Position Lots = (Account Capital x Risk %) / (Stop Loss Pips x Pip Value)</code>"
                ),
                "quiz": {
                    "question": "If risking $100 with a 20-pip stop loss on EUR/USD ($1/pip for mini lot), how many mini lots do you trade?",
                    "options": [
                        "1 Mini Lot",
                        "5 Mini Lots (0.50 lot)",
                        "10 Mini Lots",
                        "20 Mini Lots"
                    ],
                    "correct": 1,
                    "explanation": "20 pips x $1/pip per mini lot = $20 risk per mini lot. $100 risk / $20 = 5 mini lots (0.50 lot)."
                }
            },
            {
                "id": "t2_m2",
                "title": "Module 2.2: Leverage, Margin & Survival",
                "content": (
                    "<b>📚 Module 2.2: Leverage, Margin & Survival</b>\n\n"
                    "• <b>Used Margin</b>: Collateral held by your broker.\n"
                    "• <b>Usable Margin</b>: Equity minus Used Margin.\n"
                    "• <b>Margin Call</b>: Triggers when Equity drops below Used Margin; open trades are liquidated."
                ),
                "quiz": {
                    "question": "What triggers an account Margin Call?",
                    "options": [
                        "When account balance increases by 50%",
                        "When account Equity drops to or below Used Margin",
                        "When holding a position over the weekend",
                        "When taking more than 3 trades in a day"
                    ],
                    "correct": 1,
                    "explanation": "A Margin Call occurs when floating losses reduce Equity down to or below the required Used Margin."
                }
            }
        ]
    },
    "tier3": {
        "title": "🔴 Tier 3: Advanced - Candle Range Theory & TSQ Execution",
        "description": "Master Candle Range Theory, Session Kill Zones, Model 1 CISD, and the 5 TSQ Delivery Phases.",
        "modules": [
            {
                "id": "t3_m1",
                "title": "Module 3.1: CRT & Session Kill Zones",
                "content": (
                    "<b>📚 Module 3.1: CRT & Session Kill Zones</b>\n\n"
                    "• <b>CRT Foundation</b>: Every candle represents a fixed time-based range.\n"
                    "• <b>Session Kill Zones</b>: London Kill Zone (07:00-11:00 WAT) & New York Kill Zone (13:00-17:00 WAT).\n"
                    "• <b>Opening Price Rule</b>: Buy below the open price or sell above the open price."
                ),
                "quiz": {
                    "question": "According to the Opening Price Rule, where should a trader look for a high-probability Buy setup?",
                    "options": [
                        "Above the active opening price",
                        "Below the active opening price (Discount)",
                        "Only at the daily closing price",
                        "Outside session kill zones"
                    ],
                    "correct": 1,
                    "explanation": "Buying below the opening price ensures an entry at a discount during manipulation."
                }
            },
            {
                "id": "t3_m2",
                "title": "Module 3.2: TSQ Phases & Model 1 Execution",
                "content": (
                    "<b>📚 Module 3.2: TSQ Delivery Phases & Model 1</b>\n\n"
                    "<b>The 5 TSQ Delivery Phases:</b>\n"
                    "1. <b>Turtle Soup</b>: Liquidity sweep beyond a reference High/Low.\n"
                    "2. <b>Model 1 (CISD)</b>: M15 candle body closes back inside the purge candle.\n"
                    "3. <b>Breaker Block</b>: Structural shift retest level.\n"
                    "4. <b>Optimal Trade Entry (OTE)</b>: 60%-75% Fibonacci pullback.\n"
                    "5. <b>Kiss of Death</b>: Final false sweep before reaching target."
                ),
                "quiz": {
                    "question": "What is the primary purpose of Model 1 in the TSQ sequence?",
                    "options": [
                        "To predict where news will release",
                        "To provide structural confirmation (CISD) after a Turtle Soup sweep",
                        "To guarantee zero drawdown on every entry",
                        "To replace the need for stop loss orders"
                    ],
                    "correct": 1,
                    "explanation": "Turtle Soup is the initial trap; Model 1 provides mechanical confirmation via a candle close back inside the range."
                }
            }
        ]
    }
}


def send_telegram_request(method: str, payload: dict) -> dict:
    """Dispatches a request to the Telegram API."""
    domain = "api." + "telegram" + ".org"
    url = f"https://{domain}/bot{TELEGRAM_BOT_TOKEN}/{method}"
    try:
        res = requests.post(url, json=payload, timeout=10)
        return res.json()
    except Exception as e:
        print(f"Telegram API Error ({method}): {e}")
        return {}


def get_user_progress(user_id: int) -> dict:
    if user_id not in USER_PROGRESS:
        USER_PROGRESS[user_id] = {
            "completed_modules": [],
            "current_tier": "tier1",
            "score": 0
        }
    return USER_PROGRESS[user_id]


def render_main_menu(user_id: int, chat_id: int, message_id: int = None):
    prog = get_user_progress(user_id)
    completed = prog["completed_modules"]
    
    t1_done = sum(1 for m in CURRICULUM["tier1"]["modules"] if m["id"] in completed)
    t2_done = sum(1 for m in CURRICULUM["tier2"]["modules"] if m["id"] in completed)
    t3_done = sum(1 for m in CURRICULUM["tier3"]["modules"] if m["id"] in completed)
    
    t1_total = len(CURRICULUM["tier1"]["modules"])
    t2_total = len(CURRICULUM["tier2"]["modules"])
    t3_total = len(CURRICULUM["tier3"]["modules"])
    
    t1_unlocked = True
    t2_unlocked = t1_done == t1_total
    t3_unlocked = t2_done == t2_total
    
    text = (
        "🎓 <b>TradeMate Trading Academy - Interactive Curriculum</b>\n\n"
        "Welcome to your structured 3-tier trading pathway:\n\n"
        f"🟢 <b>Tier 1: Beginner</b> [{t1_done}/{t1_total} Done] {'✅ Unlocked' if t1_unlocked else '🔒 Locked'}\n"
        f"🟡 <b>Tier 2: Intermediate</b> [{t2_done}/{t2_total} Done] {'✅ Unlocked' if t2_unlocked else '🔒 Locked'}\n"
        f"🔴 <b>Tier 3: Advanced (CRT/TSQ)</b> [{t3_done}/{t3_total} Done] {'✅ Unlocked' if t3_unlocked else '🔒 Locked'}\n\n"
        "Select an unlocked Tier below to start learning:"
    )
    
    keyboard = []
    if t1_unlocked:
        keyboard.append([{"text": "🟢 Open Tier 1: Beginner", "callback_data": "nav_tier1"}])
    if t2_unlocked:
        keyboard.append([{"text": "🟡 Open Tier 2: Intermediate", "callback_data": "nav_tier2"}])
    else:
        keyboard.append([{"text": "🔒 Tier 2 (Complete Tier 1 to Unlock)", "callback_data": "locked_t2"}])
        
    if t3_unlocked:
        keyboard.append([{"text": "🔴 Open Tier 3: Advanced", "callback_data": "nav_tier3"}])
    else:
        keyboard.append([{"text": "🔒 Tier 3 (Complete Tier 2 to Unlock)", "callback_data": "locked_t3"}])
        
    keyboard.append([{"text": "📊 My Progress & Score", "callback_data": "view_score"}])
    
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "reply_markup": {"inline_keyboard": keyboard}
    }
    
    if message_id:
        payload["message_id"] = message_id
        send_telegram_request("editMessageText", payload)
    else:
        send_telegram_request("sendMessage", payload)


def handle_callback_query(callback: dict):
    callback_id = callback.get("id")
    user_id = callback["from"]["id"]
    chat_id = callback["message"]["chat"]["id"]
    message_id = callback["message"]["message_id"]
    data = callback.get("data", "")
    
    prog = get_user_progress(user_id)
    send_telegram_request("answerCallbackQuery", {"callback_query_id": callback_id})
    
    if data == "main_menu":
        render_main_menu(user_id, chat_id, message_id)
        return
        
    if data == "view_score":
        text = (
            f"📊 <b>Your Academy Profile</b>\n\n"
            f"👤 <b>Student ID</b>: <code>{user_id}</code>\n"
            f"⭐ <b>Experience Points (XP)</b>: <b>{prog['score']} XP</b>\n"
            f"📚 <b>Completed Modules</b>: <b>{len(prog['completed_modules'])} / 7</b>\n\n"
            f"Keep taking quizzes to earn XP and unlock Tier 2 & Tier 3!"
        )
        keyboard = [[{"text": "🏠 Main Menu", "callback_data": "main_menu"}]]
        send_telegram_request("editMessageText", {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
            "parse_mode": "HTML",
            "reply_markup": {"inline_keyboard": keyboard}
        })
        return

    if data.startswith("nav_tier"):
        tier_key = data.replace("nav_", "")
        tier = CURRICULUM[tier_key]
        
        text = f"<b>{tier['title']}</b>\n\n{tier['description']}\n\n<b>Select a Module:</b>"
        keyboard = []
        
        for mod in tier["modules"]:
            is_done = mod["id"] in prog["completed_modules"]
            status = "✅" if is_done else "📖"
            keyboard.append([{"text": f"{status} {mod['title']}", "callback_data": f"open_mod_{mod['id']}"}])
            
        keyboard.append([{"text": "⬅️ Back to Main Menu", "callback_data": "main_menu"}])
        
        send_telegram_request("editMessageText", {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
            "parse_mode": "HTML",
            "reply_markup": {"inline_keyboard": keyboard}
        })
        return

    if data.startswith("open_mod_"):
        mod_id = data.replace("open_mod_", "")
        target_mod = None
        for tier in CURRICULUM.values():
            for m in tier["modules"]:
                if m["id"] == mod_id:
                    target_mod = m
                    break
                    
        if not target_mod:
            return
            
        text = target_mod["content"]
        is_done = mod_id in prog["completed_modules"]
        
        keyboard = []
        if not is_done:
            keyboard.append([{"text": "📝 Take Module Quiz", "callback_data": f"quiz_{mod_id}"}])
        else:
            keyboard.append([{"text": "✅ Quiz Passed (Retake Quiz)", "callback_data": f"quiz_{mod_id}"}])
            
        keyboard.append([{"text": "⬅️ Back to Main Menu", "callback_data": "main_menu"}])
        
        send_telegram_request("editMessageText", {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
            "parse_mode": "HTML",
            "reply_markup": {"inline_keyboard": keyboard}
        })
        return

    if data.startswith("quiz_"):
        mod_id = data.replace("quiz_", "")
        target_mod = None
        for tier in CURRICULUM.values():
            for m in tier["modules"]:
                if m["id"] == mod_id:
                    target_mod = m
                    break
        if not target_mod:
            return
            
        quiz = target_mod["quiz"]
        text = f"<b>📝 Knowledge Check: {target_mod['title']}</b>\n\n<b>Question:</b> {quiz['question']}"
        keyboard = []
        
        for idx, opt in enumerate(quiz["options"]):
            keyboard.append([{"text": f"{chr(65+idx)}. {opt}", "callback_data": f"ans_{mod_id}_{idx}"}])
            
        keyboard.append([{"text": "⬅️ Cancel", "callback_data": f"open_mod_{mod_id}"}])
        
        send_telegram_request("editMessageText", {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
            "parse_mode": "HTML",
            "reply_markup": {"inline_keyboard": keyboard}
        })
        return

    if data.startswith("ans_"):
        parts = data.split("_")
        mod_id = parts[1]
        user_ans = int(parts[2])
        
        target_mod = None
        for tier in CURRICULUM.values():
            for m in tier["modules"]:
                if m["id"] == mod_id:
                    target_mod = m
                    break
        if not target_mod:
            return
            
        quiz = target_mod["quiz"]
        if user_ans == quiz["correct"]:
            if mod_id not in prog["completed_modules"]:
                prog["completed_modules"].append(mod_id)
                prog["score"] += 100
                
            text = (
                f"🎉 <b>CORRECT! Excellent Work!</b>\n\n"
                f"<b>Explanation:</b> {quiz['explanation']}\n\n"
                f"🏆 <b>+100 XP Earned!</b>"
            )
        else:
            text = (
                f"❌ <b>Incorrect Option.</b>\n\n"
                f"Review the lesson text and try again!\n\n"
                f"<b>Hint:</b> {quiz['explanation']}"
            )
            
        keyboard = [
            [{"text": "📖 Return to Module", "callback_data": f"open_mod_{mod_id}"}],
            [{"text": "🏠 Main Menu", "callback_data": "main_menu"}]
        ]
        send_telegram_request("editMessageText", {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
            "parse_mode": "HTML",
            "reply_markup": {"inline_keyboard": keyboard}
        })
        return


if __name__ == "__main__":
    print("="*60)
    print("TRADEMATE 3-TIER INTERACTIVE LEARNING ENGINE V1.0")
    print("Self-Contained Public Educational Curriculum")
    print("="*60)
    print("Engine active. Script ready for local testing or cloud deployment.")
