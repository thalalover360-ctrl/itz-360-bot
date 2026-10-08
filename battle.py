import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import database as db

# active_battles format:
# chat_id: {
#   "p1": {"id": int, "name": str, "hp": 100, "defending": False},
#   "p2": {"id": int, "name": str, "hp": 100, "defending": False},
#   "turn": p1_id,
#   "status": "waiting" | "active"
# }
active_battles = {}

def get_battle_markup(p1_id, p2_id, current_turn):
    buttons = [
        [
            InlineKeyboardButton("🗡️ Attack", callback_data=f"bat_atk_{p1_id}_{p2_id}"),
            InlineKeyboardButton("🛡️ Defend", callback_data=f"bat_def_{p1_id}_{p2_id}"),
            InlineKeyboardButton("🔥 Special Move", callback_data=f"bat_spc_{p1_id}_{p2_id}")
        ]
    ]
    return InlineKeyboardMarkup(buttons)

async def fight_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user
    db.get_or_create_user(user.id, user.first_name)

    if chat_id in active_battles:
        await update.message.reply_text("⚠️ An arena battle is already ongoing in this group!")
        return

    active_battles[chat_id] = {
        "p1": {"id": user.id, "name": user.first_name, "hp": 100, "defending": False},
        "p2": None,
        "turn": user.id,
        "status": "waiting"
    }

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⚔️ Accept Challenge", callback_data=f"bat_join_{user.id}")]
    ])

    await update.message.reply_text(
        f"⚔️ *ARENA DUEL CHALLENGE* ⚔️\n\n"
        f"👤 Challenger: *{user.first_name}*\n"
        f"❤️ Starting HP: *100*\n"
        f"💰 Stakes: *+500 pts / -250 pts*\n\n"
        "Click below to accept the challenge!",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

async def battle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data.split("_")
    action = data[1]
    chat_id = update.effective_chat.id
    user = update.effective_user
    db.get_or_create_user(user.id, user.first_name)

    if chat_id not in active_battles:
        await query.answer("This duel has expired.", show_alert=True)
        return

    battle = active_battles[chat_id]

    # Join Challenge
    if action == "join":
        challenger_id = int(data[2])
        if user.id == challenger_id:
            await query.answer("You cannot fight yourself!", show_alert=True)
            return

        battle["p2"] = {"id": user.id, "name": user.first_name, "hp": 100, "defending": False}
        battle["status"] = "active"

        await query.answer("Challenge accepted!")
        await query.edit_message_text(
            f"⚔️ *THE DUEL HAS BEGUN!* ⚔️\n\n"
            f"👤 {battle['p1']['name']}: 100 HP\n"
            f"👤 {battle['p2']['name']}: 100 HP\n\n"
            f"👉 Turn: *{battle['p1']['name']}*",
            reply_markup=get_battle_markup(battle['p1']['id'], battle['p2']['id'], battle['turn']),
            parse_mode="Markdown"
        )
        return

    if battle["status"] != "active":
        return

    # Check Turn
    if user.id != battle["turn"]:
        await query.answer("Wait for your turn!", show_alert=True)
        return

    current = battle["p1"] if user.id == battle["p1"]["id"] else battle["p2"]
    opponent = battle["p2"] if user.id == battle["p1"]["id"] else battle["p1"]

    action_text = ""
    # Process Moves
    if action == "atk":
        base_dmg = random.randint(18, 28)
        if opponent["defending"]:
            base_dmg = base_dmg // 2
            opponent["defending"] = False
            action_text = f"🗡️ {current['name']} attacked! {opponent['name']} defended and took only `{base_dmg} DMG`."
        else:
            action_text = f"🗡️ {current['name']} struck {opponent['name']} for `{base_dmg} DMG`!"
        opponent["hp"] = max(0, opponent["hp"] - base_dmg)

    elif action == "def":
        current["defending"] = True
        action_text = f"🛡️ {current['name']} took a defensive stance!"

    elif action == "spc":
        if random.random() < 0.35:
            action_text = f"💨 {current['name']}'s Special Move MISSED completely!"
        else:
            dmg = random.randint(35, 50)
            if opponent["defending"]:
                dmg = dmg // 2
                opponent["defending"] = False
            opponent["hp"] = max(0, opponent["hp"] - dmg)
            action_text = f"🔥 CRITICAL HIT! {current['name']} unleashed fury for `{dmg} DMG`!"

    # Check Winner
    if opponent["hp"] <= 0:
        win_score = db.update_score(current["id"], 500)
        lose_score = db.update_score(opponent["id"], -250)
        del active_battles[chat_id]

        await query.edit_message_text(
            f"💀 *KNOCKOUT!* 🏆\n\n"
            f"{action_text}\n\n"
            f"👑 *Winner:* {current['name']} (+500 pts)\n"
            f"🪦 *Defeated:* {opponent['name']} (-250 pts)\n\n"
            f"💰 {current['name']}'s Balance: `{win_score:,} pts`",
            parse_mode="Markdown"
        )
        return

    # Switch Turn
    battle["turn"] = opponent["id"]
    await query.edit_message_text(
        f"⚔️ *ARENA DUEL* ⚔️\n\n"
        f"{action_text}\n\n"
        f"❤️ {battle['p1']['name']}: `{battle['p1']['hp']} HP`\n"
        f"❤️ {battle['p2']['name']}: `{battle['p2']['hp']} HP`\n\n"
        f"👉 Turn: *{opponent['name']}*",
        reply_markup=get_battle_markup(battle['p1']['id'], battle['p2']['id'], battle['turn']),
        parse_mode="Markdown"
    )
  
