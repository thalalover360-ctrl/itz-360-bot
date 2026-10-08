import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import database as db

async def chess_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user:
        return
        
    db.get_or_create_user(user.id, user.first_name)

    # Lichess open challenge API configuration
    api_url = "https://lichess.org/api/challenge/open"
    headers = {
        "User-Agent": "itz360-Bot/1.0 (Telegram)",
        "Accept": "application/json"
    }
    payload = {
        "clock.limit": "600",       # 10 minutes (seconds me)
        "clock.increment": "5",     # 5 sec increment
        "rated": "false"
    }

    try:
        # Lichess form data accept karta hai (data=payload)
        response = requests.post(api_url, data=payload, headers=headers, timeout=12)
        
        if response.status_code == 200:
            res_data = response.json()
            # Challenge URL nikalna
            game_url = res_data.get("url") or res_data.get("challenge", {}).get("url")
            
            if not game_url:
                await update.message.reply_text("⚠️ Match URL nahi mil saki, dobara try karein.")
                return

            share_url = f"https://t.me/share/url?url={game_url}&text=Aaja%20Chess%20khelte%20hain%201v1!"

            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("⚔️ Join / Play Chess ♟️", url=game_url)
                ],
                [
                    InlineKeyboardButton("📤 Invite Friend", url=share_url)
                ]
            ])

            msg = (
                f"♟️ *CHESS ARENA: 1v1 MATCH CREATED!* ♟️\n\n"
                f"👤 *Host:* {user.first_name}\n"
                f"⏱️ *Time:* 10 Min + 5s Rapid\n\n"
                f"🔗 *Room Link:* [Tap to Play]({game_url})\n\n"
                "👉 Dono players button par tap karke match join karein!"
            )

            await update.message.reply_text(
                msg,
                reply_markup=keyboard,
                parse_mode="Markdown",
                disable_web_page_preview=False
            )
        else:
            await update.message.reply_text("⚠️ Lichess server busy hai. 10 second baad dobara `/chess` bhejein.")
    except Exception as e:
        print(f"Error creating Lichess game: {e}")
        await update.message.reply_text("⚠️ Match load karne me samasya aayi. Ek baar aur try karein.")
        
