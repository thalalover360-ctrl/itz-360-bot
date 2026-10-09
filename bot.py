import os
import threading
import logging
import random
import string
import time
from flask import Flask, render_template, request, jsonify
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

import database as db
from toss import toss_cmd
from dice import dice_cmd
from guess import guess_cmd
from scramble import scramble_cmd
from tictactoe import ttt_cmd, ttt_callback
from battle import fight_cmd
from chess_pvp import chess_cmd
from maut_pvp import maut_pvp_callback

logging.basicConfig(level=logging.INFO)

web_app = Flask(__name__)

# Real-time Web PvP Rooms Memory
ROOMS = {}

@web_app.route('/')
def home():
    return "itz360 Arcade Bot is running!"

@web_app.route('/chess')
def chess_view():
    return render_template('chess.html')

@web_app.route('/maut360')
def maut360_view():
    return render_template('maut360.html')

# Multiplayer Sync API Endpoints
@web_app.route('/api/room/state', methods=['GET'])
def get_room_state():
    room_id = request.args.get('room')
    if not room_id or room_id not in ROOMS:
        return jsonify({"status": "solo"})
    return jsonify(ROOMS[room_id])

@web_app.route('/api/room/action', methods=['POST'])
def post_room_action():
    data = request.json or {}
    room_id = data.get('room')
    role = data.get('role') # 'p1' or 'p2'
    action = data.get('action') # 'punch', 'kick', 'jump', 'move_left', 'move_right', 'idle'

    if not room_id or room_id not in ROOMS:
        return jsonify({"status": "error"}), 400

    room = ROOMS[room_id]
    room[f'{role}_last_act'] = action
    room[f'{role}_time'] = time.time()

    # Apply Damage
    if action in ['punch', 'kick']:
        dmg = 15 if action == 'punch' else 25
        target = 'p2_hp' if role == 'p1' else 'p1_hp'
        room[target] = max(0, room[target] - dmg)

    return jsonify({"status": "ok", "state": room})

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
        "🥊 /maut - MAUT 360 (Visual Fight & PvP)\n"
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

# Visual PvP Room Creator
async def maut_room_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    safe_user(user)
    
    room_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
    ROOMS[room_code] = {
        "p1_name": user.first_name,
        "p2_name": "Waiting...",
        "p1_hp": 100,
        "p2_hp": 100,
        "p1_last_act": "idle",
        "p2_last_act": "idle",
        "p1_time": time.time(),
        "p2_time": time.time()
    }

    base_url = "https://itz-360-bot.onrender.com/maut360"
    p1_url = f"{base_url}?room={room_code}&role=p1"
    p2_url = f"{base_url}?room={room_code}&role=p2"
    solo_url = f"{base_url}"

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"🥊 Join as {user.first_name} (P1)", url=p1_url)],
        [InlineKeyboardButton("⚔️ Join Fight (P2 / Kaju)", url=p2_url)],
        [InlineKeyboardButton("🤖 Play Solo vs Computer", url=solo_url)]
    ])

    msg = (
        f"💀 *MAUT 360 REAL DUEL ARENA* 💀\n\n"
        f"Host: *{user.first_name}*\n"
        f"Room Code: `{room_code}`\n\n"
        f"👉 *{user.first_name}* P1 dabaye aur friend/Kaju P2 dabaye!\n"
        f"Dono ke screens par real time fight start hogi!"
    )
    await update.message.reply_text(msg, reply_markup=kb, parse_mode="Markdown")

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

    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("score", score_cmd))
    app.add_handler(CommandHandler("daily", daily_cmd))

    # Real Visual MAUT Arena Command
    app.add_handler(CommandHandler("maut", make_safe(maut_room_cmd)))
    app.add_handler(CommandHandler("maut360", make_safe(maut_room_cmd)))
    app.add_handler(CommandHandler("mautfight", make_safe(maut_room_cmd)))
    app.add_handler(CallbackQueryHandler(maut_pvp_callback, pattern=r"^mpvp_"))

    # Baaki arcade games
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
