from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import datetime, timedelta
import os

app = Flask(__name__)

DB = "database.db"

# --- Kreiranje baze ---
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS devices (
        mac TEXT PRIMARY KEY,
        expires TEXT,
        playlist TEXT
    )""")
    conn.commit()
    conn.close()

init_db()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/login", methods=["POST"])
def login():
    mac = request.form["mac"]

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT expires FROM devices WHERE mac=?", (mac,))
    row = c.fetchone()
    conn.close()

    status = row[0] if row else None
    return render_template("dashboard.html", mac=mac, status=status)


@app.route("/activate", methods=["POST"])
def activate():
    mac = request.form["mac"]
    type = request.form["type"]

    if type == "trial":
        expires = datetime.now() + timedelta(days=7)
    elif type == "year":
        expires = datetime.now() + timedelta(days=365)
    else:
        expires = "LIFETIME"

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO devices (mac, expires) VALUES (?, ?)",
              (mac, str(expires)))
    conn.commit()
    conn.close()

    return redirect("/login_success?mac=" + mac)


@app.route("/upload", methods=["POST"])
def upload():
    mac = request.form["mac"]
    file = request.files["playlist"]

    filename = mac + "_playlist.m3u"
    filepath = os.path.join("static", filename)
    file.save(filepath)

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("UPDATE devices SET playlist=? WHERE mac=?", (filename, mac))
    conn.commit()
    conn.close()

    return redirect("/login_success?mac=" + mac)


@app.route("/login_success")
def reload_dashboard():
    mac = request.args.get("mac")

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT expires FROM devices WHERE mac=?", (mac,))
    row = c.fetchone()
    conn.close()

    status = row[0] if row else None

    return render_template("dashboard.html", mac=mac, status=status)


if __name__ == "__main__":
    app.run()
