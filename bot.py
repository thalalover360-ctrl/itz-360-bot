import os
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

# Token Render se automatically aayega
TOKEN = os.getenv("BOT_TOKEN")

# Points track karne ke liye {user_id: score}
user_scores = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_scores:
        user_scores[user_id] = 0

    welcome_msg = (
        "🤖 *Welcome to itz-360 Coin Toss Game!*\n\n"
        "Rules:\n"
        "✅ Sahi Guess: *+200 Points*\n"
        "❌ Galat Guess: *-100 Points*\n\n"
        "Sikka uchhalne ke liye /toss bhejein aur score check karne ke liye /score."
    )
    await update.message.reply_text(welcome_msg, parse_mode="Markdown")

async def score(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    current_score = user_scores.get(user_id, 0)
    await update.message.reply_text(f"🏆 Aapka Current Score: *{current_score} Points*", parse_mode="Markdown")

async def toss(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("🪙 Heads", callback_data="heads"),
            InlineKeyboardButton("🪙 Tails", callback_data="tails")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("itz-360 Toss: Apna guess chunein!", reply_markup=reply_markup)

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    if user_id not in user_scores:
        user_scores[user_id] = 0

    user_guess = query.data
    toss_result = random.choice(["heads", "tails"])

    if user_guess == toss_result:
        user_scores[user_id] += 200
        result_text = (
            f"🎉 *Jeet Gaye!*\n\n"
            f"Coin gira: *{toss_result.capitalize()}*\n"
            f"Aapka guess: *{user_guess.capitalize()}*\n"
            f"Points: *+200*\n"
            f"Kul Score: *{user_scores[user_id]} Points*"
        )
    else:
        user_scores[user_id] -= 100
        result_text = (
            f"😢 *Galat Guess!*\n\n"
            f"Coin gira: *{toss_result.capitalize()}*\n"
            f"Aapka guess: *{user_guess.capitalize()}*\n"
            f"Points: *-100*\n"
            f"Kul Score: *{user_scores[user_id]} Points*"
        )

    keyboard = [
        [
            InlineKeyboardButton("Dobara Toss Karein 🔄", callback_data="play_again")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text=result_text, reply_markup=reply_markup, parse_mode="Markdown")

async def play_again(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard = [
        [
            InlineKeyboardButton("🪙 Heads", callback_data="heads"),
            InlineKeyboardButton("🪙 Tails", callback_data="tails")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("itz-360 Toss: Apna guess chunein!", reply_markup=reply_markup)

def main():
    if not TOKEN:
        raise ValueError("BOT_TOKEN variable nahi mila!")

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("score", score))
    app.add_handler(CommandHandler("toss", toss))
    
    app.add_handler(CallbackQueryHandler(play_again, pattern="^play_again$"))
    app.add_handler(CallbackQueryHandler(button_click, pattern="^(heads|tails)$"))

    print("itz-360 live ho chuka hai...")
    app.run_polling()

if __name__ == "__main__":
    main()
  
