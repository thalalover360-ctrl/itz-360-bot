import os
import threading
from flask import Flask, render_template
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes
)

import database as db
import toss
import guess
import tictactoe
import scramble
import dice
import battle
import chess_pvp

# --- 24/7 FLASK KEEPER ---
flask_app = Flask(__name__, template_folder=".")

@flask_app.route("/")
def home():
    return "itz-360 Bot is Online 24/7!"

@flask_app.route("/chess-app")
def chess_page():
    return render_template("chess.html")

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    flask_app.run(host="0.0.0.0", port=port)

# --- USER COMMANDS ---
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.get_or_create_user(user.id, user.first_name)
    msg = (
        f"👋 *Welcome to itz-360 Arcade, {user.first_name}!* 🎮\n\n"
        "🕹️ *Active Games:*\n"
        "1. ♟️ `/chess` — 1v1 Live Visual Chess with Friends\n"
        "2. ⚔️ `/fight` — 1v1 PvP Arena Duel (+500 / -250)\n"
        "3. 🪙 `/toss` — Coin Toss (+200 / -100)\n"
        "4. 🎯 `/guess` — Number Guessing (1 to 500)\n"
        "5. ❌ `/ttt` — Tic-Tac-Toe vs Bot (+300 / -150)\n"
        "6. 🔤 `/scramble` — Hard Word Scramble (+350)\n"
        "7. 🎲 `/dice` — Lucky 7 Dice Challenge (+500 / +200)\n\n"
        "📊 *Profile & Rewards:*\n"
        "📜 `/scorecard` — Player ID Card & Global Rank\n"
        "💰 `/score` — Instant Balance Check\n"
        "🎁 `/daily` — Free +500 Daily Bonus\n"
        "🏆 `/leaderboard` — Top 10 Hall of Fame"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def score_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    data = db.get_or_create_user(user.id, user.first_name)
    await update.message.reply_text(f"💰 *{user.first_name}*, current score: *{data['score']:,} pts*", parse_mode="Markdown")

async def scorecard_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.get_or_create_user(user.id, user.first_name)
    stats = db.get_user_stats(user.id)

    pts = stats["score"]
    if pts < 1000:
        tier = "🥉 Bronze Rookie"
    elif pts < 3000:
        tier = "🥈 Silver Pro"
    elif pts < 7000:
        tier = "🥇 Gold Master"
    elif pts < 15000:
        tier = "💎 Diamond Champion"
    else:
        tier = "👑 Arcade Legend"

    card = (
        "╔══════════════════════╗\n"
        "   🎮 *ITZ-360 SCORECARD* 🎮\n"
        "╚══════════════════════╝\n\n"
        f"👤 *Player:* `{stats['name']}`\n"
        f"🎖️ *Tier:* {tier}\n"
        f"🏆 *Global Rank:* `#{stats['rank']}`\n"
        f"💰 *Points:* `{pts:,} pts`\n\n"
        "──────────────────────\n"
        "⚔️ *Tip:* Win `/fight` duels and claim `/daily` to climb the leaderboard!"
    )
    await update.message.reply_text(card, parse_mode="Markdown")

async def daily_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.get_or_create_user(user.id, user.first_name)
    claimed, new_score = db.claim_daily(user.id)
    if claimed:
        await update.message.reply_text(f"🎁 *Daily Bonus Claimed!* You received *+500 pts*!\nTotal Score: *{new_score:,} pts*", parse_mode="Markdown")
    else:
        await update.message.reply_text("⏳ You have already claimed today's bonus. Come back tomorrow!", parse_mode="Markdown")

async def leaderboard_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    top_users = db.get_leaderboard()
    if not top_users:
        await update.message.reply_text("Leaderboard is currently empty. Play a game to establish a rank!")
        return

    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    text = "🏆 *ITZ-360 LEADERBOARD* 🏆\n\n"
    for idx, (name, sc) in enumerate(top_users):
        m = medals[idx] if idx < len(medals) else f"{idx+1}."
        text += f"{m} *{name}* — `{sc:,} pts`\n"
    await update.message.reply_text(text, parse_mode="Markdown")

# Message Router for Guess & Scramble
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    handled = await scramble.handle_scramble_guess(update, context)
    if not handled:
        await guess.handle_guess_number(update, context)

# --- BOT INITIALIZER ---
def main():
    db.init_db()

    # Flask web server start
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    token = os.environ.get("BOT_TOKEN")
    if not token:
        print("ERROR: BOT_TOKEN is missing!")
        return

    app = ApplicationBuilder().token(token).build()

    # Base Commands
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("score", score_cmd))
    app.add_handler(CommandHandler("scorecard", scorecard_cmd))
    app.add_handler(CommandHandler("profile", scorecard_cmd))
    app.add_handler(CommandHandler("daily", daily_cmd))
    app.add_handler(CommandHandler("leaderboard", leaderboard_cmd))

    # Game Commands
    app.add_handler(CommandHandler("chess", chess_pvp.chess_cmd))
    app.add_handler(CommandHandler("fight", battle.fight_cmd))
    app.add_handler(CommandHandler("toss", toss.toss_cmd))
    app.add_handler(CommandHandler("guess", guess.guess_cmd))
    app.add_handler(CommandHandler("ttt", tictactoe.ttt_cmd))
    app.add_handler(CommandHandler("scramble", scramble.scramble_cmd))
    app.add_handler(CommandHandler("dice", dice.dice_cmd))

    # Inline Button Callback Handlers
    app.add_handler(CallbackQueryHandler(battle.battle_callback, pattern="^bat_"))
    app.add_handler(CallbackQueryHandler(toss.toss_callback, pattern="^toss_"))
    app.add_handler(CallbackQueryHandler(tictactoe.ttt_callback, pattern="^ttt_"))
    app.add_handler(CallbackQueryHandler(dice.dice_callback, pattern="^dice_"))

    # Chat Text Message Handler
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), text_handler))

    print("itz-360 Arcade Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
    
