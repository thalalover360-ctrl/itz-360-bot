import uuid
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import database as db

async def chess_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        if not user:
            return
            
        db.get_or_create_user(user.id, user.first_name)

        # Unique Match ID
        room_id = uuid.uuid4().hex[:8]
        game_url = f"https://lichess.org/{room_id}"
        share_url = f"https://t.me/share/url?url={game_url}&text=Aaja%20Chess%20khelte%20hain%201v1!"

        # Groups me direct url buttons 100% reliable chalte hain
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("⚔️ Join / Play Chess ♟️", url=game_url)
            ],
            [
                InlineKeyboardButton("📤 Invite Friend", url=share_url)
            ]
        ])

        msg = (
            f"♟️ *CHESS ARENA: 1v1 MATCH* ♟️\n\n"
            f"👤 *Host:* {user.first_name}\n"
            f"⏱️ *Mode:* Live Rapid PvP\n\n"
            f"🔗 *Room Link:* [Tap to Play]({game_url})\n\n"
            "👉 Dono players button par tap karke seedha khel sakte hain!"
        )

        await update.message.reply_text(
            msg,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    except Exception as e:
        print(f"Error in chess_cmd: {e}")
        # Agar group markdown fail kare toh normal text bhejega
        await update.message.reply_text(f"Chess match link: https://lichess.org/{uuid.uuid4().hex[:8]}")
        
