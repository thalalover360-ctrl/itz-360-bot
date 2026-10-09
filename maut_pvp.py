import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import database as db

# Active battles memory store
pvp_games = {}

async def maut_fight_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat

    if chat.type == "private":
        await update.message.reply_text("⚠️ Ye command sirf Groups me kaam karti hai jahan 2 players lad sakein!")
        return

    wager = 100
    if context.args and len(context.args) > 0:
        try:
            wager = int(context.args[0])
            if wager <= 0:
                await update.message.reply_text("Wager amount 0 se zyada hona chahiye!")
                return
        except ValueError:
            await update.message.reply_text("Sahi format: `/mautfight 100`")
            return

    user_data = db.get_or_create_user(user.id, user.first_name)
    user_coins = user_data.get('score', 0) if isinstance(user_data, dict) else 0

    if user_coins < wager:
        await update.message.reply_text(f"❌ Balance kam hai! Aapke paas sirf {user_coins} coins hain.")
        return

    game_id = f"{chat.id}_{update.message.message_id}"
    pvp_games[game_id] = {
        "chat_id": chat.id,
        "p1_id": user.id,
        "p1_name": user.first_name,
        "p2_id": None,
        "p2_name": None,
        "wager": wager,
        "p1_hp": 100,
        "p2_hp": 100,
        "turn": user.id,
        "status": "waiting",
        "log": f"🥊 {user.first_name} ne arena open kiya! Challenger ka wait ho raha hai..."
    }

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"⚔️ Accept Challenge ({wager} 🪙)", callback_data=f"mpvp_join_{game_id}")]
    ])

    await update.message.reply_text(
        f"🥊 *MAUT 360: ARENA PVP CHALLENGE!* 🥊\n\n"
        f"👤 *Host:* {user.first_name}\n"
        f"💰 *Wager Pool:* {wager * 2} Coins ({wager} each)\n\n"
        f"Arena me utarne ke liye niche button dabayein!",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

def render_fight_screen(game):
    p1_bar = "█" * (max(0, game["p1_hp"]) // 10) + "░" * (10 - (max(0, game["p1_hp"]) // 10))
    p2_bar = "█" * (max(0, game["p2_hp"]) // 10) + "░" * (10 - (max(0, game["p2_hp"]) // 10))
    
    current_attacker = game["p1_name"] if game["turn"] == game["p1_id"] else game["p2_name"]

    text = (
        f"🥊 *MAUT 360: LIVE PVP COMBAT* 🥊\n\n"
        f"🔴 *{game['p1_name']}*: {game['p1_hp']}/100 HP\n`[{p1_bar}]`\n\n"
        f"🔵 *{game['p2_name']}*: {game['p2_hp']}/100 HP\n`[{p2_bar}]`\n\n"
        f"📜 *Battle Action:*\n_{game['log']}_\n\n"
        f"👉 *Turn:* {current_attacker} (Select Move!)"
    )
    return text

def get_combat_buttons(game_id):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("👊 Heavy Punch", callback_data=f"mpvp_act_punch_{game_id}"),
            InlineKeyboardButton("🦵 Roundhouse Kick", callback_data=f"mpvp_act_kick_{game_id}")
        ],
        [
            InlineKeyboardButton("🛡️ Guard / Counter", callback_data=f"mpvp_act_guard_{game_id}"),
            InlineKeyboardButton("⚡ Aura Strike", callback_data=f"mpvp_act_aura_{game_id}")
        ]
    ])

