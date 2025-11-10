import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "change_this_secret")

DB_PATH = "database.db"
APK_FILENAME = "BETTVPLUS-PRO.apk"   # stavi apk u static/

# --- DB init ---
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mac TEXT UNIQUE,
            pin TEXT,
            playlist TEXT,
            created_at TEXT
        )
    ''')
    conn.commit()
    conn.close()

def get_device(mac):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id,mac,pin,playlist,created_at FROM devices WHERE mac = ?", (mac,))
    row = c.fetchone()
    conn.close()
    return row

def create_or_update_device(mac, pin):
    now = datetime.utcnow().isoformat()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # try insert, if exists update pin
    try:
        c.execute("INSERT INTO devices (mac,pin,playlist,created_at) VALUES (?,?,?,?)",
                  (mac, pin, "", now))
    except sqlite3.IntegrityError:
        c.execute("UPDATE devices SET pin = ? WHERE mac = ?", (pin, mac))
    conn.commit()
    conn.close()

def save_playlist(mac, playlist_url):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE devices SET playlist = ? WHERE mac = ?", (playlist_url, mac))
    conn.commit()
    conn.close()

init_db()

# --- routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    mac = request.form.get('mac', '').strip().lower()
    pin = request.form.get('pin', '').strip()
    if not mac or not pin:
        flash("Unesi MAC i PIN.", "danger")
        return redirect(url_for('index'))

    device = get_device(mac)
    if device:
        # device = (id, mac, pin, playlist, created_at)
        stored_pin = device[2]
        if stored_pin == pin:
            return redirect(url_for('dashboard', mac=mac))
        else:
            flash("PIN nije točan.", "danger")
            return redirect(url_for('index'))
    else:
        # create device with given pin and empty playlist
        create_or_update_device(mac, pin)
        flash("Novi uređaj je kreiran i PIN spremljen. Sada si prijavljen.", "success")
        return redirect(url_for('dashboard', mac=mac))

@app.route('/dashboard/<mac>', methods=['GET', 'POST'])
def dashboard(mac):
    mac = mac.strip().lower()
    device = get_device(mac)
    if not device:
        flash("MAC nije pronađen. Prijavi se prvo.", "danger")
        return redirect(url_for('index'))

    if request.method == 'POST':
        # spremi playlist
        playlist = request.form.get('playlist', '').strip()
        save_playlist(mac, playlist)
        flash("Playlist je spremljen.", "success")
        return redirect(url_for('dashboard', mac=mac))

    # GET: prikaži dashboard
    playlist = device[3] or ""
    return render_template('dashboard.html', mac=mac, playlist=playlist)

@app.route('/download')
def download_apk():
    static_dir = os.path.join(app.root_path, "static")
    apk_path = os.path.join(static_dir, APK_FILENAME)
    if not os.path.exists(apk_path):
        return "APK datoteka nije pronađena u static/ folderu.", 404
    return send_from_directory(static_dir, APK_FILENAME, as_attachment=True)

# simple admin: view devices (protected by simple key query param)
@app.route('/admin', methods=['GET'])
def admin():
    key = request.args.get('key', '')
    ADMIN_KEY = os.environ.get("ADMIN_KEY", "change_admin_key")
    if key != ADMIN_KEY:
        return "Access denied. Provide ?key=ADMIN_KEY", 403

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT mac, pin, playlist, created_at FROM devices ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    return render_template('admin.html', devices=rows)

if __name__ == '__main__':
    # useful for local debug
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
