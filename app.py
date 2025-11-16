import os
import sqlite3
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import stripe

# Load env vars (Render already sets them)
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "Livnjak1978@@")
STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY")
STRIPE_PUBLIC_KEY = os.environ.get("STRIPE_PUBLIC_KEY")
YEAR_PRICE_ID = os.environ.get("YEAR_PRICE_ID")
LIFETIME_PRICE_ID = os.environ.get("LIFETIME_PRICE_ID")

if not STRIPE_SECRET_KEY or not STRIPE_PUBLIC_KEY:
    print("Warning: STRIPE keys not set in environment.")

stripe.api_key = STRIPE_SECRET_KEY

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "change-me-secret")  # set a real secret

DB = "macs.db"

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS macs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    mac TEXT UNIQUE,
                    status TEXT,
                    expires_at TEXT,
                    created_at TEXT
                )''')
    conn.commit()
    conn.close()

init_db()

def add_mac_to_db(mac, status="Aktiviran", expires_at=None):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    now = datetime.utcnow().isoformat()
    c.execute("INSERT OR REPLACE INTO macs (mac, status, expires_at, created_at) VALUES (?, ?, ?, ?)",
              (mac, status, expires_at, now))
    conn.commit()
    conn.close()

def list_macs():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT mac, status, expires_at FROM macs ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    return rows

def activate_mac(mac, years=None, lifetime=False):
    if lifetime:
        expires_at = "lifetime"
    elif years:
        expires_at = (datetime.utcnow() + timedelta(days=365*years)).isoformat()
    else:
        expires_at = None
    add_mac_to_db(mac, status="Aktiviran", expires_at=expires_at)


@app.route("/")
def index():
    return render_template("index.html", public_key=STRIPE_PUBLIC_KEY)

@app.route("/create-checkout-session", methods=["POST"])
def create_checkout_session():
    data = request.get_json()
    mac = data.get("mac")
    price_type = data.get("price_type")  # "year" or "lifetime"
    if not mac or price_type not in ("year", "lifetime"):
        return jsonify({"error": "invalid request"}), 400

    price_id = YEAR_PRICE_ID if price_type == "year" else LIFETIME_PRICE_ID
    if not price_id:
        return jsonify({"error": "price ID not configured"}), 500

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="payment",
            line_items=[{"price": price_id, "quantity": 1}],
            metadata={"mac": mac, "price_type": price_type},
            success_url=url_for("success", _external=True) + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=url_for("index", _external=True),
        )
        return jsonify({"url": session.url})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/success")
def success():
    session_id = request.args.get("session_id")
    if not session_id:
        flash("No session id", "error")
        return redirect(url_for("index"))
    try:
        s = stripe.checkout.Session.retrieve(session_id)
        paid = s.payment_status == "paid"
        if paid:
            mac = s.metadata.get("mac")
            price_type = s.metadata.get("price_type")
            if price_type == "year":
                activate_mac(mac, years=1)
            else:
                activate_mac(mac, lifetime=True)
            return render_template("success.html", mac=mac)
        else:
            flash("Payment not completed", "error")
            return redirect(url_for("index"))
    except Exception as e:
        flash("Error verifying payment: " + str(e), "error")
        return redirect(url_for("index"))

# Admin login
@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        pwd = request.form.get("password")
        if pwd == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect(url_for("admin_panel"))
        else:
            flash("Pogrešna lozinka", "error")
    return render_template("admin.html", macs=list_macs())

@app.route("/admin/panel", methods=["GET", "POST"])
def admin_panel():
    if not session.get("admin"):
        return redirect(url_for("admin"))
    if request.method == "POST":
        mac = request.form.get("mac")
        term = request.form.get("term")  # "1" or "lifetime"
        if not mac:
            flash("Unesite MAC", "error")
        else:
            if term == "lifetime":
                activate_mac(mac, lifetime=True)
            else:
                activate_mac(mac, years=1)
            flash("MAC dodan", "success")
    return render_template("admin.html", macs=list_macs())

@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
