import uuid
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ContextTypes
import database as db

async def chess_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.get_or_create_user(user.id, user.first_name)

    # Unique Match Room ID
    room_id = uuid.uuid4().hex[:10]
    
    # Direct fast game URL (zero network failure)
    game_url = f"https://lichess.org/{room_id}"
    share_url = f"https://t.me/share/url?url={game_url}&text=Aaja%20Chess%20khelte%20hain%201v1!"

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⚔️ Play Chess (Web Board)", web_app=WebAppInfo(url=game_url))
        ],
        [
            InlineKeyboardButton("📤 Invite / Share Link", url=share_url)
        ]
    ])

    msg = (
        f"♟️ *CHESS ARENA: 1v1 MATCH CREATED!* ♟️\n\n"
        f"👤 *Host:* {user.first_name}\n"
        f"⏱️ *Mode:* Live 1v1 PvP\n\n"
        f"🔗 *Direct Join:* [Click Here to Play]({game_url})\n\n"
        "👉 Group members neeche diye gaye button par tap karke seedha khel sakte hain!"
    )

    await update.message.reply_text(
        msg,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
