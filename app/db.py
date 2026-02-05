import sqlite3
import os
from werkzeug.security import generate_password_hash

SCHEMA = [
"""CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL
);""",
"""CREATE TABLE IF NOT EXISTS settings(
    id INTEGER PRIMARY KEY CHECK (id=1),
    display_name TEXT NOT NULL DEFAULT 'Meu Jogo',
    xp_per_task INTEGER NOT NULL DEFAULT 10,
    level_xp INTEGER NOT NULL DEFAULT 100
);""",
"""CREATE TABLE IF NOT EXISTS tasks(
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    kind TEXT NOT NULL DEFAULT 'daily', -- daily/weekly/monthly/once
    due_date TEXT, -- YYYY-MM-DD (para once)
    created_at TEXT NOT NULL,
    active INTEGER NOT NULL DEFAULT 1
);""",
"""CREATE TABLE IF NOT EXISTS task_logs(
    id INTEGER PRIMARY KEY,
    task_id INTEGER NOT NULL,
    done_date TEXT NOT NULL, -- YYYY-MM-DD
    FOREIGN KEY(task_id) REFERENCES tasks(id)
);""",
"""CREATE TABLE IF NOT EXISTS game_state(
    id INTEGER PRIMARY KEY CHECK (id=1),
    xp INTEGER NOT NULL DEFAULT 0,
    level INTEGER NOT NULL DEFAULT 1,
    streak INTEGER NOT NULL DEFAULT 0,
    last_streak_date TEXT
);""",
"""CREATE TABLE IF NOT EXISTS transactions(
    id INTEGER PRIMARY KEY,
    tdate TEXT NOT NULL, -- YYYY-MM-DD
    ttype TEXT NOT NULL, -- gain/spend
    category TEXT NOT NULL,
    amount REAL NOT NULL,
    note TEXT
);""",
"""CREATE INDEX IF NOT EXISTS idx_task_logs_done_date ON task_logs(done_date);""",
"""CREATE INDEX IF NOT EXISTS idx_tx_tdate ON transactions(tdate);"""
]

def connect(db_path: str):
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    return con

def init_db(db_path: str):
    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
    with connect(db_path) as con:
        cur = con.cursor()
        for stmt in SCHEMA:
            cur.execute(stmt)
        # seed rows
        cur.execute("INSERT OR IGNORE INTO settings(id) VALUES (1)")
        cur.execute("INSERT OR IGNORE INTO game_state(id) VALUES (1)")
        con.commit()

def ensure_admin(db_path: str):
    from datetime import datetime
    with connect(db_path) as con:
        cur = con.cursor()
        cur.execute("SELECT COUNT(*) as c FROM users")
        if cur.fetchone()["c"] == 0:
            cur.execute(
                "INSERT INTO users(username, password_hash, created_at) VALUES (?,?,?)",
                ("admin", generate_password_hash("admin123"), datetime.utcnow().isoformat())
            )
            con.commit()
