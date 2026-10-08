import sqlite3
from datetime import date

DB_NAME = "arcade.db"

def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            name TEXT,
            score INTEGER DEFAULT 0,
            last_daily TEXT
        )
    """)
    conn.commit()
    conn.close()

def get_or_create_user(user_id, name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, name, score, last_daily FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    
    if not row:
        cursor.execute("INSERT INTO users (user_id, name, score, last_daily) VALUES (?, ?, 0, '')", (user_id, name))
        conn.commit()
        data = {"user_id": user_id, "name": name, "score": 0, "last_daily": ""}
    else:
        # Agar user ne apna telegram display name change kiya ho toh update kar dega
        if row[1] != name:
            cursor.execute("UPDATE users SET name = ? WHERE user_id = ?", (name, user_id))
            conn.commit()
        data = {"user_id": row[0], "name": name, "score": row[2], "last_daily": row[3]}
        
    conn.close()
    return data

def update_score(user_id, delta):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET score = MAX(0, score + ?) WHERE user_id = ?", (delta, user_id))
    conn.commit()
    cursor.execute("SELECT score FROM users WHERE user_id = ?", (user_id,))
    new_score = cursor.fetchone()[0]
    conn.close()
    return new_score

def claim_daily(user_id):
    today = str(date.today())
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT last_daily, score FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()

    if row and row[0] == today:
        conn.close()
        return False, row[1]

    cursor.execute("UPDATE users SET score = score + 500, last_daily = ? WHERE user_id = ?", (today, user_id))
    conn.commit()
    cursor.execute("SELECT score FROM users WHERE user_id = ?", (user_id,))
    new_score = cursor.fetchone()[0]
    conn.close()
    return True, new_score

def get_leaderboard(limit=10):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name, score FROM users ORDER BY score DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_user_stats(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name, score FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return None

    # Global Rank count
    cursor.execute("SELECT COUNT(*) + 1 FROM users WHERE score > ?", (row[1],))
    rank = cursor.fetchone()[0]
    conn.close()

    return {
        "name": row[0],
        "score": row[1],
        "rank": rank
    }
    
