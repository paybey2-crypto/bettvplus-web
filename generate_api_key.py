import sqlite3
import secrets
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "database.db"

def create_key(label=""):
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("CREATE TABLE IF NOT EXISTS api_keys (id INTEGER PRIMARY KEY AUTOINCREMENT, key TEXT NOT NULL UNIQUE, label TEXT, created_at TEXT NOT NULL)")
    new_key = secrets.token_urlsafe(32)
    conn.execute("INSERT INTO api_keys (key, label, created_at) VALUES (?, ?, ?)",
                 (new_key, label, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()
    return new_key

if __name__ == "__main__":
    label = input("Label for the key (optional): ").strip()
    key = create_key(label)
    print("NEW API KEY:", key)
