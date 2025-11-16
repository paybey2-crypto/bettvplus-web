from flask import Flask, render_template, request, redirect, jsonify
import os
import json
from datetime import datetime, timedelta

app = Flask(__name__)

DATABASE_FILE = "mac_db.json"

# ------------------------------
# Load / Save DB
# ------------------------------

def load_db():
    if not os.path.exists(DATABASE_FILE):
        with open(DATABASE_FILE, "w") as f:
            json.dump({}, f)
    with open(DATABASE_FILE, "r") as f:
        return json.load(f)

def save_db(db):
    with open(DATABASE_FILE, "w") as f:
        json.dump(db, f, indent=4)

# ------------------------------
# ROUTES
# ------------------------------

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/activate_mac", methods=["POST"])
def activate_mac():
    mac = request.form.get("mac", "").strip().lower()
    code = request.form.get("code", "").strip()

    if mac == "":
        return jsonify({"status": "error", "message": "Unesite MAC adresu!"})

    db = load_db()

    # MAC već postoji = provjera
    if mac in db:
        return jsonify({"status": "success", "message": "MAC uspješno provjeren!"})

    # Dodajemo novi MAC (bez plaćanja)
    db[mac] = {
        "activated": True,
        "expires": "lifetime"
    }

    save_db(db)

    return jsonify({"status": "success", "message": "MAC aktiviran!"})

# ------------------------------
# Admin Panel
# ------------------------------

@app.route("/admin")
def admin():
    db = load_db()
    return render_template("admin.html", data=db)

@app.route("/admin/add", methods=["POST"])
def admin_add():
    mac = request.form.get("mac", "").strip().lower()
    duration = request.form.get("duration")

    if mac == "":
        return redirect("/admin")

    db = load_db()

    if duration == "1year":
        expires = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")
    else:
        expires = "lifetime"

    db[mac] = {
        "activated": True,
        "expires": expires
    }

    save_db(db)
    return redirect("/admin")

# ------------------------------
# Run App
# ------------------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