async def maut_pvp_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data or ""
    user = query.from_user

    if data.startswith("mpvp_join_"):
        await query.answer()
        game_id = data.replace("mpvp_join_", "")
        game = pvp_games.get(game_id)

        if not game or game["status"] != "waiting":
            await query.answer("Match expire ho gaya ya pehle hi shuru ho chuka hai!", show_alert=True)
            return

        if user.id == game["p1_id"]:
            await query.answer("Apne khud ke match me nahi lad sakte!", show_alert=True)
            return

        user_data = db.get_or_create_user(user.id, user.first_name)
        coins = user_data.get('score', 0) if isinstance(user_data, dict) else 0

        if coins < game["wager"]:
            await query.answer(f"Coins kam hain! You need {game['wager']} coins.", show_alert=True)
            return

        # Deduct entry fees
        db.update_score(game["p1_id"], -game["wager"])
        db.update_score(user.id, -game["wager"])

        game["p2_id"] = user.id
        game["p2_name"] = user.first_name
        game["status"] = "fighting"
        game["log"] = f"🔥 {user.first_name} arena me ghus gaya! Fight Shuru!"

        await query.edit_message_text(
            render_fight_screen(game),
            reply_markup=get_combat_buttons(game_id),
            parse_mode="Markdown"
        )
        return

    if data.startswith("mpvp_act_"):
        parts = data.split("_")
        move = parts[2]
        game_id = f"{parts[3]}_{parts[4]}"
        game = pvp_games.get(game_id)

        if not game or game["status"] != "fighting":
            await query.answer("Battle expire ho chuki hai!", show_alert=True)
            return

        if user.id not in [game["p1_id"], game["p2_id"]]:
            await query.answer("Aap is match ka hissa nahi hain!", show_alert=True)
            return

        if user.id != game["turn"]:
            await query.answer("Sabr rakhein, abhi aapki turn nahi hai!", show_alert=True)
            return

        await query.answer()

        attacker_name = game["p1_name"] if user.id == game["p1_id"] else game["p2_name"]
        defender_name = game["p2_name"] if user.id == game["p1_id"] else game["p1_name"]

        # Combat Calculation
        dmg = 0
        action_msg = ""
        if move == "punch":
            dmg = random.randint(15, 25)
            action_msg = f"👊 {attacker_name} ne powerful punch mara! (-{dmg} HP)"
        elif move == "kick":
            dmg = random.randint(18, 30)
            if random.random() < 0.2:
                dmg = 0
                action_msg = f"💨 {attacker_name} ka kick miss ho gaya!"
            else:
                action_msg = f"🦵 {attacker_name} ne solid kick connect kiya! (-{dmg} HP)"
        elif move == "guard":
            dmg = random.randint(10, 18)
            action_msg = f"🛡️ {attacker_name} guard karke counter attack mara! (-{dmg} HP)"
        elif move == "aura":
            if random.random() < 0.4:
                dmg = random.randint(35, 45)
                action_msg = f"💥 CRITICAL! {attacker_name} ne AURA BLAST blast mara! (-{dmg} HP)"
            else:
                dmg = 8
                action_msg = f"⚡ {attacker_name} ka aura blast kamzor raha! (-{dmg} HP)"

        # Apply damage
        if user.id == game["p1_id"]:
            game["p2_hp"] = max(0, game["p2_hp"] - dmg)
            game["turn"] = game["p2_id"]
        else:
            game["p1_hp"] = max(0, game["p1_hp"] - dmg)
            game["turn"] = game["p1_id"]

        game["log"] = action_msg

        # Check Knockout
        if game["p1_hp"] <= 0 or game["p2_hp"] <= 0:
            winner_id = game["p1_id"] if game["p2_hp"] <= 0 else game["p2_id"]
            winner_name = game["p1_name"] if game["p2_hp"] <= 0 else game["p2_name"]
            loser_name = game["p2_name"] if game["p2_hp"] <= 0 else game["p1_name"]
            
            pot = game["wager"] * 2
            db.update_score(winner_id, pot)
            db.add_win(winner_id)

            del pvp_games[game_id]

            final_text = (
                f"💀 *K.O. — MAUT 360 CHAMPIONSHIP* 💀\n\n"
                f"👑 *WINNER:* {winner_name}\n"
                f"☠️ *LOSER:* {loser_name}\n\n"
                f"💰 Total Pot: {pot} Coins credited to {winner_name}'s account!"
            )
            await query.edit_message_text(final_text, parse_mode="Markdown")
            return

        await query.edit_message_text(
            render_fight_screen(game),
            reply_markup=get_combat_buttons(game_id),
            parse_mode="Markdown"
        )
        
