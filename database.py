import sqlite3
from datetime import date

DB_NAME = "game_data.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            score INTEGER DEFAULT 0,
            last_daily TEXT
        )
    """)
    conn.commit()
    conn.close()

def get_or_create_user(user_id, username):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT score FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    if not row:
        c.execute("INSERT INTO users (user_id, username, score) VALUES (?, ?, ?)", (user_id, username, 0))
        conn.commit()
        score = 0
    else:
        # Username update agar user ne Telegram pe naam badal liya ho
        c.execute("UPDATE users SET username = ? WHERE user_id = ?", (username, user_id))
        conn.commit()
        score = row[0]
    conn.close()
    return score

def update_score(user_id, delta):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Ensure user exists pehle
    c.execute("SELECT score FROM users WHERE user_id = ?", (user_id,))
    if not c.fetchone():
        c.execute("INSERT INTO users (user_id, username, score) VALUES (?, ?, ?)", (user_id, "Player", 0))
    
    c.execute("UPDATE users SET score = score + ? WHERE user_id = ?", (delta, user_id))
    conn.commit()
    c.execute("SELECT score FROM users WHERE user_id = ?", (user_id,))
    new_score = c.fetchone()[0]
    conn.close()
    return new_score

def claim_daily_bonus(user_id):
    today = str(date.today())
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT last_daily FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    if row and row[0] == today:
        conn.close()
        return False, "Aapne aaj ka bonus pehle hi claim kar liya hai!"
    
    c.execute("UPDATE users SET score = score + 500, last_daily = ? WHERE user_id = ?", (today, user_id))
    conn.commit()
    c.execute("SELECT score FROM users WHERE user_id = ?", (user_id,))
    total = c.fetchone()[0]
    conn.close()
    return True, total

def get_top_players(limit=10):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT username, score FROM users ORDER BY score DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    return rows
  
