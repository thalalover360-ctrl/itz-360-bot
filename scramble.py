import random
from telegram import Update
from telegram.ext import ContextTypes
import database as db

# Word list aur category hints
WORDS_DB = [
    {"word": "VIRAT", "hint": "Indian Cricketer"},
    {"word": "DHONI", "hint": "Legendary Captain & Finisher"},
    {"word": "ROHIT", "hint": "Hitman Cricketer"},
    {"word": "PYTHON", "hint": "Programming Language & Snake"},
    {"word": "RENDER", "hint": "Cloud Hosting Platform"},
    {"word": "TELEGRAM", "hint": "Messaging App"},
    {"word": "CRICKET", "hint": "India's Favorite Sport"},
    {"word": "FOOTBALL", "hint": "Global Sport with 11 Players"},
    {"word": "BOLLYWOOD", "hint": "Indian Cinema Industry"},
    {"word": "SHOLAY", "hint": "Classic Bollywood Movie"},
    {"word": "CHAI", "hint": "National Drink of India"},
    {"word": "SAMOSA", "hint": "Famous Indian Crispy Snack"},
    {"word": "DIWALI", "hint": "Festival of Lights"},
    {"word": "CHAMPION", "hint": "Winner of the Tournament"},
    {"word": "ARCADE", "hint": "Gaming Room or Hub"}
]

# Active scramble games: {chat_id: {"word": str, "scrambled": str, "hint": str}}
active_scramble_games = {}

def get_scrambled_word(word):
    letters = list(word)
    while True:
        random.shuffle(letters)
        scrambled = "".join(letters)
        if scrambled != word or len(word) <= 1:
            return scrambled

async def scramble_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user
    db.get_or_create_user(user.id, user.first_name)

    if chat_id in active_scramble_games:
        current = active_scramble_games[chat_id]
        await update.message.reply_text(
            f"⚠️ Pehle se ek word pending hai!\n"
            f"Scrambled: *{current['scrambled']}*\n"
            f"Hint: *{current['hint']}*",
            parse_mode="Markdown"
        )
        return

    chosen = random.choice(WORDS_DB)
    scrambled = get_scrambled_word(chosen["word"])

    active_scramble_games[chat_id] = {
        "word": chosen["word"],
        "scrambled": scrambled,
        "hint": chosen["hint"]
    }

    msg = (
        "🔤 *Word Scramble Challenge Shuru!* 🔤\n\n"
        f"Shabd: *{scrambled}*\n"
        f"Hint: 💡 *{chosen['hint']}*\n"
        "Points: *+250 pts*\n\n"
        "Jo banda sabse pehle sahi spelling chat me likhega, points usko milenge!"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def handle_scramble_guess(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    chat_id = update.effective_chat.id
    if chat_id not in active_scramble_games:
        return False

    text = update.message.text.strip().upper()
    game = active_scramble_games[chat_id]

    if text == game["word"]:
        user = update.effective_user
        db.get_or_create_user(user.id, user.first_name)
        new_score = db.update_score(user.id, 250)
        correct_word = game["word"]
        del active_scramble_games[chat_id]

        await update.message.reply_text(
            f"🎉 *FASTEST FINGER FIRST! Sahi Jawab!* 🏆\n\n"
            f"Winner: *{user.first_name}*\n"
            f"Word: *{correct_word}*\n"
            f"Points: *+250 pts*\n"
            f"Total Score: *{new_score} pts*",
            parse_mode="Markdown"
        )
        return True

    return False
  
