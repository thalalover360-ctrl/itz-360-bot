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

import database as db
import toss
import guess
import tictactoe
import scramble
import dice

# --- 24/7 FLASK KEEPER (For Render & cron-job.org) ---
flask_app = Flask(__name__)

@flask_app.route("/")
def home():
    return "itz-360 Bot is Online 24/7!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    flask_app.run(host="0.0.0.0", port=port)

# --- USER COMMANDS ---
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.get_or_create_user(user.id, user.first_name)
    msg = (
        f"👋 *Welcome to itz-360 Arcade, {user.first_name}!* 🎮\n\n"
        "🕹️ *5 Dhamakedar Games:*\n"
        "1. 🪙 `/toss` — Coin Toss (+200 / -100)\n"
        "2. 🎯 `/guess` — Number Guessing (1 se 500)\n"
        "3. ❌ `/ttt` — Tic-Tac-Toe vs Bot (+300 / -150)\n"
        "4. 🔤 `/scramble` — Word Scramble (+250)\n"
        "5. 🎲 `/dice` — Lucky 7 Dice (+500 / +200)\n\n"
        "📊 *Profile & Rewards:*\n"
        "📜 `/scorecard` — Player ID Card & Rank\n"
        "💰 `/score` — Instant Balance\n"
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
        "🔥 *Tip:* Roz `/daily` claim karein aur games jeet kar leaderboard par chadhayein!"
    )
    await update.message.reply_text(card, parse_mode="Markdown")

async def daily_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.get_or_create_user(user.id, user.first_name)
    claimed, new_score = db.claim_daily(user.id)
    if claimed:
        await update.message.reply_text(f"🎁 *Daily Bonus Claimed!* Aapko mile *+500 pts*!\nTotal Score: *{new_score:,} pts*", parse_mode="Markdown")
    else:
        await update.message.reply_text("⏳ Aaj ka daily bonus aap pehle hi claim kar chuke hain. Kal subah wapas aayein!", parse_mode="Markdown")

async def leaderboard_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    top_users = db.get_leaderboard()
    if not top_users:
        await update.message.reply_text("Leaderboard abhi khali hai. Game khel kar rank banayein!")
        return

    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    text = "🏆 *ITZ-360 LEADERBOARD* 🏆\n\n"
    for idx, (name, sc) in enumerate(top_users):
        m = medals[idx] if idx < len(medals) else f"{idx+1}."
        text += f"{m} *{name}* — `{sc:,} pts`\n"
    await update.message.reply_text(text, parse_mode="Markdown")

# Message Router (Guess & Scramble ke input sambhalne ke liye)
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
        print("ERROR: BOT_TOKEN Environment Variable nahi mila!")
        return

    app = ApplicationBuilder().token(token).build()

    # Command Handlers
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("score", score_cmd))
    app.add_handler(CommandHandler("scorecard", scorecard_cmd))
    app.add_handler(CommandHandler("profile", scorecard_cmd))
    app.add_handler(CommandHandler("daily", daily_cmd))
    app.add_handler(CommandHandler("leaderboard", leaderboard_cmd))

    # Game Handlers
    app.add_handler(CommandHandler("toss", toss.toss_cmd))
    app.add_handler(CommandHandler("guess", guess.guess_cmd))
    app.add_handler(CommandHandler("ttt", tictactoe.ttt_cmd))
    app.add_handler(CommandHandler("scramble", scramble.scramble_cmd))
    app.add_handler(CommandHandler("dice", dice.dice_cmd))

    # Inline Button Callbacks
    app.add_handler(CallbackQueryHandler(toss.toss_callback, pattern="^toss_"))
    app.add_handler(CallbackQueryHandler(tictactoe.ttt_callback, pattern="^ttt_"))
    app.add_handler(CallbackQueryHandler(dice.dice_callback, pattern="^dice_"))

    # Text Guessing Handler
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), text_handler))

    print("itz-360 Bot polling running successfully...")
    app.run_polling()

if __name__ == "__main__":
    main()
    
