import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ContextTypes
import database as db

async def chess_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.get_or_create_user(user.id, user.first_name)

    # Headers taaki Lichess request ko bot samajh kar block na kare
    headers = {
        "User-Agent": "itz360TelegramBot/1.0 (contact: telegram @itz360_bot)",
        "Accept": "application/json"
    }

    payload = {
        "clock.limit": 600,       # 10 minutes
        "clock.increment": 5,     # 5 sec per move
        "rated": False
    }

    try:
        res = requests.post(
            "https://lichess.org/api/challenge/open",
            json=payload,
            headers=headers,
            timeout=15  # Render lag handle karne ke liye 15s timeout
        )
        
        if res.status_code == 200:
            data = res.json()
            game_url = data.get("url")
            
            share_url = f"https://t.me/share/url?url={game_url}&text=Aaja%20Chess%20khelte%20hain%201v1!"

            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("⚔️ Play Chess (Board)", web_app=WebAppInfo(url=game_url))
                ],
                [
                    InlineKeyboardButton("📤 Invite / Share Link", url=share_url)
                ]
            ])
            
            msg = (
                f"♟️ *CHESS ARENA: 1v1 MATCH CREATED!* ♟️\n\n"
                f"👤 *Host:* {user.first_name}\n"
                f"⏱️ *Time:* 10 Min Rapid\n\n"
                f"🔗 *Direct Link:* [Click Here to Join]({game_url})\n\n"
                "👉 *Group me:* Neeche 'Play Chess' button dabayein.\n"
                "👉 *Dost ko bhejna hai:* 'Invite / Share' dabayein ya link copy karke bhejein."
            )

            await update.message.reply_text(
                msg,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(f"⚠️ Lichess busy hai (Code: {res.status_code}). Kuch second baad try karein.")
    except requests.exceptions.Timeout:
        await update.message.reply_text("⏱️ Connection slow tha, dobara `/chess` bhejein.")
    except Exception as e:
        await update.message.reply_text("⚠️ Match load karne me samasya aayi. Dobara try karein.")
        
