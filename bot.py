import os
import threading
import logging
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

logging.basicConfig(level=logging.INFO)

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
    web_app.run(host="0.0.0.0", port=port, use_reloader=False)

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user:
        try:
            db.get_or_create_user(user.id, user.first_name)
        except Exception as e:
            print(f"DB Error: {e}", flush=True)
    msg = "🎮 Welcome to itz360 Arcade!\n\n/maut - Play MAUT 360\n/chess - Chess 1v1\n/guess - Number Game\n/toss - Toss Coin\n/score - My Coins"
    await update.message.reply_text(msg)

async def score_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    u = db.get_or_create_user(user.id, user.first_name)
    score = u.get('score', 0) if isinstance(u, dict) else 0
    await update.message.reply_text(f"Coins: {score}")

async def daily_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.get_or_create_user(user.id, user.first_name)
    db.update_score(user.id, 100)
    await update.message.reply_text("Bonus: +100 Coins!")

async def maut_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user:
        try:
            db.get_or_create_user(user.id, user.first_name)
        except Exception:
            pass
    url = "https://itz-360-bot.onrender.com/maut360"
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🥊 Play MAUT 360", web_app=WebAppInfo(url=url))]])
    await update.message.reply_text("⚔️ MAUT 360 Arena:", reply_markup=kb)

if __name__ == "__main__":
    token = os.environ.get("BOT_TOKEN")
    if not token:
        print("❌ CRITICAL: BOT_TOKEN is missing!", flush=True)
        exit(1)

    # Flask ko background me daalo
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # Telegram ko MAIN thread me chalao taaki crash na ho
    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("score", score_cmd))
    app.add_handler(CommandHandler("scorecard", score_cmd))
    app.add_handler(CommandHandler("daily", daily_cmd))
    app.add_handler(CommandHandler("toss", toss_cmd))
    app.add_handler(CommandHandler("dice", dice_cmd))
    app.add_handler(CommandHandler("chess", chess_cmd))
    app.add_handler(CommandHandler("maut", maut_cmd))
    app.add_handler(CommandHandler("maut360", maut_cmd))
    app.add_handler(CommandHandler("mautfight", maut_fight_cmd))
    app.add_handler(CallbackQueryHandler(maut_pvp_callback, pattern=r"^mpvp_"))
    app.add_handler(CommandHandler("fight", fight_cmd))
    app.add_handler(CommandHandler("ttt", ttt_cmd))
    app.add_handler(CallbackQueryHandler(ttt_callback, pattern=r"^ttt_"))
    app.add_handler(CommandHandler("guess", guess_cmd))
    app.add_handler(CommandHandler("scramble", scramble_cmd))

    print("✅ BOT IS LIVE ON TELEGRAM!", flush=True)
    app.run_polling(drop_pending_updates=True)
    
