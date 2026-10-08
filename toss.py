import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import database as db

async def toss_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.get_or_create_user(user.id, user.first_name)
    
    keyboard = [
        [
            InlineKeyboardButton("🪙 Heads", callback_data="toss_heads"),
            InlineKeyboardButton("🪙 Tails", callback_data="toss_tails")
        ]
    ]
    await update.message.reply_text(
        f"🪙 *Coin Toss Game*\n\n{user.first_name}, apna guess chuno:\n"
        "Jeetne par: *+200 pts*\nHaarne par: *-100 pts*",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def toss_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    db.get_or_create_user(user.id, user.first_name)
    
    user_choice = query.data.split("_")[1]
    bot_outcome = random.choice(["heads", "tails"])
    
    if user_choice == bot_outcome:
        new_score = db.update_score(user.id, 200)
        msg = (
            f"🎉 *Jeet Gaye!* 🪙\n\n"
            f"Outcome: *{bot_outcome.capitalize()}*\n"
            f"Player: *{user.first_name}*\n"
            f"Points: *+200*\n"
            f"Total Score: *{new_score} pts*"
        )
    else:
        new_score = db.update_score(user.id, -100)
        msg = (
            f"😢 *Haar Gaye!* 🪙\n\n"
            f"Outcome: *{bot_outcome.capitalize()}*\n"
            f"Player: *{user.first_name}*\n"
            f"Points: *-100*\n"
            f"Total Score: *{new_score} pts*"
        )
        
    await query.edit_message_text(msg, parse_mode="Markdown")
  
