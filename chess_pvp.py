import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ContextTypes
import database as db

async def chess_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user
    db.get_or_create_user(user.id, user.first_name)

    # Lichess open challenge create API
    try:
        res = requests.post("https://lichess.org/api/challenge/open", json={
            "clock.limit": 600,       # 10 minute match
            "clock.increment": 5,     # 5 sec increment
            "rated": False
        }, timeout=8)
        
        if res.status_code == 200:
            data = res.json()
            game_url = data.get("url")  # e.g., https://lichess.org/xxxxxx
            
            # Telegram Web App button
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "⚔️ Open Chess Board (PvP)", 
                        web_app=WebAppInfo(url=game_url)
                    )
                ]
            ])
            
            await update.message.reply_text(
                f"♟️ *CHESS ARENA: 1v1 MATCH CREATED!* ♟️\n\n"
                f"👤 *Host:* {user.first_name}\n"
                f"⏱️ *Time:* 10 Min Rapid\n\n"
                "👉 Dono players neeche diye gaye button par click karein!\n"
                "Telegram ke andar hi live visual board khulega.",
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text("⚠️ Match link generate nahi ho paya, dobara koshish karein.")
    except Exception as e:
        await update.message.reply_text("⚠️ Match load karne me samasya aayi. Dobara try karein.")
      
