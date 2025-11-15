app = Flask(__name__, static_folder='static', template_folder='templates')
# app.py
import os
import sqlite3
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash
import stripe
import requests

# --- CONFIG ---
STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY")
STRIPE_PUBLIC_KEY = os.environ.get("STRIPE_PUBLIC_KEY")
# public domain your site (used for redirects). Example: https://bettvplus-web-xyz.onrender.com
DOMAIN = os.environ.get("DOMAIN", "http://localhost:5000")

if not STRIPE_SECRET_KEY or not STRIPE_PUBLIC_KEY:
    print("Warning: STRIPE keys are not set in environment variables.")

stripe.api_key = STRIPE_SECRET_KEY

DB_PATH = os.environ.get("DB_PATH", "db.sqlite3")

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "change-me-in-prod")


# --- Database helpers ---
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS macs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mac TEXT UNIQUE,
            status TEXT,
            start_date TEXT,
            end_date TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()

def get_mac(mac):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, mac, status, start_date, end_date FROM macs WHERE mac = ?", (mac,))
    row = cur.fetchone()
    conn.close()
    return row

def create_mac(mac, days=7):
    start = datetime.utcnow()
    end = start + timedelta(days=days)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT OR REPLACE INTO macs (mac, status, start_date, end_date, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (mac, "active", start.isoformat(), end.isoformat(), datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()
    return {"mac": mac, "start": start, "end": end}

def update_mac(mac, mode):
    """mode can be 'year' or 'lifetime'"""
    now = datetime.utcnow()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    if mode == "year":
        new_end = now + timedelta(days=365)
        cur.execute("UPDATE macs SET status = ?, end_date = ? WHERE mac = ?", ("active", new_end.isoformat(), mac))
    elif mode == "lifetime":
        # lifetime -> set end_date far in future and status lifetime
        far = now + timedelta(days=36500)
        cur.execute("UPDATE macs SET status = ?, end_date = ? WHERE mac = ?", ("lifetime", far.isoformat(), mac))
    conn.commit()
    conn.close()


# initialize db
init_db()


# --- Routes ---
@app.route("/")
def index():
    # simple front page with MAC + code input
    return render_template("index.html", stripe_public_key=STRIPE_PUBLIC_KEY)


@app.route("/play", methods=["GET"])
def play():
    # This endpoint accepts username/password (or mac+code) and tries to load channels
    username = request.args.get("username")
    password = request.args.get("password")
    mac = request.args.get("mac")  # optional alternative
    # For convenience, allow either username/password or mac
    if mac:
        # If mac exists and active -> show success
        row = get_mac(mac)
        if row:
            # check expiration
            _, _, status, start_date, end_date = row
            if status in ("active", "lifetime"):
                # check end date
                try:
                    end = datetime.fromisoformat(end_date)
                    if end >= datetime.utcnow():
                        return render_template("play.html", message="Učitavanje streama...", m3u=None)
                except Exception:
                    pass
            # expired -> ask to pay
            return render_template("expired.html", mac=mac)
        else:
            # create temp 7-day activation
            create_mac(mac, days=7)
            return render_template("play.html", message="MAC aktiviran 7 dana (free).", m3u=None)

    # If username/password provided, try to fetch playlist from provider
    if username and password:
        # build URL (example format used earlier)
        source_url = f"http://anotv.org:80/get.php?username={username}&password={password}&type=m3u_plus&output=mpegts"
        try:
            resp = requests.get(source_url, timeout=10)
            if resp.status_code == 200 and resp.text:
                # return raw m3u to template or show "loaded"
                m3u_text = resp.text
                return render_template("play.html", message="Učitano", m3u=m3u_text)
            else:
                return render_template("play.html", message=f"Neuspjelo učitavanje - status {resp.status_code}", m3u=None)
        except Exception as e:
            return render_template("play.html", message=f"Greska pri spajanju: {e}", m3u=None)

    return render_template("index.html", stripe_public_key=STRIPE_PUBLIC_KEY)


@app.route("/admin", methods=["GET", "POST"])
def admin():
    # Simple admin login + listing macs (insecure basic but ok for demo)
    ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
    ADMIN_PASS = os.environ.get("ADMIN_PASS", "adminpass")

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username == ADMIN_USER and password == ADMIN_PASS:
            # list macs
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            cur.execute("SELECT mac, status, start_date, end_date FROM macs ORDER BY id DESC")
            rows = cur.fetchall()
            conn.close()
            return render_template("admin.html", rows=rows)
        else:
            return "Pogrešan username ili password!", 401

    return render_template("login.html")


# Stripe checkout creation
@app.route("/create-checkout-session", methods=["POST"])
def create_checkout_session():
    data = request.form
    mac = data.get("mac")
    plan = data.get("plan")  # "year" or "lifetime"
    if not mac or plan not in ("year", "lifetime"):
        return "Neispravni podaci", 400

    # price config: you can create Stripe Price IDs in dashboard and use them here
    # For demo we set amounts directly via line_items (works with payment mode=payment)
    if plan == "year":
        price = 799  # cents -> 7.99 EUR assuming currency=eur (adjust as needed)
    else:
        price = 1199

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'eur',
                    'product_data': {
                        'name': f'Activation {plan} for {mac}',
                    },
                    'unit_amount': price,
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=DOMAIN + '/success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=DOMAIN + '/cancel',
            metadata={"mac": mac, "plan": plan}
        )
        return redirect(session.url, code=303)
    except Exception as e:
        return str(e), 400


@app.route("/success")
def success():
    session_id = request.args.get("session_id")
    if not session_id:
        return "No session", 400
    try:
        sess = stripe.checkout.Session.retrieve(session_id)
        md = sess.get("metadata", {})
        mac = md.get("mac")
        plan = md.get("plan")
        # confirm payment status
        if sess.get("payment_status") == "paid" and mac and plan:
            update_mac(mac, plan)
            return render_template("success.html", mac=mac, plan=plan)
        else:
            return "Payment not confirmed or invalid metadata", 400
    except Exception as e:
        return f"Error retrieving session: {e}", 400


@app.route("/cancel")
def cancel():
    return "Plaćanje otkazano"


# simple route to create mac quickly (for testing)
@app.route("/create-mac", methods=["POST"])
def create_mac_route():
    mac = request.form.get("mac")
    days = int(request.form.get("days", 7))
    if not mac:
        return "Missing mac", 400
    create_mac(mac, days=days)
    return f"Created {mac} for {days} days"


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
