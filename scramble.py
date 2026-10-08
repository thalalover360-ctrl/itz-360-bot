import random
from telegram import Update
from telegram.ext import ContextTypes
import database as db

# Diverse, challenging vocabulary across multiple categories
ALL_WORDS = [
    # Technology & Science
    {"word": "ALGORITHM", "hint": "Step-by-step problem-solving procedure"},
    {"word": "CRYPTOGRAPHY", "hint": "Art of writing or solving codes"},
    {"word": "CYBERSECURITY", "hint": "Protection of computer systems from theft"},
    {"word": "BLOCKCHAIN", "hint": "Decentralized digital ledger technology"},
    {"word": "MICROPROCESSOR", "hint": "Integrated circuit containing CPU logic"},
    {"word": "QUANTUM", "hint": "Branch of physics dealing with atomic scales"},
    {"word": "BANDWIDTH", "hint": "Maximum rate of data transfer across a path"},
    {"word": "KUBERNETES", "hint": "Container orchestration system"},
    {"word": "NEURALNETWORK", "hint": "Interconnected nodes modeling the brain"},
    {"word": "REPOSITORIES", "hint": "Storage locations for software packages"},
    {"word": "VIRTUALIZATION", "hint": "Creating virtual versions of resources"},
    {"word": "SUPERCONDUCTOR", "hint": "Zero electrical resistance material"},
    {"word": "PHOTOVOLTAIC", "hint": "Relating to the production of electric current at the junction of two substances"},
    {"word": "NANOTECHNOLOGY", "hint": "Manipulation of matter on atomic or molecular scale"},
    {"word": "TELEMETRY", "hint": "Automated communications process from distant sources"},

    # Geography & Landmarks
    {"word": "KILIMANJARO", "hint": "Dormant volcano and highest peak in Africa"},
    {"word": "MADAGASCAR", "hint": "Large island nation off the coast of East Africa"},
    {"word": "MEDITERRANEAN", "hint": "Sea connected to the Atlantic Ocean"},
    {"word": "ARCHIPELAGO", "hint": "An extensive group of islands"},
    {"word": "STRATOSPHERE", "hint": "Atmospheric layer containing ozone"},
    {"word": "HEMISPHERE", "hint": "Half of the earth divided north/south or east/west"},
    {"word": "SCANDINAVIA", "hint": "Subregion in Northern Europe"},
    {"word": "PHILIPPINES", "hint": "Southeast Asian archipelagic nation"},
    {"word": "EVEREST", "hint": "Highest mountain peak above sea level"},
    {"word": "AMAZONAS", "hint": "Massive South American river basin"},
    {"word": "GLACIER", "hint": "Slowly moving mass or river of ice"},
    {"word": "ANTARCTICA", "hint": "Earth's southernmost icy continent"},
    {"word": "CASPIAN", "hint": "World's largest inland body of water"},

    # High-Difficulty Vocabulary
    {"word": "SERENDIPITY", "hint": "Occurrence of events by chance in a happy way"},
    {"word": "QUINTESSENTIAL", "hint": "Representing the most perfect example of a quality"},
    {"word": "UBIQUITOUS", "hint": "Present, appearing, or found everywhere"},
    {"word": "ANACHRONISM", "hint": "Something belonging to a period other than that in which it exists"},
    {"word": "EPHEMERAL", "hint": "Lasting for a very short time"},
    {"word": "LABYRINTH", "hint": "A complicated irregular network of passages"},
    {"word": "PERSEVERANCE", "hint": "Persistence in doing something despite difficulty"},
    {"word": "SURREPTITIOUS", "hint": "Kept secret, especially because it would not be approved of"},
    {"word": "MALLEABLE", "hint": "Able to be hammered or pressed permanently out of shape"},
    {"word": "EQUILIBRIUM", "hint": "A state in which opposing forces are balanced"},
    {"word": "PROLIFIC", "hint": "Producing much fruit, foliage, or work"},
    {"word": "CONUNDRUM", "hint": "A confusing and difficult problem or question"},
    {"word": "MAGNANIMOUS", "hint": "Very generous or forgiving"},
    {"word": "CACISTOCRACY", "hint": "Government by the least suitable or competent citizens"},
    {"word": "BENEVOLENT", "hint": "Well meaning and kindly"},

    # Cinema, Pop Culture & Lore
    {"word": "INTERSTELLAR", "hint": "Nolan's sci-fi masterpiece traveling through wormholes"},
    {"word": "OPPENHEIMER", "hint": "Biographical film on the father of the atomic bomb"},
    {"word": "INCEPTION", "hint": "Stealing corporate secrets through dream-sharing technology"},
    {"word": "GLADIATOR", "hint": "Roman general betrayed and reduced to fighting in arenas"},
    {"word": "METROPOLIS", "hint": "Fritz Lang's 1927 pioneering sci-fi city"},
    {"word": "HOGWARTS", "hint": "Fictional school of witchcraft and wizardry"},
    {"word": "WESTEROS", "hint": "Fictional continent from Game of Thrones"},
    {"word": "MILLENNIUM", "hint": "Han Solo's iconic Falcon starship prefix"},
    {"word": "AVATAR", "hint": "Sci-fi epic set on the moon of Pandora"},
    {"word": "TITANIC", "hint": "Tragic voyage directed by James Cameron"},

    # Gaming & Fantasy
    {"word": "PLAYSTATION", "hint": "Sony's iconic flagship console brand"},
    {"word": "NINTENDO", "hint": "Japanese gaming company behind Mario and Zelda"},
    {"word": "OVERWATCH", "hint": "Team-based hero shooter by Blizzard"},
    {"word": "CYBERPUNK", "hint": "Night City dystopian open-world RPG"},
    {"word": "ELDENRING", "hint": "FromSoftware's open-world fantasy Soulsborne game"},
    {"word": "VALORANT", "hint": "Riot Games tactical 5v5 FPS"},
    {"word": "COUNTERSTRIKE", "hint": "Classic bomb defusal tactical FPS series"},
    {"word": "ASSASSIN", "hint": "Creed franchise featuring the hidden blade"},
    {"word": "LEAGUEOFLGNDS", "hint": "Popular MOBA featuring champions and lanes"},
    {"word": "MINECRAFT", "hint": "Block-based sandbox survival game"}
]

