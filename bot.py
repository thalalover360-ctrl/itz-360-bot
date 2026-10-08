import os
import threading
from flask import Flask
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes
)

# Local imports (ye files hum aage step-by-step banayenge)
import database as db
import toss
import guess
import dice
import scramble
import tictactoe

# --- Render ke liye Dummy Web Server ---
web_app = Flask(__name__)

@web_app.route("/")
def home():
    return "itz-360 Bot is Running 24/7!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host="0.0.0.0", port=port)

# --- Core Commands ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.get_or_create_user(user.id, user.first_name)
    
    welcome_text = (
        f"🎮 *itz-360 Arcade me Swagat hai, {user.first_name}!* 🎮\n\n"
        "Yahan hain aapke 5 Zabardast Games:\n"
        "1. 🪙 `/toss` - Coin Toss (+200 / -100)\n"
        "2. 🎯 `/guess` - Guess The Number (1 to 500, 10 Moves)\n"
        "3. ❌ `/ttt` - Tic-Tac-Toe (Zero Kaata)\n"
        "4. 🔤 `/scramble` - Word Scramble Challenge\n"
        "5. 🎲 `/dice` - Lucky Dice Roll\n\n"
        "Other Commands:\n"
        "💰 `/score` - Apna Score Dekhein\n"
        "🎁 `/daily` - Daily +500 Free Bonus\n"
        "🏆 `/leaderboard` - Group ke Top 10 Players"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def score_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    points = db.get_or_create_user(user.id, user.first_name)
    await update.message.reply_text(f"💰 {user.first_name}, aapka total score: *{points} Points*", parse_mode="Markdown")

async def daily_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.get_or_create_user(user.id, user.first_name)
    success, result = db.claim_daily_bonus(user.id)
    if success:
        await update.message.reply_text(f"🎁 *Daily Bonus!* +500 points claim hue.\nKul Score: *{result} Points*", parse_mode="Markdown")
    else:
        await update.message.reply_text(f"⚠️ {result}")

async def leaderboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    top_players = db.get_top_players(10)
    if not top_players:
        await update.message.reply_text("Abhi tak kisi ne koi points nahi banaye!")
        return
    
    text = "🏆 *itz-360 TOP 10 PLAYERS* 🏆\n\n"
    medals = ["🥇", "🥈", "🥉"]
    for i, (name, score) in enumerate(top_players, 1):
        rank = medals[i-1] if i <= 3 else f"{i}."
        text += f"{rank} *{name}*: `{score} pts`\n"
    await update.message.reply_text(text, parse_mode="Markdown")

# --- Central Message Handler (Guess & Scramble ke text guesses ke liye) ---
async def central_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    
    # Pehle Word Scramble check karega, agar word solve hua to guess check nahi karega
    handled = await scramble.handle_scramble_guess(update, context)
    if not handled:
        await guess.handle_guess_number(update, context)

def main():
    # Database initialize karein
    db.init_db()

    TOKEN = os.getenv("BOT_TOKEN")
    if not TOKEN:
        raise ValueError("BOT_TOKEN environment variable nahi mila!")

    # Flask web server background thread me start karein
    threading.Thread(target=run_web, daemon=True).start()

    app = ApplicationBuilder().token(TOKEN).build()

    # Core System Handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("score", score_command))
    app.add_handler(CommandHandler("daily", daily_command))
    app.add_handler(CommandHandler("leaderboard", leaderboard_command))

    # Game Handlers
    app.add_handler(CommandHandler("toss", toss.toss_cmd))
    app.add_handler(CommandHandler("guess", guess.guess_cmd))
    app.add_handler(CommandHandler("ttt", tictactoe.ttt_cmd))
    app.add_handler(CommandHandler("scramble", scramble.scramble_cmd))
    app.add_handler(CommandHandler("dice", dice.dice_cmd))

    # All Button Callbacks Route
    app.add_handler(CallbackQueryHandler(toss.toss_callback, pattern="^toss_"))
    app.add_handler(CallbackQueryHandler(dice.dice_callback, pattern="^dice_"))
    app.add_handler(CallbackQueryHandler(tictactoe.ttt_callback, pattern="^ttt_"))

    # Chat Messages Router (Number Guesses + Word Guesses)
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), central_text_handler))

    print("itz-360 Modular Bot live ho raha hai...")
    app.run_polling()

if __name__ == "__main__":
    main()
    
