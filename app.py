from flask import Flask, render_template, request, redirect, url_for, jsonify
from datetime import datetime, timedelta
import json
import os

app = Flask(__name__, static_folder='static', template_folder='templates')

DATA_FILE = "mac_data.json"


# -----------------------------
# Helper functions
# -----------------------------
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


# -----------------------------
# INDEX PAGE
# -----------------------------
@app.route("/")
def index():
    return render_template("index.html")


# -----------------------------
# LOGIN (dummy primjer)
# -----------------------------
@app.route("/play", methods=["GET"])
def play():
    username = request.args.get("username")
    password = request.args.get("password")

    # Ovo je samo primjer!
    if username == "admin" and password == "admin":
        return "Login OK — ovdje ide tvoja IPTV stranica."

    return "Pogrešan username ili password."


# -----------------------------
# MAC CHECK / ACTIVATION
# -----------------------------
@app.route("/mac", methods=["GET"])
def mac_check():
    mac = request.args.get("mac")
    if not mac:
        return "MAC adresa nije unesena."

    data = load_data()

    # Ako MAC nije u bazi → aktiviramo 7 dana BESPLATNO
    if mac not in data:
        expiry = datetime.now() + timedelta(days=7)
        data[mac] = expiry.strftime("%Y-%m-%d %H:%M:%S")
        save_data(data)
        return f"MAC aktiviran 7 dana do: {data[mac]}"

    # Ako je MAC već aktiviran → provjera isteka
    expiry = datetime.strptime(data[mac], "%Y-%m-%d %H:%M:%S")

    if datetime.now() > expiry:
        # MAC istekao → uputi korisnika na naplatu
        return redirect("https://tvoj-stripe-link.com")  # OVDJE UBACI STRIPE LINK

    # MAC još vrijedi
    return f"MAC važi do: {data[mac]}"


# -----------------------------
# ADMIN PANEL (dummy)
# -----------------------------
@app.route("/admin")
def admin():
    data = load_data()
    return jsonify(data)


# -----------------------------
# RUN LOCAL
# -----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
