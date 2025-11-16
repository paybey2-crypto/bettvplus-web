from flask import Flask, render_template, request, redirect, jsonify
import stripe
import os
import json
from datetime import datetime, timedelta

app = Flask(__name__)

# STRIPE KEYS – čita iz RENDER environment varijabli
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
PUBLIC_KEY = os.getenv("STRIPE_PUBLIC_KEY")

# “Baza” u JSON datoteci
DATA_FILE = "mac_data.json"

def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

@app.route("/")
def index():
    return render_template("index.html", public_key=PUBLIC_KEY)

@app.route("/create-checkout-session", methods=["POST"])
def create_checkout_session():
    data = request.get_json()
    mac = data.get("mac")
    plan = data.get("plan")

    if plan == "year":
        price = 7.99
        duration_days = 365
    elif plan == "lifetime":
        price = 11.99
        duration_days = 9999
    else:
        return jsonify({"error": "Invalid plan"}), 400

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "eur",
                "product_data": {"name": f"Subscription for {mac}"},
                "unit_amount": int(price * 100),
            },
            "quantity": 1,
        }],
        mode="payment",
        success_url=f"{request.host_url}success?mac={mac}&days={duration_days}",
        cancel_url=f"{request.host_url}",
    )

    return jsonify({"id": session.id})

@app.route("/success")
def success():
    mac = request.args.get("mac")
    days = int(request.args.get("days", 0))

    data = load_data()
    expiry = datetime.now() + timedelta(days=days)

    data[mac] = expiry.strftime("%Y-%m-%d %H:%M:%S")
    save_data(data)

    return render_template("success.html", mac=mac)

@app.route("/admin/panel")
def admin_panel():
    data = load_data()
    return render_template("admin.html", data=data)

@app.route("/api/check", methods=["POST"])
def api_check():
    mac = request.json.get("mac")
    data = load_data()

    if mac in data:
        expiry = datetime.strptime(data[mac], "%Y-%m-%d %H:%M:%S")
        if expiry > datetime.now():
            return jsonify({"status": "active", "expiry": data[mac]})

    return jsonify({"status": "inactive"})
