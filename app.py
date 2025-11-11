
from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory, flash
import json
import os

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "change-me-to-secret")

USERS_FILE = "users.json"

def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_users(data):
    with open(USERS_FILE, "w") as f:
        json.dump(data, f, indent=2)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        mac = (request.form.get("mac") or "").strip()
        pin = (request.form.get("pin") or "").strip()
        dns = (request.form.get("dns") or "").strip()

        if not mac or not pin or not dns:
            flash("Ispunite sva polja: MAC, PIN i DNS URL.", "danger")
            return render_template("index.html", mac=mac, dns=dns)

        users = load_users()
        # users structure: { "59:d9:...": { "pin":"943169", "blocked": false } }
        u = users.get(mac.lower())
        if not u:
            flash("MAC adresa nije registrirana.", "danger")
            return render_template("index.html", mac=mac, dns=dns)

        if u.get("blocked"):
            flash("Račun je blokiran.", "danger")
            return render_template("index.html", mac=mac, dns=dns)

        if u.get("pin") != pin:
            flash("PIN nije ispravan.", "danger")
            return render_template("index.html", mac=mac, dns=dns)

        # uspješna prijava
        session["mac"] = mac.lower()
        session["dns"] = dns
        return redirect(url_for("player"))

    return render_template("index.html")

@app.route("/player")
def player():
    mac = session.get("mac")
    dns = session.get("dns")
    if not mac or not dns:
        flash("Niste prijavljeni.", "danger")
        return redirect(url_for("index"))
    return render_template("player.html", mac=mac, dns=dns)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

# download APK (ako je u static)
@app.route("/download")
def download_apk():
    apk_name = "BETTVPLUS-PRO.apk"
    static_folder = os.path.join(app.root_path, "static")
    apk_path = os.path.join(static_folder, apk_name)
    if not os.path.exists(apk_path):
        return "APK nije pronađen.", 404
    return send_from_directory(static_folder, apk_name, as_attachment=True)

# helper for quick testing: add user (not for production)
@app.route("/_admin_add_user", methods=["POST"])
def admin_add_user():
    # ovo je namijenjeno samo za brzo testiranje lokalno
    mac = (request.form.get("mac") or "").strip().lower()
    pin = (request.form.get("pin") or "").strip()
    if not mac or not pin:
        return "Missing", 400
    users = load_users()
    users[mac] = {"pin": pin, "blocked": False}
    save_users(users)
    return "OK", 200

if __name__ == "__main__":
    # debug=True samo lokalno
    app.run(host="0.0.0.0", port=5000, debug=True)
