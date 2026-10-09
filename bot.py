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

def safe_user(user):
    if not user:
        return {}
    try:
        return db.get_or_create_user(user.id, user.first_name) or {}
    except Exception as e:
        print(f"DB Bypass: {e}", flush=True)
        return {"score": 100}

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    safe_user(user)
    msg = (
        "🎮 *Welcome to itz360 Arcade!*\n\n"
        "🥊 /maut - Play MAUT 360 Mini App\n"
        "⚔️ /mautfight - Duel Fight with Friend / Levels\n"
        "♟️ /chess - 1v1 Chess Challenge\n"
        "🎯 /guess - Guess The Number\n"
        "🪙 /toss - Flip a Coin\n"
        "🎲 /dice - Roll Dice\n"
        "💰 /score - Check Coins"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def score_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    u = safe_user(user)
    score = u.get('score', 100) if isinstance(u, dict) else 100
    await update.message.reply_text(f"💰 Aapke paas: {score} Coins hain!")

async def daily_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    safe_user(user)
    try:
        db.update_score(user.id, 100)
    except Exception:
        pass
    await update.message.reply_text("🎁 Daily Bonus: +100 Coins mil gaye!")

async def maut_app_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    safe_user(update.effective_user)
    url = "https://itz-360-bot.onrender.com/maut360"
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🥊 Play MAUT 360", web_app=WebAppInfo(url=url))]])
    await update.message.reply_text("⚔️ MAUT 360 Arena:", reply_markup=kb)

def make_safe(handler_fn):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            safe_user(update.effective_user)
            await handler_fn(update, context)
        except Exception as err:
            print(f"Command Error in {handler_fn.__name__}: {err}", flush=True)
            await update.message.reply_text(f"⚠️ Game start hone me error: {err}")
    return wrapper

if __name__ == "__main__":
    token = os.environ.get("BOT_TOKEN")
    if not token:
        print("❌ CRITICAL: BOT_TOKEN is missing!", flush=True)
        exit(1)

    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    app = ApplicationBuilder().token(token).build()

    # Base commands
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("score", score_cmd))
    app.add_handler(CommandHandler("scorecard", score_cmd))
    app.add_handler(CommandHandler("daily", daily_cmd))

    # MAUT Handlers (Web App + Group Duel)
    app.add_handler(CommandHandler("maut", make_safe(maut_app_cmd)))
    app.add_handler(CommandHandler("maut360", make_safe(maut_app_cmd)))
    app.add_handler(CommandHandler("mautfight", make_safe(maut_fight_cmd)))
    app.add_handler(CallbackQueryHandler(maut_pvp_callback, pattern=r"^mpvp_"))

    # Other arcade games
    app.add_handler(CommandHandler("toss", make_safe(toss_cmd)))
    app.add_handler(CommandHandler("dice", make_safe(dice_cmd)))
    app.add_handler(CommandHandler("chess", make_safe(chess_cmd)))
    app.add_handler(CommandHandler("guess", make_safe(guess_cmd)))
    app.add_handler(CommandHandler("scramble", make_safe(scramble_cmd)))
    app.add_handler(CommandHandler("fight", make_safe(fight_cmd)))
    app.add_handler(CommandHandler("ttt", make_safe(ttt_cmd)))
    app.add_handler(CallbackQueryHandler(ttt_callback, pattern=r"^ttt_"))

    print("✅ BOT IS LIVE ON TELEGRAM!", flush=True)
    app.run_polling(drop_pending_updates=True)
    
