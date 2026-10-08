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

# Custom Game Modules
import database as db
from toss import toss_cmd
from dice import dice_cmd
from guess import guess_cmd, guess_callback
from scramble import scramble_cmd, scramble_callback
from tictactoe import ttt_cmd, ttt_callback
from battle import fight_cmd, fight_callback
from chess_pvp import chess_cmd
from maut_pvp import maut_fight_cmd, maut_pvp_callback

# Flask Web Server
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

# General Commands
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.get_or_create_user(user.id, user.first_name)
    
    welcome_text = (
        f"🎮 *Welcome to itz360 Arcade, {user.first_name}!* 🎮\n\n"
        "Available Games & Commands:\n"
        "• 🥊 `/maut` - 2D Fighting Mini App (50 Stages)\n"
        "• ⚔️ `/mautfight <coins>` - Group Coin-Wager PvP\n"
        "• ♟️ `/chess` - 1v1 PvP Chess Match\n"
        "• 🗡️ `/fight` - Simple Turn Duel\n"
        "• 🪙 `/toss` - Coin Toss\n"
        "• 🎲 `/dice` - Roll Lucky 7\n"
        "• ❌ `/ttt` - Tic-Tac-Toe\n"
        "• 🔤 `/scramble` - Word Puzzle\n"
        "• 🎯 `/guess` - Number Guessing\n"
        "• 💰 `/score` - Wallet Balance\n"
        "• 🎁 `/daily` - Daily Free Coins"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def score_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    u = db.get_or_create_user(user.id, user.first_name)
    score = u.get('score', 0) if isinstance(u, dict) else 0
    wins = u.get('wins', 0) if isinstance(u, dict) else 0
    await update.message.reply_text(
        f"👤 *Player:* {user.first_name}\n"
        f"💰 *Coins:* {score} pts\n"
        f"🏆 *Wins:* {wins}",
        parse_mode="Markdown"
    )

async def daily_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.get_or_create_user(user.id, user.first_name)
    db.update_score(user.id, 100)
    await update.message.reply_text(
        f"🎁 *Daily Bonus Claimed!*\n+100 Coins aapke balance me add ho gaye! 🪙",
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
        "Fight shuru karne ke liye button dabayein:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

def main():
    token = os.environ.get("BOT_TOKEN")
    if not token:
        print("BOT_TOKEN nahi mila! Environment variables me check karein.")
        return

    # Start Flask Web Server Thread
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # Telegram Bot Setup
    app = ApplicationBuilder().token(token).build()

    # Base Handlers
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("score", score_cmd))
    app.add_handler(CommandHandler("daily", daily_cmd))

    # Arcade Games
    app.add_handler(CommandHandler("toss", toss_cmd))
    app.add_handler(CommandHandler("dice", dice_cmd))
    app.add_handler(CommandHandler("chess", chess_cmd))
    app.add_handler(CommandHandler("maut", maut_cmd))

    # Maut360 PvP (Wager Coin Battles)
    app.add_handler(CommandHandler("mautfight", maut_fight_cmd))
    app.add_handler(CallbackQueryHandler(maut_pvp_callback, pattern=r"^mpvp_"))

    # Other Minigames
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
    
