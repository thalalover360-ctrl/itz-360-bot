import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import database as db

# In-memory active PVP battles
active_maut_fights = {}

async def maut_fight_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat

    if chat.type == "private":
        await update.message.reply_text("⚠️ PvP Match sirf group chat me khela ja sakta hai!")
        return

    # Check wager amount (Default 50 coins)
    wager = 50
    if context.args:
        try:
            wager = int(context.args[0])
            if wager <= 0:
                raise ValueError
        except ValueError:
            await update.message.reply_text("⚠️ Valid coin amount likhein! Example: `/mautfight 100`", parse_mode="Markdown")
            return

    # Check challenger balance
    u_data = db.get_or_create_user(user.id, user.first_name)
    user_score = u_data.get("score", 0)
    if user_score < wager:
        await update.message.reply_text(f"❌ Aapke paas sirf {user_score} coins hain! Minimum {wager} coins chahiye.")
        return

    # Match ID
    match_id = f"{chat.id}_{user.id}_{int(update.message.date.timestamp())}"
    active_maut_fights[match_id] = {
        "p1": {"id": user.id, "name": user.first_name, "hp": 100, "move": None},
        "p2": None,
        "wager": wager,
        "round": 1,
        "chat_id": chat.id,
        "status": "waiting"
    }

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"⚔️ Accept Challenge ({wager} Coins)", callback_data=f"mpvp_acc_{match_id}")],
        [InlineKeyboardButton("🚫 Cancel", callback_data=f"mpvp_cnc_{match_id}")]
    ])

    await update.message.reply_text(
        f"🥊 *MAUT 360: PVP COIN DUEL CHALLENGE!* 🥊\n\n"
        f"👤 *Host:* {user.first_name}\n"
        f"💰 *Wager Pot:* {wager * 2} Coins ({wager} each)\n\n"
        "Jo bhi ladna chahta hai, neeche button daba kar accept kare!",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
 async def maut_pvp_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = update.effective_user
    data = query.data

    # Cancel Match
    if data.startswith("mpvp_cnc_"):
        match_id = data.replace("mpvp_cnc_", "")
        match = active_maut_fights.get(match_id)
        if not match:
            await query.answer("Match expire ho chuka hai!", show_alert=True)
            return
        if user.id != match["p1"]["id"]:
            await query.answer("Sirf host is match ko cancel kar sakta hai!", show_alert=True)
            return
        active_maut_fights.pop(match_id, None)
        await query.edit_message_text("🚫 Challenge cancel kar diya gaya.")
        return

    # Accept Match
    if data.startswith("mpvp_acc_"):
        match_id = data.replace("mpvp_acc_", "")
        match = active_maut_fights.get(match_id)
        if not match or match["status"] != "waiting":
            await query.answer("Match already shuru ho chuka hai ya expire ho gaya!", show_alert=True)
            return

        if user.id == match["p1"]["id"]:
            await query.answer("Khud ka challenge khud accept nahi kar sakte!", show_alert=True)
            return

        u_data = db.get_or_create_user(user.id, user.first_name)
        if u_data.get("score", 0) < match["wager"]:
            await query.answer(f"Aapke paas kam se kam {match['wager']} coins hone chahiye!", show_alert=True)
            return

        # Deduct wager coins from both players
        wager = match["wager"]
        db.update_score(match["p1"]["id"], -wager)
        db.update_score(user.id, -wager)

        match["p2"] = {"id": user.id, "name": user.first_name, "hp": 100, "move": None}
        match["status"] = "fighting"

        await query.answer("Match accepted! Fight shuru!")
        await send_battle_card(query, match_id)
        return

    # Combat Move Selected
    if data.startswith("mpvp_mv_"):
        _, _, move, match_id = data.split("_", 3)
        match = active_maut_fights.get(match_id)
        if not match or match["status"] != "fighting":
            await query.answer("Match active nahi hai!", show_alert=True)
            return

        p1, p2 = match["p1"], match["p2"]
        if user.id not in (p1["id"], p2["id"]):
            await query.answer("Aap is battle ka hissa nahi hain!", show_alert=True)
            return

        current_player = p1 if user.id == p1["id"] else p2
        if current_player["move"] is not None:
            await query.answer("Aap pehle hi move choose kar chuke hain! Dusre player ka wait karein.", show_alert=True)
            return

        current_player["move"] = move
        await query.answer(f"Aapne {move.upper()} choose kiya!")

        # Both picked their moves -> Resolve Round
        if p1["move"] and p2["move"]:
            await resolve_round(query, match_id)

async def send_battle_card(query, match_id):
    match = active_maut_fights[match_id]
    p1, p2 = match["p1"], match["p2"]

    text = (
        f"🥊 *MAUT 360: ROUND {match['round']}* 🥊\n\n"
        f"🔴 *{p1['name']}:* {p1['hp']}/100 HP\n"
        f"🔵 *{p2['name']}:* {p2['hp']}/100 HP\n"
        f"💰 *Total Pot:* {match['wager'] * 2} Coins\n\n"
        "⚡ Dono fighters apna secret move select karein:"
    )

    kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("👊 Punch", callback_data=f"mpvp_mv_punch_{match_id}"),
            InlineKeyboardButton("🦵 Kick", callback_data=f"mpvp_mv_kick_{match_id}")
        ],
        [
            InlineKeyboardButton("🛡️ Aura Guard", callback_data=f"mpvp_mv_guard_{match_id}"),
            InlineKeyboardButton("⚡ Ulti Strike", callback_data=f"mpvp_mv_ulti_{match_id}")
        ]
    ])

    await query.edit_message_text(text, reply_markup=kb, parse_mode="Markdown")

