import os
import threading
from flask import Flask, render_template
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

import database as db
from toss import toss_cmd
from dice import dice_cmd
from guess import guess_cmd
from scramble import scramble_cmd
from tictactoe import ttt_cmd, ttt_callback
from battle import fight_cmd
from chess_pvp import chess_cmd
from maut_pvp import maut_fight_cmd, maut_pvp_callback

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

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.get_or_create_user(user.id, user.first_name)
    msg = (
        f"🎮 *Welcome to itz360 Arcade, {user.first_name}!* 🎮\n\n"
        "• 🥊 `/maut` - 2D Fighting Mini App\n"
        "• ⚔️ `/mautfight <coins>` - PvP Coin Duel\n"
        "• ♟️ `/chess` - 1v1 PvP Chess\n"
        "• 🗡️ `/fight` - Duel\n"
        "• 🪙 `/toss` - Toss\n"
        "• 🎲 `/dice` - Dice\n"
        "• ❌ `/ttt` - Tic-Tac-Toe\n"
        "• 🔤 `/scramble` - Word Game\n"
        "• 🎯 `/guess` - Number Guess\n"
        "• 💰 `/score` - Wallet\n"
        "• 🎁 `/daily` - Daily Reward"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def score_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    u = db.get_or_create_user(user.id, user.first_name)
    score = u.get('score', 0) if isinstance(u, dict) else 0
    wins = u.get('wins', 0) if isinstance(u, dict) else 0
    await update.message.reply_text(f"👤 *Player:* {user.first_name}\n💰 *Coins:* {score}\n🏆 *Wins:* {wins}", parse_mode="Markdown")

async def daily_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.get_or_create_user(user.id, user.first_name)
    db.update_score(user.id, 100)
    await update.message.reply_text("🎁 *Daily Bonus Claimed!* +100 Coins 🪙", parse_mode="Markdown")

async def maut_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user:
        return
    db.get_or_create_user(user.id, user.first_name)
    url = "https://itz-360-bot.onrender.com/maut360"
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🥊 Play MAUT 360 ⚔️", web_app=WebAppInfo(url=url))]])
    await update.message.reply_text(f"🥊 *MAUT 360 ARENA*\nFighter: {user.first_name}\nStage: 50 Levels", reply_markup=kb, parse_mode="Markdown")

def main():
    token = os.environ.get("BOT_TOKEN")
    if not token:
        print("BOT_TOKEN missing!")
        return

    flask_t = threading.Thread(target=run_flask)
    flask_t.daemon = True
    flask_t.start()

    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("score", score_cmd))
    app.add_handler(CommandHandler("daily", daily_cmd))
    app.add_handler(CommandHandler("toss", toss_cmd))
    app.add_handler(CommandHandler("dice", dice_cmd))
    app.add_handler(CommandHandler("chess", chess_cmd))
    app.add_handler(CommandHandler("maut", maut_cmd))
    app.add_handler(CommandHandler("mautfight", maut_fight_cmd))
    app.add_handler(CallbackQueryHandler(maut_pvp_callback, pattern=r"^mpvp_"))
    app.add_handler(CommandHandler("fight", fight_cmd))
    app.add_handler(CommandHandler("ttt", ttt_cmd))
    app.add_handler(CallbackQueryHandler(ttt_callback, pattern=r"^ttt_"))
    app.add_handler(CommandHandler("guess", guess_cmd))
    app.add_handler(CommandHandler("scramble", scramble_cmd))

    print("Bot is live!")
    app.run_polling()

if __name__ == "__main__":
    main()
    
