import sqlite3

def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS activations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    mac TEXT UNIQUE,
                    device_key TEXT,
                    playlist TEXT,
                    trial_start TEXT,
                    paid_until TEXT,
                    paid_type TEXT
                )''')
    conn.commit()
    conn.close()

init_db()
