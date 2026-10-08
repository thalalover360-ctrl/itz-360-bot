import os
import threading
from flask import Flask, render_template
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

# Custom modules
import database as db
from toss import toss_cmd
from dice import dice_cmd
from guess import guess_cmd, guess_callback
from scramble import scramble_cmd, scramble_callback
from tictactoe import ttt_cmd, ttt_callback
from battle import fight_cmd, fight_callback
from chess_pvp import chess_cmd

# Flask Setup
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "itz360 Arcade Bot is running!"

@web_app.route('/chess')
def chess_view():
    return render_template('chess.html')

@web_app.route('/maut360')
def maut360_view():
    return render_template('maut360.html')

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host="0.0.0.0", port=port)

# Command Handlers
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.get_or_create_user(user.id, user.first_name)
    
    welcome_text = (
        f"🎮 *Welcome to itz360 Arcade, {user.first_name}!* 🎮\n\n"
        "Yahan sabhi games live aur active hain:\n"
        "• 🥊 `/maut` - 2D Fighting Arena (50 Stages)\n"
        "• ♟️ `/chess` - 1v1 PvP Chess Match\n"
        "• ⚔️ `/fight` - Duel a Friend\n"
        "• 🪙 `/toss` - Coin Flip (+Coins)\n"
        "• 🎲 `/dice` - Roll Lucky 7\n"
        "• ❌ `/ttt` - Tic-Tac-Toe\n"
        "• 🔤 `/scramble` - Word Puzzle\n"
        "• 🎯 `/guess` - Number Guessing\n"
        "• 💰 `/score` - Balance & Rank\n"
        "• 🎁 `/daily` - Daily Bonus"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def score_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    u = db.get_or_create_user(user.id, user.first_name)
    await update.message.reply_text(
        f"👤 *Player:* {user.first_name}\n"
        f"💰 *Coins:* {u.get('score', 0)} pts\n"
        f"🏆 *Wins:* {u.get('wins', 0)}",
        parse_mode="Markdown"
    )

async def daily_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.get_or_create_user(user.id, user.first_name)
    # Give 100 free coins daily
    db.update_score(user.id, 100)
    await update.message.reply_text(
        f"🎁 *Daily Bonus Claimed!*\n+{100} Coins aapke wallet me add ho gaye! 🪙",
        parse_mode="Markdown"
    )
    async def maut_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user:
        return
        
    db.get_or_create_user(user.id, user.first_name)
    game_url = "https://itz-360-bot.onrender.com/maut360"

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🥊 Play MAUT 360 (50 Levels) ⚔️", web_app=WebAppInfo(url=game_url))
        ]
    ])

    await update.message.reply_text(
        f"🥊 *MAUT 360: 2D ARENA FIGHTER* 🥊\n\n"
        f"👤 *Fighter:* {user.first_name}\n"
        f"🏆 *Championship:* 50 Progressive Levels\n"
        f"⚡ *Controls:* Punch, Kick, Aura Charge & Ultimate!\n\n"
        "Fight start karne ke liye neeche button dabayein:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

def main():
    token = os.environ.get("BOT_TOKEN")
    if not token:
        print("BOT_TOKEN nahi mila! Environment variables check karein.")
        return

    # Start Flask Web Server
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # Telegram Application
    app = ApplicationBuilder().token(token).build()

    # Register Handlers
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("score", score_cmd))
    app.add_handler(CommandHandler("daily", daily_cmd))
    app.add_handler(CommandHandler("toss", toss_cmd))
    app.add_handler(CommandHandler("dice", dice_cmd))
    app.add_handler(CommandHandler("chess", chess_cmd))
    app.add_handler(CommandHandler("maut", maut_cmd))

    # Battle & Minigames
    app.add_handler(CommandHandler("fight", fight_cmd))
    app.add_handler(CallbackQueryHandler(fight_callback, pattern=r"^fight_"))

    app.add_handler(CommandHandler("ttt", ttt_cmd))
    app.add_handler(CallbackQueryHandler(ttt_callback, pattern=r"^ttt_"))

    app.add_handler(CommandHandler("guess", guess_cmd))
    app.add_handler(CallbackQueryHandler(guess_callback, pattern=r"^guess_"))

    app.add_handler(CommandHandler("scramble", scramble_cmd))
    app.add_handler(CallbackQueryHandler(scramble_callback, pattern=r"^scramble_"))

    print("itz-360 Arcade Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
    
