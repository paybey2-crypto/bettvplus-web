from flask import Flask, request, render_template, redirect, send_from_directory
import os
import sqlite3
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename

app = Flask(__name__)

# ---------------------------
#  DB INIT
# ---------------------------

def get_db():
    conn = sqlite3.connect("users.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mac TEXT UNIQUE,
            pin TEXT,
            dns TEXT,
            playlist TEXT,
            active_until TEXT,
            blocked INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ---------------------------
#  INDEX / LOGIN
# ---------------------------

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods=["POST"])
def login():
    mac = request.form.get("mac")
    key = request.form.get("device_key")

    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE mac=? AND pin=?", (mac, key)
    ).fetchone()

    if not user:
        return "Invalid MAC or Device Key"

    if user["blocked"] == 1:
        return "This device is BLOCKED."

    if datetime.now() > datetime.fromisoformat(user["active_until"]):
        return "Your subscription expired."

    return f"Welcome! DNS: {user['dns']}"

# ---------------------------
#  ADMIN PANEL (hidden url)
# ---------------------------

ADMIN_URL = "/admin-LIVNJAK1978"

@app.route(ADMIN_URL)
def admin_home():
    conn = get_db()
    users = conn.execute("SELECT * FROM users ORDER BY id DESC").fetchall()
    return render_template("admin.html", users=users, admin_url=ADMIN_URL)

# ---------------------------
#  ADMIN – CREATE USER
# ---------------------------

@app.route(f"{ADMIN_URL}/create", methods=["POST"])
def admin_create():
    mac = request.form.get("mac")
    pin = request.form.get("pin")
    dns = request.form.get("dns")
    duration = request.form.get("duration")
    file = request.files.get("playlist")

    if not (mac and pin and dns and duration and file):
        return "Missing data", 400

    filename = secure_filename(file.filename)

    if not os.path.exists("playlists"):
        os.makedirs("playlists")

    save_path = os.path.join("playlists", filename)
    file.save(save_path)

    if duration == "7":
        active_until = datetime.now() + timedelta(days=7)
    elif duration == "30":
        active_until = datetime.now() + timedelta(days=30)
    elif duration == "365":
        active_until = datetime.now() + timedelta(days=365)
    else:
        active_until = datetime.now() + timedelta(days=9999)  # lifetime

    conn = get_db()
    conn.execute("""
        INSERT OR REPLACE INTO users (mac, pin, dns, playlist, active_until, blocked)
        VALUES (?, ?, ?, ?, ?, 0)
    """, (mac, pin, dns, filename, active_until.isoformat()))
    conn.commit()

    return redirect(ADMIN_URL)

# ---------------------------
#  ADMIN – DELETE USER
# ---------------------------

@app.route(f"{ADMIN_URL}/delete/<int:user_id>")
def delete_user(user_id):
    conn = get_db()
    conn.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    return redirect(ADMIN_URL)

# ---------------------------
#  ADMIN – BLOCK / UNBLOCK
# ---------------------------

@app.route(f"{ADMIN_URL}/block/<int:user_id>")
def block_user(user_id):
    conn = get_db()
    conn.execute("UPDATE users SET blocked=1 WHERE id=?", (user_id,))
    conn.commit()
    return redirect(ADMIN_URL)

@app.route(f"{ADMIN_URL}/unblock/<int:user_id>")
def unblock_user(user_id):
    conn = get_db()
    conn.execute("UPDATE users SET blocked=0 WHERE id=?", (user_id,))
    conn.commit()
    return redirect(ADMIN_URL)

# ---------------------------
#  SERVE PLAYLISTS
# ---------------------------

@app.route("/playlist/<path:name>")
def play(name):
    return send_from_directory("playlists", name)

# ---------------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