active_scramble_games = {}
chat_used_words = {}

def get_scrambled_word(word):
    letters = list(word)
    # Ensure it is well-shuffled and not equal to the original word
    while True:
        random.shuffle(letters)
        scrambled = "".join(letters)
        if scrambled != word or len(word) <= 1:
            return scrambled

def pick_unique_word(chat_id):
    if chat_id not in chat_used_words:
        chat_used_words[chat_id] = []

    available = [w for w in ALL_WORDS if w["word"] not in chat_used_words[chat_id]]

    if not available:
        chat_used_words[chat_id] = []
        available = ALL_WORDS.copy()

    chosen = random.choice(available)
    chat_used_words[chat_id].append(chosen["word"])
    return chosen

async def scramble_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user
    db.get_or_create_user(user.id, user.first_name)

    if chat_id in active_scramble_games:
        current = active_scramble_games[chat_id]
        await update.message.reply_text(
            f"⚠️ *An unsolved challenge is already active!*\n\n"
            f"🔤 Jumbled: `{current['scrambled']}`\n"
            f"💡 Hint: _{current['hint']}_\n"
            f"Length: *{len(current['word'])} letters*",
            parse_mode="Markdown"
        )
        return

    chosen = pick_unique_word(chat_id)
    scrambled = get_scrambled_word(chosen["word"])

    active_scramble_games[chat_id] = {
        "word": chosen["word"],
        "scrambled": scrambled,
        "hint": chosen["hint"]
    }

    msg = (
        "🧩 *EXPERT WORD SCRAMBLE CHALLENGE* 🧩\n\n"
        f"Unscramble this word:  `{scrambled}`\n"
        f"Length: *{len(chosen['word'])} letters*\n"
        f"💡 *Clue:* _{chosen['hint']}_\n\n"
        "💰 Reward: *+350 pts* (First to answer wins!)"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def handle_scramble_guess(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    chat_id = update.effective_chat.id
    if chat_id not in active_scramble_games:
        return False

    text = update.message.text.strip().replace(" ", "").upper()
    game = active_scramble_games[chat_id]

    if text == game["word"]:
        user = update.effective_user
        db.get_or_create_user(user.id, user.first_name)
        new_score = db.update_score(user.id, 350)
        correct_word = game["word"]
        del active_scramble_games[chat_id]

        await update.message.reply_text(
            f"🎯 *CORRECT ANSWER!* 🏆\n\n"
            f"👤 Winner: *{user.first_name}*\n"
            f"🔠 Word: `{correct_word}`\n"
            f"🎁 Earned: *+350 pts*\n"
            f"💰 New Balance: *{new_score:,} pts*",
            parse_mode="Markdown"
        )
        return True

    return False
    
