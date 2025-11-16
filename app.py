from flask import Flask, render_template, request, redirect, url_for, jsonify
import stripe
import sqlite3
import os
from datetime import datetime, timedelta

app = Flask(__name__)

# Stripe ključevi iz Render varijabli
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")
PUBLIC_KEY = os.environ.get("STRIPE_PUBLIC_KEY")

# Stripe cijene
PRICE_1_YEAR = "price_1STQ3XFZy9W3RRoZhswoUF5R"
PRICE_LIFETIME = "price_1STurmFZy9W3RRoZVZ0RSLAX"


# ─────────────────────────────────────────────
# DB SETUP
# ─────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect("macs.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS macs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mac TEXT UNIQUE,
            status TEXT,
            expires TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()


# ─────────────────────────────────────────────
# HOME PAGE
# ─────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")


# ─────────────────────────────────────────────
# ADMIN PANEL
# ─────────────────────────────────────────────
@app.route("/admin")
def admin():
    conn = sqlite3.connect("macs.db")
    c = conn.cursor()
    c.execute("SELECT mac, status, expires FROM macs")
    macs = c.fetchall()
    conn.close()
    return render_template("admin.html", macs=macs)


# ─────────────────────────────────────────────
# ADMIN → ADD MAC MANUALLY
# ─────────────────────────────────────────────
@app.route("/add_mac", methods=["POST"])
def add_mac():
    mac = request.form.get("mac")
    sub = request.form.get("subscription")

    if sub == "1_year":
        expires = datetime.now() + timedelta(days=365)
    else:
        expires = "lifetime"

    conn = sqlite3.connect("macs.db")
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO macs (mac, status, expires) VALUES (?, ?, ?)",
              (mac, "Aktiviran", expires if sub == "1_year" else "lifetime"))
    conn.commit()
    conn.close()

    return redirect(url_for("admin"))


# ─────────────────────────────────────────────
# CREATE CHECKOUT SESSION
# ─────────────────────────────────────────────
@app.route("/create-checkout-session", methods=["POST"])
def create_checkout():
    mac = request.form.get("mac")
    plan = request.form.get("plan")  # "1_year" ili "lifetime"

    price_id = PRICE_1_YEAR if plan == "1_year" else PRICE_LIFETIME

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{"price": price_id, "quantity": 1}],
        mode="payment",
        success_url=request.host_url + "success?mac=" + mac + "&plan=" + plan,
        cancel_url=request.host_url + "cancel",
    )

    return redirect(session.url, code=303)


# ─────────────────────────────────────────────
# PAYMENT SUCCESS → ACTIVATE MAC
# ─────────────────────────────────────────────
@app.route("/success")
def success():
    mac = request.args.get("mac")
    plan = request.args.get("plan")

    if plan == "1_year":
        expires = datetime.now() + timedelta(days=365)
    else:
        expires = "lifetime"

    conn = sqlite3.connect("macs.db")
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO macs (mac, status, expires) VALUES (?, ?, ?)",
              (mac, "Aktiviran", expires if plan == "1_year" else "lifetime"))
    conn.commit()
    conn.close()

    return "Uplata uspješna! MAC je aktiviran."


@app.route("/cancel")
def cancel():
    return "Plaćanje otkazano."


# ─────────────────────────────────────────────
# API → provjera MAC
# ─────────────────────────────────────────────
@app.route("/check_mac", methods=["POST"])
def check_mac():
    data = request.json
    mac = data.get("mac")

    conn = sqlite3.connect("macs.db")
    c = conn.cursor()
    c.execute("SELECT status, expires FROM macs WHERE mac = ?", (mac,))
    result = c.fetchone()
    conn.close()

    if not result:
        return jsonify({"status": "not_found"})

    status, expires = result

    if expires != "lifetime":
        if datetime.now() > datetime.fromisoformat(expires):
            return jsonify({"status": "expired"})

    return jsonify({"status": "active", "expires": expires})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
