import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import database as db

ACTIVE_FIGHTS = {}

def get_hp_bar(hp, max_hp=100):
    val = max(0, min(hp, max_hp))
    filled = int(val / 10)
    return "🟩" * filled + "🟥" * (10 - filled) + f" ({val}/{max_hp})"

async def maut_fight_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    user = update.effective_user
    args = context.args

    bet = 50
    if args and args[0].isdigit():
        bet = int(args[0])

    db.get_or_create_user(user.id, user.first_name)

    kb = [
        [InlineKeyboardButton(f"⚔️ Fight with Friend (Bet: {bet} Coins)", callback_data=f"mpvp_join_{user.id}_{bet}")],
        [InlineKeyboardButton("🤖 Play vs Computer (Levels)", callback_data=f"mpvp_bot_1")]
    ]
    reply_markup = InlineKeyboardMarkup(kb)

    await msg.reply_text(
        f"💀 *MAUT 360: THE DUEL ARENA* 💀\n\n"
        f"Challenger: *{user.first_name}*\n"
        f"Bet: *{bet} Coins*\n\n"
        f"Friend button daba kar match accept kare, ya computer ke khilaf level complete karo!",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def maut_pvp_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = update.effective_user
    data = query.data.split("_")
    action = data[1]

    # 1. Computer Fight
    if action == "bot":
        level = int(data[2])
        game_id = f"bot_{user.id}"
        ACTIVE_FIGHTS[game_id] = {
            "p1_id": user.id, "p1_name": user.first_name, "p1_hp": 100,
            "p2_id": "bot", "p2_name": f"Level {level} Cyborg", "p2_hp": 80 + (level * 20),
            "level": level, "turn": user.id, "is_bot": True
        }
        await render_battle(query, game_id, f"⚔️ Battle started against *Level {level} Cyborg*!")
        return

    # 2. Friend Join
    if action == "join":
        host_id = int(data[2])
        bet = int(data[3])

        if user.id == host_id:
            await query.answer("Khud se duel nahi lad sakte! Friend ko button dabane do.", show_alert=True)
            return

        game_id = f"pvp_{host_id}_{user.id}"
        host_user = db.get_or_create_user(host_id)
        db.get_or_create_user(user.id, user.first_name)

        ACTIVE_FIGHTS[game_id] = {
            "p1_id": host_id, "p1_name": host_user.get("name", "P1"), "p1_hp": 100,
            "p2_id": user.id, "p2_name": user.first_name, "p2_hp": 100,
            "bet": bet, "turn": host_id, "is_bot": False
        }

        await render_battle(query, game_id, f"🔥 *{user.first_name}* ne challenge accept kar liya! Round 1 Start!")
        return

    # 3. Combat Moves
    if action in ["atk", "def", "crit"]:
        game_id = "_".join(data[2:])
        game = ACTIVE_FIGHTS.get(game_id)
        if not game:
            await query.answer("Match khatam ho chuka hai!", show_alert=True)
            return

        if game["turn"] != user.id:
            await query.answer("Abhi tumhari turn nahi hai!", show_alert=True)
            return

        is_p1 = (user.id == game["p1_id"])
        attacker_name = game["p1_name"] if is_p1 else game["p2_name"]
        defender_key = "p2_hp" if is_p1 else "p1_hp"

        dmg = 0
        log_text = ""
        if action == "atk":
            dmg = random.randint(18, 26)
            log_text = f"👊 *{attacker_name}* ne Punch mara (-{dmg} HP)!"
        elif action == "crit":
            if random.random() < 0.55:
                dmg = random.randint(32, 45)
                log_text = f"💥 *CRITICAL!* *{attacker_name}* ne super kick maari (-{dmg} HP)!"
            else:
                dmg = 0
                log_text = f"💨 *MISS!* *{attacker_name}* ka kick chook gaya!"
        elif action == "def":
            heal = random.randint(12, 20)
            hp_key = "p1_hp" if is_p1 else "p2_hp"
            game[hp_key] = min(100, game[hp_key] + heal)
            log_text = f"🛡️ *{attacker_name}* ne shield banayi (+{heal} HP Heal)!"

        game[defender_key] -= dmg

        if game[defender_key] <= 0:
            winner_name = attacker_name
            winner_id = user.id
            if not game["is_bot"]:
                db.update_score(winner_id, game["bet"])
                loser_id = game["p2_id"] if is_p1 else game["p1_id"]
                db.update_score(loser_id, -game["bet"])
                result_text = f"🏆 *{winner_name} NE MAUT DUEL JEET LIYA!* 🏆\nWinner reward: *+{game['bet']} Coins*!"
            else:
                result_text = f"🏆 *You defeated Level {game['level']}!* Level cleared!"
            del ACTIVE_FIGHTS[game_id]
            await query.edit_message_text(result_text, parse_mode="Markdown")
            return

        if game["is_bot"]:
            bot_dmg = random.randint(12 + game["level"] * 3, 20 + game["level"] * 4)
            game["p1_hp"] -= bot_dmg
            log_text += f"\n🤖 *Cyborg* ne counter-attack kiya (-{bot_dmg} HP)!"
            if game["p1_hp"] <= 0:
                del ACTIVE_FIGHTS[game_id]
                await query.edit_message_text(f"💀 *YOU DIED!* Cyborg Level {game['level']} jeet gaya!", parse_mode="Markdown")
                return
            game["turn"] = user.id
        else:
            game["turn"] = game["p2_id"] if is_p1 else game["p1_id"]

        await render_battle(query, game_id, log_text)

async def render_battle(query, game_id, log):
    game = ACTIVE_FIGHTS[game_id]
    turn_name = game["p1_name"] if game["turn"] == game["p1_id"] else game["p2_name"]

    text = (
        f"🥊 *MAUT 360 COMBAT ARENA*\n\n"
        f"👤 *{game['p1_name']}*: {get_hp_bar(game['p1_hp'])}\n"
        f"👤 *{game['p2_name']}*: {get_hp_bar(game['p2_hp'])}\n\n"
        f"⚡ *Log:* {log}\n"
        f"👉 *Turn:* *{turn_name}* ki baari hai!\n"
    )

    kb = [
        [
            InlineKeyboardButton("👊 Punch", callback_data=f"mpvp_atk_{game_id}"),
            InlineKeyboardButton("💥 Super Kick", callback_data=f"mpvp_crit_{game_id}"),
            InlineKeyboardButton("🛡️ Shield", callback_data=f"mpvp_def_{game_id}")
        ]
    ]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
    
