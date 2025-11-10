import os
import sqlite3
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash
import stripe

# Load stripe keys from environment
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_PUBLIC_KEY = os.getenv("STRIPE_PUBLIC_KEY")

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", "supersecretdev")  # set real secret in env on Render

DB_PATH = "database.db"

# Prices in cents (EUR)
PRICE_LIFETIME_CENTS = 1177   # €11.77
PRICE_YEARLY_CENTS = 777      # €7.77
CURRENCY = "eur"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS activations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mac TEXT UNIQUE,
        device_key TEXT,
        playlist TEXT,
        trial_start TEXT,
        paid_until TEXT,
        paid_type TEXT
    )
    """)
    conn.commit()
    conn.close()

def get_activation(mac):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, mac, device_key, playlist, trial_start, paid_until, paid_type FROM activations WHERE mac = ?", (mac,))
    row = c.fetchone()
    conn.close()
    return row

def create_activation(mac, device_key):
    now = datetime.utcnow()
    trial_end = now + timedelta(days=7)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT OR IGNORE INTO activations (mac, device_key, playlist, trial_start, paid_until, paid_type)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (mac, device_key, "", now.isoformat(), (trial_end).isoformat(), "trial"))
    conn.commit()
    conn.close()

def update_activation_payment(mac, paid_until, paid_type):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE activations SET paid_until = ?, paid_type = ? WHERE mac = ?", (paid_until.isoformat(), paid_type, mac))
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return render_template("login.html")

@app.route('/login', methods=['POST'])
def login():
    mac = request.form.get('mac', '').strip()
    device_key = request.form.get('device_key', '').strip()

    if not mac or not device_key:
        flash("Unesite MAC i Device Key.", "warning")
        return redirect(url_for('index'))

    activation = get_activation(mac)
    if not activation:
        # create new with 7-day trial
        create_activation(mac, device_key)
        activation = get_activation(mac)

    # activation columns: id, mac, device_key, playlist, trial_start, paid_until, paid_type
    _, mac_db, dev_db, playlist, trial_start, paid_until, paid_type = activation

    # basic device_key check (if different, update it)
    if dev_db != device_key:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("UPDATE activations SET device_key = ? WHERE mac = ?", (device_key, mac))
        conn.commit()
        conn.close()

    # check paid_until
    now = datetime.utcnow()
    paid_until_dt = datetime.fromisoformat(paid_until) if paid_until else None
    active_until_text = paid_until_dt.isoformat() if paid_until_dt else "1970-01-01T00:00:00"

    is_active = False
    if paid_until_dt and paid_until_dt > now:
        is_active = True
    # trial also handled because paid_until for trial was set to trial end

    if not is_active:
        # not active, show dashboard but mark as expired so user is prompted to pay
        flash("Vaš MAC nije aktivan. Istekla trial/podrška — potrebno platiti ili aktivirati.", "danger")

    return redirect(url_for('dashboard', mac=mac))

@app.route('/dashboard')
def dashboard():
    mac = request.args.get('mac')
    if not mac:
        flash("Nema MAC-a. Prijavite se.", "warning")
        return redirect(url_for('index'))

    activation = get_activation(mac)
    if not activation:
        flash("MAC nije pronađen. Registrirajte se ponovo.", "danger")
        return redirect(url_for('index'))

    _, mac_db, dev_db, playlist, trial_start, paid_until, paid_type = activation
    now = datetime.utcnow()
    paid_until_dt = datetime.fromisoformat(paid_until) if paid_until else None
    active = paid_until_dt and paid_until_dt > now

    return render_template("dashboard.html",
                           mac=mac_db,
                           device_key=dev_db,
                           playlist=playlist or "",
                           active=active,
                           paid_until=paid_until_dt,
                           stripe_public_key=STRIPE_PUBLIC_KEY)

@app.route('/create-checkout', methods=['POST'])
def create_checkout():
    mac = request.form.get('mac')
    device_key = request.form.get('device_key')
    product = request.form.get('product')  # 'lifetime' or 'yearly'

    if product == 'lifetime':
        amount = PRICE_LIFETIME_CENTS
        paid_type = 'lifetime'
    else:
        amount = PRICE_YEARLY_CENTS
        paid_type = 'yearly'

    try:
        # create checkout session, pass metadata to identify MAC
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            mode='payment',
            line_items=[{
                'price_data': {
                    'currency': CURRENCY,
                    'product_data': {
                        'name': f'BetTVPlus {paid_type.capitalize()} ({mac})',
                    },
                    'unit_amount': amount,
                },
                'quantity': 1,
            }],
            metadata={'mac': mac, 'device_key': device_key, 'paid_type': paid_type},
            success_url=url_for('success', _external=True) + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=url_for('dashboard', mac=mac, _external=True)
        )
        return redirect(session.url, code=303)
    except Exception as e:
        flash("Greška pri stvaranju checkout sesije: " + str(e), "danger")
        return redirect(url_for('dashboard', mac=mac))

@app.route('/success')
def success():
    session_id = request.args.get('session_id')
    if not session_id:
        flash("Nema session_id.", "danger")
        return redirect(url_for('index'))

    try:
        checkout_session = stripe.checkout.Session.retrieve(session_id)
        metadata = checkout_session.metadata or {}
        mac = metadata.get('mac')
        paid_type = metadata.get('paid_type', 'unknown')

        # set paid_until depending on paid_type
        now = datetime.utcnow()
        if paid_type == 'lifetime':
            paid_until = now + timedelta(days=36500)  # effectively lifetime
        elif paid_type == 'yearly':
            paid_until = now + timedelta(days=365)
        else:
            paid_until = now + timedelta(days=30)

        if mac:
            update_activation_payment(mac, paid_until, paid_type)
            flash("Uspješno plaćeno. Aktivacija je ažurirana.", "success")
            return render_template("success.html", mac=mac, paid_until=paid_until)
        else:
            flash("Ne mogu pronaći MAC u sesiji.", "warning")
            return redirect(url_for('index'))
    except Exception as e:
        flash("Greška u success handleru: " + str(e), "danger")
        return redirect(url_for('index'))

if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
