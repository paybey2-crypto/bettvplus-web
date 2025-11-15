from flask import Flask, request, redirect, render_template, session, abort
import os
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "BETTVPLUS_SECRET_2024"   # obavezno za session login


# --------------------------
#  TAJNI ADMIN LOGIN URL
# --------------------------

ADMIN_URL = "/admin-LIVNJAK1978"
ADMIN_USER = "admin"
ADMIN_PASS = "Livnjak1978@@"



# LOGIN STRANICA
@app.route(ADMIN_URL, methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        user = request.form.get("user")
        pw = request.form.get("pw")

        if user == ADMIN_USER and pw == ADMIN_PASS:
            session["admin"] = True
            return redirect("/admin-panel")

        return render_template("admin_login.html", error="Pogrešni podaci!")

    return render_template("admin_login.html")



# --------------------------
# PRAVI ADMIN PANEL
# --------------------------

@app.route("/admin-panel")
def admin_panel():
    if not session.get("admin"):
        return abort(403)

    # učitaj sve korisnike iz baze
    users = db.execute("SELECT * FROM users").fetchall()

    return render_template("admin_panel.html", users=users)



# --------------------------
# UPLOAD PLAYLIST + USER
# --------------------------

@app.route("/upload-user", methods=['POST'])
def upload_user():
    if not session.get("admin"):
        return abort(403)

    mac = request.form.get("mac")
    pin = request.form.get("pin")
    dns = request.form.get("dns")
    file = request.files.get("playlist")

    if not (mac and pin and dns and file):
        return "Missing data", 400

    # spremi playlist
    filename = secure_filename(file.filename)

    if not os.path.exists("playlists"):
        os.makedirs("playlists")

    file.save(os.path.join("playlists", filename))

    # dodaj korisnika u DB
    active_until = datetime.now() + timedelta(days=7)

    db.execute(
        "INSERT INTO users (mac, pin, dns, active_until, blocked) VALUES (?, ?, ?, ?, ?)",
        (mac, pin, dns, active_until, 0)
    )
    db.commit()

    return redirect("/admin-panel?msg=OK")
