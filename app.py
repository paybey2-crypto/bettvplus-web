from flask import Flask, request, redirect, render_template
import os
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename

app = Flask(__name__)   # <--- OVO mora biti prije svih @app.route

# ---------------------------
# RUTE
# ---------------------------

@app.route('/admin/upload', methods=['POST'])
def admin_upload():
    mac = request.form.get("mac")
    pin = request.form.get("pin")
    dns = request.form.get("dns")
    file = request.files.get("playlist")

    if not (mac and pin and dns and file):
        return "Missing data", 400

    # spremi playlist
    filename = secure_filename(file.filename)
    save_path = os.path.join("playlists", filename)

    if not os.path.exists("playlists"):
        os.makedirs("playlists")

    file.save(save_path)

    # spremi korisnika (ovisno o tvojoj DB strukturi)
    active_until = datetime.now() + timedelta(days=7)
    db.execute(
        "INSERT INTO users (mac, pin, dns, active_until, blocked) VALUES (?, ?, ?, ?, ?)",
        (mac, pin, dns, active_until, 0)
    )
    db.commit()

    return redirect("/admin?msg=Korisnik+kreiran+i+playlist+uploadan")
