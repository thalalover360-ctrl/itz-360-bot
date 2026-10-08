import random
from telegram import Update
from telegram.ext import ContextTypes
import database as db

# Active games track karne ke liye: {chat_id: {"target": int, "moves_left": int, "user_id": int, "user_name": str}}
active_guess_games = {}

async def guess_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user
    db.get_or_create_user(user.id, user.first_name)

    if chat_id in active_guess_games:
        await update.message.reply_text("⚠️ Is group me pehle se ek Guess Game chal raha hai! Chat me apna number likh kar bhejo.")
        return

    secret_number = random.randint(1, 500)
    active_guess_games[chat_id] = {
        "target": secret_number,
        "moves_left": 10,
        "user_id": user.id,
        "user_name": user.first_name
    }

    msg = (
        f"🎯 *Guess The Number Game Shuru!* 🎯\n\n"
        f"Shuru kiya: *{user.first_name}*\n"
        "Range: *1 se 500*\n"
        "Total Moves: *10*\n"
        "Jeetne par: *+500 pts* | Haarne par: *-200 pts*\n\n"
        "Koi bhi member direct chat me number type karke guess kar sakta hai!"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def handle_guess_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in active_guess_games:
        return

    text = update.message.text.strip()
    if not text.isdigit():
        return

    guess_val = int(text)
    user = update.effective_user
    db.get_or_create_user(user.id, user.first_name)

    game = active_guess_games[chat_id]
    target = game["target"]
    game["moves_left"] -= 1
    moves_left = game["moves_left"]

    if guess_val == target:
        new_score = db.update_score(user.id, 500)
        del active_guess_games[chat_id]
        await update.message.reply_text(
            f"🎉 *BINGO! Bilkul Sahi Guess!* 🎯\n\n"
            f"Winner: *{user.first_name}*\n"
            f"Secret Number: *{target}*\n"
            f"Points: *+500*\n"
            f"Total Score: *{new_score} pts*",
            parse_mode="Markdown"
        )
    elif moves_left <= 0:
        new_score = db.update_score(user.id, -200)
        del active_guess_games[chat_id]
        await update.message.reply_text(
            f"💀 *Game Over! 10 Moves Khatam!* 💀\n\n"
            f"Secret Number tha: *{target}*\n"
            f"Last Guesser ({user.first_name}) Points: *-200*\n"
            f"Total Score: *{new_score} pts*",
            parse_mode="Markdown"
        )
    elif guess_val < target:
        await update.message.reply_text(
            f"📈 *Too Low!* {guess_val} se BADA number hai.\n"
            f"Bache hue moves: *{moves_left}/10*",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            f"📉 *Too High!* {guess_val} se CHHOTA number hai.\n"
            f"Bache hue moves: *{moves_left}/10*",
            parse_mode="Markdown"
        )
      
