from flask import Flask, request, redirect, render_template, url_for
import os
import sqlite3
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename

app = Flask(__name__)

# ------------------------------------
# BAZA
# ------------------------------------
db = sqlite3.connect("users.db", check_same_thread=False)
db.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mac TEXT,
    pin TEXT,
    dns TEXT,
    active_until TEXT,
    blocked INTEGER
)
""")
db.commit()

# ------------------------------------
# GLAVNA STRANICA
# ------------------------------------
@app.route('/')
def index():
    return "BetTVPlus server radi ✔️"

# ------------------------------------
# ADMIN LOGIN
# ------------------------------------
ADMIN_USER = "BETPLUS-ADMIN-2024"
ADMIN_PASS = "admin123"

@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if request.method == "POST":
        user = request.form.get("username")
        pw = request.form.get("password")

        if user == ADMIN_USER and pw == ADMIN_PASS:
            return redirect("/admin/dashboard")

        return "Pogrešni podaci"

    return """
    <h2>Admin Login</h2>
    <form method='POST'>
        <input name='username' placeholder='Admin user'>
        <input name='password' placeholder='Lozinka' type='password'>
        <button type='submit'>Prijava</button>
    </form>
    """

# ------------------------------------
# ADMIN DASHBOARD
# ------------------------------------
@app.route('/admin/dashboard')
def admin_dashboard():
    users = db.execute("SELECT * FROM users").fetchall()

    html = "<h2>ADMIN PANEL</h2>"
    html += "<a href='/admin/new'>Dodaj korisnika</a><br><br>"

    for u in users:
        html += f"{u[1]} — {u[2]} — aktivan do {u[4]} <br>"

    return html

# ------------------------------------
# FORMA ZA NOVOG KORISNIKA
# ------------------------------------
@app.route('/admin/new')
def admin_new_user():
    return """
    <h2>Novi korisnik</h2>
    <form action='/admin/upload' method='POST' enctype='multipart/form-data'>
        <input name='mac' placeholder='MAC'><br>
        <input name='pin' placeholder='PIN'><br>
        <input name='dns' placeholder='DNS URL'><br>
        <input type='file' name='playlist'><br><br>
        <button type='submit'>Spremi</button>
    </form>
    """

# ------------------------------------
# UPLOAD + SPREMANJE KORISNIKA
# ------------------------------------
@app.route('/admin/upload', methods=['POST'])
def admin_upload():
    mac = request.form.get("mac")
    pin = request.form.get("pin")
    dns = request.form.get("dns")
    file = request.files.get("playlist")

    if not (mac and pin and dns and file):
        return "Nedostaju podaci", 400

    # spremi playlistu
    if not os.path.exists("playlists"):
        os.makedirs("playlists")

    filename = secure_filename(file.filename)
    save_path = os.path.join("playlists", filename)
    file.save(save_path)

    # aktivacija 7 dana
    active_until = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d %H:%M")

    db.execute(
        "INSERT INTO users (mac, pin, dns, active_until, blocked) VALUES (?, ?, ?, ?, ?)",
        (mac, pin, dns, active_until, 0)
    )
    db.commit()

    return redirect("/admin/dashboard")
