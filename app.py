import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, abort, flash
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(APP_DIR, "data.db")
UPLOAD_FOLDER = os.path.join(APP_DIR, "playlists")
ALLOWED_EXT = {"m3u","txt","json","zip"}

ADMIN_KEY = os.environ.get("ADMIN_KEY", "BETPLUS-ADMIN-2024")
SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-secret")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = SECRET_KEY

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        mac TEXT UNIQUE,
        pin TEXT,
        dns TEXT,
        active_until TEXT,
        blocked INTEGER DEFAULT 0,
        created_at TEXT
    )""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS playlists (
        id INTEGER PRIMARY KEY,
        filename TEXT,
        uploaded_by TEXT,
        uploaded_at TEXT
    )""")
    conn.commit()
    conn.close()

init_db()

# helper
def is_allowed(filename):
    ext = filename.rsplit('.',1)[-1].lower() if '.' in filename else ''
    return ext in ALLOWED_EXT

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/login", methods=["POST"])
def login():
    mac = request.form.get("mac","").strip()
    pin = request.form.get("pin","").strip()
    dns = request.form.get("dns","").strip()
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE mac=?",(mac,))
    user = cur.fetchone()
    if not user:
        # not found -> show simple message (admin can add)
        return f"MAC not found. Submit for activation or contact admin."
    if user["blocked"]:
        return "Account blocked."
    # check PIN
    if user["pin"] != pin:
        return "Wrong PIN."
    # check active
    if user["active_until"]:
        active_until = datetime.fromisoformat(user["active_until"])
        if datetime.utcnow() > active_until:
            return "MAC expired. Please renew/subsribe."
        else:
            return f"OK — access allowed. MAC active until {active_until.isoformat()}"
    else:
        return "MAC not active. Contact admin."

# admin protection helper
def admin_check():
    key = request.args.get("key","")
    if key != ADMIN_KEY:
        abort(404)

@app.route("/admin", methods=["GET","POST"])
def admin_panel():
    admin_check()
    conn = get_db()
    cur = conn.cursor()

    # add user
    if request.method == "POST" and request.form.get("action") == "add_user":
        mac = request.form.get("mac","").strip()
        pin = request.form.get("pin","").strip()
        dns = request.form.get("dns","").strip()
        now = datetime.utcnow().isoformat()
        try:
            cur.execute("INSERT INTO users(mac,pin,dns,created_at) VALUES(?,?,?,?)",(mac,pin,dns,now))
            conn.commit()
            flash("User added.")
        except sqlite3.IntegrityError:
            flash("MAC already exists.")
        return redirect(url_for("admin_panel", key=ADMIN_KEY))

    # upload playlist
    if request.method == "POST" and request.form.get("action") == "upload_playlist":
        f = request.files.get("playlist")
        uploaded_by = request.form.get("uploaded_by","admin")
        if f and is_allowed(f.filename):
            filename = secure_filename(f.filename)
            dest = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            f.save(dest)
            cur.execute("INSERT INTO playlists(filename,uploaded_by,uploaded_at) VALUES(?,?,?)",(filename,uploaded_by,datetime.utcnow().isoformat()))
            conn.commit()
            flash("Playlist uploaded.")
        else:
            flash("Invalid file or extension.")
        return redirect(url_for("admin_panel", key=ADMIN_KEY))

    # actions via query (activate/block/delete/set expiry)
    action = request.args.get("a")
    uid = request.args.get("id")
    if action and uid:
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE id=?",(uid,))
        user = cur.fetchone()
        if not user:
            flash("User not found.")
            return redirect(url_for("admin_panel", key=ADMIN_KEY))
        if action == "activate7":
            until = (datetime.utcnow() + timedelta(days=7)).isoformat()
            cur.execute("UPDATE users SET active_until=? WHERE id=?",(until,uid))
            conn.commit()
            flash("Activated 7 days.")
        elif action == "activate1y":
            until = (datetime.utcnow() + timedelta(days=365)).isoformat()
            cur.execute("UPDATE users SET active_until=? WHERE id=?",(until,uid))
            conn.commit()
            flash("Activated 1 year.")
        elif action == "activatelife":
            until = (datetime.utcnow() + timedelta(days=36500)).isoformat()  # ~100 years
            cur.execute("UPDATE users SET active_until=? WHERE id=?",(until,uid))
            conn.commit()
            flash("Activated lifetime.")
        elif action == "block":
            cur.execute("UPDATE users SET blocked=1 WHERE id=?",(uid,))
            conn.commit()
            flash("Blocked user.")
        elif action == "unblock":
            cur.execute("UPDATE users SET blocked=0 WHERE id=?",(uid,))
            conn.commit()
            flash("Unblocked user.")
        elif action == "delete":
            cur.execute("DELETE FROM users WHERE id=?",(uid,))
            conn.commit()
            flash("Deleted user.")
        return redirect(url_for("admin_panel", key=ADMIN_KEY))

    cur.execute("SELECT * FROM users ORDER BY id DESC")
    users = cur.fetchall()
    cur.execute("SELECT * FROM playlists ORDER BY id DESC")
    playlists = cur.fetchall()
    conn.close()
    return render_template("admin.html", users=users, playlists=playlists, key=ADMIN_KEY)

@app.route("/playlists/<path:filename>")
def serve_playlist(filename):
    # careful: only serve existing playlist files
    if os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], filename)):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)
    abort(404)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
