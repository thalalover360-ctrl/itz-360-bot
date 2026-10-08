import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import database as db

async def dice_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.get_or_create_user(user.id, user.first_name)

    keyboard = [
        [
            InlineKeyboardButton("⬇️ Under 7 (+200)", callback_data="dice_under"),
            InlineKeyboardButton("🎯 Exact 7 (+500)", callback_data="dice_exact"),
            InlineKeyboardButton("⬆️ Over 7 (+200)", callback_data="dice_over")
        ]
    ]

    msg = (
        f"🎲 *Dice 7 Challenge!*\n\n"
        f"{user.first_name}, do dice roll honge (Total 2 se 12).\n"
        "Apna guess chuno:\n"
        "• Under 7: *+200 pts*\n"
        "• Exact 7: *+500 pts*\n"
        "• Over 7: *+200 pts*\n"
        "• Galat hone par: *-100 pts*"
    )
    await update.message.reply_text(
        msg,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def dice_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = query.from_user
    db.get_or_create_user(user.id, user.first_name)

    guess = query.data.split("_")[1]
    d1 = random.randint(1, 6)
    d2 = random.randint(1, 6)
    total = d1 + d2

    dice_emojis = {1: "⚀", 2: "⚁", 3: "⚂", 4: "⚃", 5: "⚄", 6: "⚅"}

    if total < 7:
        outcome = "under"
        tag = "Under 7"
    elif total == 7:
        outcome = "exact"
        tag = "Exact 7"
    else:
        outcome = "over"
        tag = "Over 7"

    roll_display = f"{dice_emojis[d1]} ({d1}) + {dice_emojis[d2]} ({d2}) = *{total}* ({tag})"

    if guess == outcome:
        pts = 500 if outcome == "exact" else 200
        new_score = db.update_score(user.id, pts)
        msg = (
            f"🎯 *Sahi Guess! Shandaar!* 🎲\n\n"
            f"Roll: {roll_display}\n"
            f"Player: *{user.first_name}*\n"
            f"Points: *+{pts} pts*\n"
            f"Total Score: *{new_score} pts*"
        )
    else:
        new_score = db.update_score(user.id, -100)
        msg = (
            f"❌ *Kismat Ne Saath Nahi Diya!* 🎲\n\n"
            f"Roll: {roll_display}\n"
            f"Player: *{user.first_name}*\n"
            f"Points: *-100 pts*\n"
            f"Total Score: *{new_score} pts*"
        )

    await query.edit_message_text(msg, parse_mode="Markdown")
