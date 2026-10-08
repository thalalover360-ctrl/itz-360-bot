import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import database as db

# Active games storage: {game_id: {"board": list, "user_id": int, "user_name": str}}
active_ttt_games = {}

def check_winner(b):
    win_conditions = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8], # Horizontal
        [0, 3, 6], [1, 4, 7], [2, 5, 8], # Vertical
        [0, 4, 8], [2, 4, 6]             # Diagonal
    ]
    for x, y, z in win_conditions:
        if b[x] != " " and b[x] == b[y] == b[z]:
            return b[x]
    if " " not in b:
        return "Tie"
    return None

def build_keyboard(game_id, board):
    symbols = {" ": "⬜", "X": "❌", "O": "⭕"}
    kb = []
    for r in range(3):
        row = []
        for c in range(3):
            idx = r * 3 + c
            row.append(
                InlineKeyboardButton(
                    symbols[board[idx]], 
                    callback_data=f"ttt_move_{game_id}_{idx}"
                )
            )
        kb.append(row)
    return InlineKeyboardMarkup(kb)

async def ttt_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.get_or_create_user(user.id, user.first_name)
    
    # Har game ko ek unique ID dete hain
    game_id = f"{user.id}_{int(update.message.message_id)}"
    active_ttt_games[game_id] = {
        "board": [" "] * 9,
        "user_id": user.id,
        "user_name": user.first_name
    }

    msg = (
        f"❌ *Tic-Tac-Toe Shuru!* ⭕\n\n"
        f"Player: *{user.first_name}* (❌)\n"
        f"Bot: *itz-360* (⭕)\n"
        "Jeetne par: *+300 pts* | Haarne par: *-150 pts*\n\n"
        "Kisi bhi box par tap karke apni chaal chalo:"
    )
    await update.message.reply_text(
        msg, 
        reply_markup=build_keyboard(game_id, active_ttt_games[game_id]["board"]), 
        parse_mode="Markdown"
    )

async def ttt_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    parts = query.data.split("_")
    game_id = f"{parts[2]}_{parts[3]}"
    idx = int(parts[4])

    if game_id not in active_ttt_games:
        await query.edit_message_text("⚠️ Ye game expire ho chuka hai ya pehle hi khatam ho gaya. Naya game start karne ke liye `/ttt` likhein.")
        return

    game = active_ttt_games[game_id]

    # Sirf wahi banda click kar sakta hai jisne game shuru kiya
    if query.from_user.id != game["user_id"]:
        return

    board = game["board"]

    # Agar box already bhara ho
    if board[idx] != " ":
        return

    # Player ka move (X)
    board[idx] = "X"
    winner = check_winner(board)

    # Bot ka counter move (O) agar player na jeeta ho aur game bacha ho
    if not winner:
        empty_indices = [i for i, val in enumerate(board) if val == " "]
        if empty_indices:
            bot_pick = random.choice(empty_indices)
            board[bot_pick] = "O"
            winner = check_winner(board)

    # Result check
    if winner == "X":
        new_score = db.update_score(game["user_id"], 300)
        del active_ttt_games[game_id]
        final_text = (
            f"🎉 *Balle Balle! Aap Jeet Gaye!* 🏆\n\n"
            f"Player: *{game['user_name']}*\n"
            f"Points: *+300 pts*\n"
            f"Total Score: *{new_score} pts*"
        )
        await query.edit_message_text(final_text, reply_markup=build_keyboard(game_id, board), parse_mode="Markdown")
    elif winner == "O":
        new_score = db.update_score(game["user_id"], -150)
        del active_ttt_games[game_id]
        final_text = (
            f"💀 *Bot Jeet Gaya! Aap Haar Gaye!* 💀\n\n"
            f"Player: *{game['user_name']}*\n"
            f"Points: *-150 pts*\n"
            f"Total Score: *{new_score} pts*"
        )
        await query.edit_message_text(final_text, reply_markup=build_keyboard(game_id, board), parse_mode="Markdown")
    elif winner == "Tie":
        del active_ttt_games[game_id]
        final_text = (
            f"🤝 *Kante Ki Takkar! Match Tie Ho Gaya!* 🤝\n\n"
            f"Player: *{game['user_name']}*\n"
            f"Points: *0 pts*"
        )
        await query.edit_message_text(final_text, reply_markup=build_keyboard(game_id, board), parse_mode="Markdown")
    else:
        # Game jari hai
        await query.edit_message_reply_markup(reply_markup=build_keyboard(game_id, board))
      
