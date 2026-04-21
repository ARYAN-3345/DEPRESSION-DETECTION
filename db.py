import sqlite3

DB_PATH = "database.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT NOT NULL,
        prediction TEXT,
        score INTEGER,
        type TEXT,
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        details TEXT,
        confidence REAL
    )
    """)

    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_user_email 
    ON results(user_email)
    """)

    conn.commit()
    conn.close()