import sqlite3

DB_NAME = "arcade.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            name TEXT,
            score INTEGER DEFAULT 100,
            wins INTEGER DEFAULT 0,
            losses INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

# Bot chalu hote hi table ensure karega
init_db()

def get_or_create_user(user_id, name="Player"):
    init_db()
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT user_id, name, score, wins, losses FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    if not row:
        c.execute("INSERT INTO users (user_id, name, score, wins, losses) VALUES (?, ?, 100, 0, 0)", (user_id, name))
        conn.commit()
        row = (user_id, name, 100, 0, 0)
    conn.close()
    return {"user_id": row[0], "name": row[1], "score": row[2], "wins": row[3], "losses": row[4]}

def update_score(user_id, delta):
    init_db()
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE users SET score = MAX(0, score + ?) WHERE user_id = ?", (delta, user_id))
    conn.commit()
    conn.close()