async def resolve_round(query, match_id):
    match = active_maut_fights.get(match_id)
    if not match:
        return

    p1, p2 = match["p1"], match["p2"]
    m1, m2 = p1["move"], p2["move"]

    # Damage Rules
    dmg_table = {"punch": 20, "kick": 25, "guard": 0, "ulti": 35}
    p1_dmg = dmg_table.get(m1, 15)
    p2_dmg = dmg_table.get(m2, 15)

    # Counters: Guard absorbs damage
    if m1 == "guard" and m2 != "ulti":
        p1_dmg_taken = 0
        p2_dmg_taken = 10  # Counter-attack
    elif m2 == "guard" and m1 != "ulti":
        p2_dmg_taken = 0
        p1_dmg_taken = 10
    else:
        p1_dmg_taken = p2_dmg
        p2_dmg_taken = p1_dmg

    # Ulti Clash Risk: random whiff chance
    if m1 == "ulti" and random.random() < 0.25:
        p2_dmg_taken = 0
    if m2 == "ulti" and random.random() < 0.25:
        p1_dmg_taken = 0

    p1["hp"] = max(0, p1["hp"] - p1_dmg_taken)
    p2["hp"] = max(0, p2["hp"] - p2_dmg_taken)

    round_log = (
        f"⚔️ *ROUND {match['round']} RESULT:*\n"
        f"• {p1['name']} ne chala *{m1.upper()}*! (Damage dealt: {p2_dmg_taken})\n"
        f"• {p2['name']} ne chala *{m2.upper()}*! (Damage dealt: {p1_dmg_taken})\n\n"
    )

    # Check for Winner
    if p1["hp"] <= 0 or p2["hp"] <= 0:
        pot = match["wager"] * 2
        if p1["hp"] <= 0 and p2["hp"] <= 0:
            # Draw: Refund wager
            db.update_score(p1["id"], match["wager"])
            db.update_score(p2["id"], match["wager"])
            result_text = round_log + f"🤝 *DOUBLE KNOCKOUT! DRAW!*\nDono ko unke {match['wager']} coins wapas mil gaye."
        elif p1["hp"] > 0:
            db.update_score(p1["id"], pot)
            db.update_wins(p1["id"])
            result_text = round_log + f"🏆 *{p1['name']} WINS THE MATCH!*\n💰 Pot prize: *+{pot} Coins* wallet me add ho gaye! 🪙"
        else:
            db.update_score(p2["id"], pot)
            db.update_wins(p2["id"])
            result_text = round_log + f"🏆 *{p2['name']} WINS THE MATCH!*\n💰 Pot prize: *+{pot} Coins* wallet me add ho gaye! 🪙"

        active_maut_fights.pop(match_id, None)
        await query.edit_message_text(result_text, parse_mode="Markdown")
        return

    # Reset for next round
    p1["move"] = None
    p2["move"] = None
    match["round"] += 1

    kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("👊 Punch", callback_data=f"mpvp_mv_punch_{match_id}"),
            InlineKeyboardButton("🦵 Kick", callback_data=f"mpvp_mv_kick_{match_id}")
        ],
        [
            InlineKeyboardButton("🛡️ Aura Guard", callback_data=f"mpvp_mv_guard_{match_id}"),
            InlineKeyboardButton("⚡ Ulti Strike", callback_data=f"mpvp_mv_ulti_{match_id}")
        ]
    ])

    next_text = (
        f"{round_log}"
        f"🔴 *{p1['name']}:* {p1['hp']}/100 HP\n"
        f"🔵 *{p2['name']}:* {p2['hp']}/100 HP\n\n"
        f"⚡ *ROUND {match['round']}!* Agla move select karein:"
    )

    await query.edit_message_text(next_text, reply_markup=kb, parse_mode="Markdown")
  
