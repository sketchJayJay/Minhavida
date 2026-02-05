import sqlite3, os
from werkzeug.security import generate_password_hash
from datetime import datetime

SCHEMA = [
"""CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL
);""",
"""CREATE TABLE IF NOT EXISTS settings(
    id INTEGER PRIMARY KEY CHECK (id=1),
    display_name TEXT NOT NULL DEFAULT 'JayJay Neon Quest',
    level_xp INTEGER NOT NULL DEFAULT 100
);""",
"""CREATE TABLE IF NOT EXISTS tasks(
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    kind TEXT NOT NULL DEFAULT 'daily', -- daily/weekly/monthly/once
    due_date TEXT, -- YYYY-MM-DD (once)
    tag TEXT NOT NULL DEFAULT 'geral', -- saude/estudo/trabalho/dinheiro/casa/geral
    xp INTEGER NOT NULL DEFAULT 10,
    created_at TEXT NOT NULL,
    active INTEGER NOT NULL DEFAULT 1
);""",
"""CREATE TABLE IF NOT EXISTS task_logs(
    id INTEGER PRIMARY KEY,
    task_id INTEGER NOT NULL,
    done_date TEXT NOT NULL, -- YYYY-MM-DD (data do clique)
    FOREIGN KEY(task_id) REFERENCES tasks(id)
);""",
"""CREATE TABLE IF NOT EXISTS day_bonus(
    done_date TEXT PRIMARY KEY -- marca que o bônus 5+ já foi aplicado
);""",
"""CREATE TABLE IF NOT EXISTS game_state(
    id INTEGER PRIMARY KEY CHECK (id=1),
    xp INTEGER NOT NULL DEFAULT 0,
    level INTEGER NOT NULL DEFAULT 1,
    streak INTEGER NOT NULL DEFAULT 0,
    last_streak_date TEXT
);""",
"""CREATE TABLE IF NOT EXISTS character(
    id INTEGER PRIMARY KEY CHECK (id=1),
    name TEXT NOT NULL DEFAULT 'JayJay',
    cls TEXT NOT NULL DEFAULT 'Neon Runner',
    strength INTEGER NOT NULL DEFAULT 0,
    focus INTEGER NOT NULL DEFAULT 0,
    discipline INTEGER NOT NULL DEFAULT 0
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
        cur.execute("INSERT OR IGNORE INTO settings(id) VALUES (1)")
        cur.execute("INSERT OR IGNORE INTO game_state(id) VALUES (1)")
        cur.execute("INSERT OR IGNORE INTO character(id) VALUES (1)")
        con.commit()

def ensure_admin(db_path: str):
    with connect(db_path) as con:
        cur = con.cursor()
        cur.execute("SELECT COUNT(*) as c FROM users")
        if cur.fetchone()["c"] == 0:
            cur.execute(
                "INSERT INTO users(username, password_hash, created_at) VALUES (?,?,?)",
                ("admin", generate_password_hash("admin123"), datetime.utcnow().isoformat())
            )
            con.commit()

def ensure_seed_missions(db_path: str):
    # cadastra missões padrão se ainda não existir nenhuma
    missions = [
        # daily
        ("Boot Up: arrumar cama", "daily", None, "casa", 5),
        ("Core Focus: 25 min foco (sem celular)", "daily", None, "estudo", 15),
        ("Body.exe: 20 min caminhada/treino leve", "daily", None, "saude", 15),
        ("Water Protocol: 6 copos de água", "daily", None, "saude", 10),
        ("Inbox Zero Mini: resolver 3 pendências", "daily", None, "trabalho", 10),
        ("Cash Scan: registrar todo gasto do dia", "daily", None, "dinheiro", 10),
        ("Shutdown: planejar 3 metas de amanhã", "daily", None, "trabalho", 5),

        # weekly
        ("Deep Clean: organizar uma área (mesa/quarto/pc)", "weekly", None, "casa", 30),
        ("Skill Upload: aprender 45 min (curso/tutorial)", "weekly", None, "estudo", 35),
        ("Finance Patch: revisar semana e cortar 1 vazamento", "weekly", None, "dinheiro", 40),
        ("Network Call: falar com 1 cliente/contato importante", "weekly", None, "trabalho", 25),

        # monthly
        ("Budget Lock: definir limites por categoria", "monthly", None, "dinheiro", 80),
        ("Savings Vault: guardar qualquer valor", "monthly", None, "dinheiro", 70),
        ("Boss Quest: concluir 1 objetivo grande", "monthly", None, "trabalho", 120),
    ]

    with connect(db_path) as con:
        cur = con.cursor()
        cur.execute("SELECT COUNT(*) as c FROM tasks")
        if cur.fetchone()["c"] == 0:
            now = datetime.utcnow().isoformat()
            for title, kind, due, tag, xp in missions:
                cur.execute(
                    "INSERT INTO tasks(title, kind, due_date, tag, xp, created_at, active) VALUES (?,?,?,?,?,?,1)",
                    (title, kind, due, tag, xp, now)
                )
            con.commit()
