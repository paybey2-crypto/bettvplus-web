
import os
import sqlite3
import secrets
from datetime import datetime
from flask import Flask, request, render_template, redirect, url_for, send_from_directory, jsonify
from werkzeug.utils import secure_filename
from pathlib import Path

# KONFIG
APP_DIR = Path(__file__).parent
UPLOAD_FOLDER = APP_DIR / "uploads"
DB_PATH = APP_DIR / "database.db"
ALLOWED_EXTENSIONS = {"m3u", "m3u8"}
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "promijeni_admin_lozinku")  # za produkciju postavi env var

# Inicijalizacija aplikacije
app = Flask(__name__, static_folder="static", template_folder="templates")
app.config["UPLOAD_FOLDER"] = str(UPLOAD_FOLDER)
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# --- Baza podataka ---
def get_db_connection():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute("CREATE TABLE IF NOT EXISTS activations (id INTEGER PRIMARY KEY AUTOINCREMENT, mac TEXT NOT NULL, filename TEXT NOT NULL, created_at TEXT NOT NULL)")
    conn.execute("CREATE TABLE IF NOT EXISTS api_keys (id INTEGER PRIMARY KEY AUTOINCREMENT, key TEXT NOT NULL UNIQUE, label TEXT, created_at TEXT NOT NULL)")
    conn.commit()
    conn.close()

# --- Util funkcije ---
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_api_key(key):
    if not key:
        return False
    conn = get_db_connection()
    r = conn.execute("SELECT * FROM api_keys WHERE key = ?", (key,)).fetchone()
    conn.close()
    return r is not None

# --- Web rute ---
@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/activate", methods=["POST"])
def activate():
    mac = request.form.get("mac", "").strip()
    file = request.files.get("playlist")

    if not mac:
        return "MAC adresa je obavezna.", 400

    if not file or file.filename == "":
        return "Playlist (.m3u/.m3u8) je obavezan.", 400

    if not allowed_file(file.filename):
        return "Neispravan format fajla. Dozvoljeno: .m3u, .m3u8", 400

    safe_name = secure_filename(f"{mac}_{file.filename}")
    save_path = Path(app.config["UPLOAD_FOLDER"]) / safe_name
    file.save(str(save_path))

    # upiši u bazu
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO activations (mac, filename, created_at) VALUES (?, ?, ?)",
        (mac, safe_name, datetime.utcnow().isoformat())
    )
    conn.commit()
    conn.close()

    return render_template("index.html", success=f"MAC {mac} je aktiviran. Playlista spremljena kao {safe_name}.")

@app.route("/activations", methods=["GET"])
def activations():
    conn = get_db_connection()
    rows = conn.execute("SELECT mac, filename, created_at FROM activations ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("activations.html", rows=rows)

# --- API endpointi za aplikaciju ---
@app.route("/api/check_mac/<mac>", methods=["GET"])
def api_check_mac(mac):
    api_key = request.args.get("api_key", "")
    if not validate_api_key(api_key):
        return jsonify({"error": "invalid_api_key"}), 401

    conn = get_db_connection()
    row = conn.execute(
        "SELECT mac, filename, created_at FROM activations WHERE mac = ? ORDER BY id DESC LIMIT 1",
        (mac,)
    ).fetchone()
    conn.close()
    if not row:
        return jsonify({"status": "not_found"}), 404

    return jsonify({
        "status": "activated",
        "mac": row["mac"],
        "filename": row["filename"],
        "created_at": row["created_at"]
    })

@app.route("/api/get_playlist/<mac>", methods=["GET"])
def api_get_playlist(mac):
    api_key = request.args.get("api_key", "")
    if not validate_api_key(api_key):
        return jsonify({"error": "invalid_api_key"}), 401

    conn = get_db_connection()
    row = conn.execute(
        "SELECT filename FROM activations WHERE mac = ? ORDER BY id DESC LIMIT 1",
        (mac,)
    ).fetchone()
    conn.close()
    if not row:
        return jsonify({"error": "not_found"}), 404

    filename = row["filename"]
    folder = Path(app.config["UPLOAD_FOLDER"])
    return send_from_directory(directory=str(folder), path=filename, as_attachment=False)

# --- Admin endpoint za izradu ključa (zaštićen ADMIN_PASSWORD env varom) ---
@app.route("/admin/create_key", methods=["POST"])
def admin_create_key():
    pwd = request.form.get("admin_password", "")
    label = request.form.get("label", "").strip()
    if pwd != ADMIN_PASSWORD:
        return "Netočna admin lozinka.", 403

    new_key = secrets.token_urlsafe(32)
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO api_keys (key, label, created_at) VALUES (?, ?, ?)",
        (new_key, label, datetime.utcnow().isoformat())
    )
    conn.commit()
    conn.close()
    return jsonify({"api_key": new_key, "label": label})

# --- Pokretanje ---
if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
